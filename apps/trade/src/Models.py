import datetime
import pymongo
from classes import Tick, OneTick, OnePosition, Confidence, Trade, datetimeToStr

class Models(object):
    def __init__(self, dbs):
      btctai_db = dbs.btctai_db
      tick_db = dbs.tick_db
      self.Values = Values(btctai_db)
      self.Confidences = Confidences(btctai_db)
      self.Trades = Trades(btctai_db)
      self.Ticks = Ticks(tick_db)

    def Ticks(self):
      return self.Ticks

    def Values(self):
      return self.Values

    def Confidences(self):
      return self.Confidences

    def Trades(self):
      return self.Trades


class Ticks(object):
  def __init__(self, db):
    self.db = db
    self.collections = {
      Tick.BitFlyer: self.db.tick_bitflyer,
      Tick.Quoine: self.db.tick_quoine
    }

  def setup(self):
    for k, collection in self.collections:
      collection.create_index([('datetime', pymongo.DESCENDING)])

  def one(self, exchangers=None):
    """
    (self: Ticks, exchangers: [str]?) -> Tick
    """
    if exchangers is None:
      exchangers = Tick.exchangers()
    collections = [self.collections[e] for e in exchangers]
    curs = [c.find().sort('datetime', -1).limit(1) for c in collections]
    result = {}
    for e, cur in zip(exchangers, curs):
      t = next(cur, None)
      if t is None:
        result[e] = None
      else:
        result[e] = OneTick.from_dict(t)
    return result

  def all(self, exchangers=None, start=None, end=None, limit=10, order=-1):
    """
    (self: Ticks, exchangers: [str]?, start: float?, end: float?, limit: int?)
    -> {(exchanger: str): [Tick]}
    """
    if exchangers is None:
      exchangers = Tick.exchangers()
    order = 1 if order > 0 else -1
    collections = [self.collections[e] for e in exchangers]
    conditions = []
    if start is not None:
      dateStart = datetime.datetime.fromtimestamp(start)
      dateStart = datetimeToStr(dateStart)
      conditions.append({'datetime': {'$gt': dateStart}})
    if end is not None:
      dateEnd = datetime.datetime.fromtimestamp(end)
      dateEnd = datetimeToStr(dateEnd)
      conditions.append({'datetime': {'$lt': dateEnd}})
    if len(conditions) > 0:
      curs = [c.find({'$and': conditions}) for c in collections]
    else:
      curs = [c.find() for c in collections]
    curs = [c.sort('datetime', order).limit(limit) for c in curs]
    result = {}
    for e, cur in zip(exchangers, curs):
      result[e] = [OneTick.from_dict(t) for t in cur]
    return result

  def save(self, tick, exchangers=None):
    """
    (self: Ticks, tick: Tick, exchangers: [str]?) -> Tick
    """
    if exchangers is None:
      exchangers = tick.exchangers()
    results = {k: None for k in exchangers}
    for e in exchangers:
      if tick.exchanger(e) is not None:
        t = tick.exchanger(e)
        result = self.collections[e].replace_one({'datetime': t.date},
                                                 t.to_dict(), upsert=True)
        if result.matched_count != 0:
          results[e] = t
    return results


class Values(object):
  Enabled = 'monitor.enabled'
  AdjusterStep = 'adjuster.step'
  AdjusterStop = 'adjuster.stop'
  AdjusterSpeed = 'adjuster.speed'
  AdjusterLastDirection = 'adjuster.direction'
  AdjusterThresConf = 'adjuster.confidence.thres'
  AdjusterLotMin = 'adjuster.lot.min'
  AdjusterLotInit = 'adjuster.lot.init'
  AdjusterLotDecay = 'adjuster.lot.decay'
  AllKeys = [
    Enabled,
    AdjusterStep,
    AdjusterStop,
    AdjusterSpeed,
    AdjusterLastDirection,
    AdjusterThresConf,
    AdjusterLotMin,
    AdjusterLotInit,
    AdjusterLotDecay
  ]
  AllTypes = {
    Enabled: 'boolean',
    AdjusterStep: 'float',
    AdjusterStop: 'float',
    AdjusterSpeed: 'float',
    AdjusterLastDirection: 'int',
    AdjusterThresConf: 'float',
    AdjusterLotMin: 'float',
    AdjusterLotInit: 'float',
    AdjusterLotDecay: 'float'
  }
  
  def __init__(self, db):
    self.collection = db.values
    self.setup()
  
  def setup(self):
    self.collection.create_index([('account_id', pymongo.TEXT),
                                  ('k', pymongo.TEXT)])
  
  def all(self, accountId):
    """
    (self: Values, accountId: str) -> {str: (value: any, type: str)}
    """
    kvs = {k: (None, Values.AllTypes[k]) for k in Values.AllKeys}
    conditions = {'account_id': accountId}
    objs = self.collection.find(conditions)
    for kv in objs:
      kvs[kv['k']] = (kv['v'], Values.AllTypes[kv['k']])
    return kvs

  def get(self, key, accountId):
    """
    (self: Values, key: str, accountId: str) -> any
    """
    if key not in Values.AllKeys:
      raise KeyError(key)
    conditions = {
      '$and': [{'account_id': accountId}, {'k': key}]
    }
    kv = self.collection.find_one(conditions)
    if kv is None:
      return None
    else:
      return kv['v']
  
  def set(self, key, value, accountId):
    """
    (self: Values, key: str, value: any, accountId: str) -> any
    """
    if key not in Values.AllKeys:
      raise KeyError(key)
    kv = {'account_id': accountId, 'k': key, 'v': value}
    conditions = {'$and': [{'account_id': accountId}, {'k': key}]}
    result = self.collection.replace_one(conditions, kv, upsert=True)
    if result.upserted_id is None and result.matched_count == 0:
      return None
    else:
      return value

  def getType(self, key):
    return Values.AllTypes[key]
  
  def checkType(self, key, value):
    ty = Values.AllTypes[key]
    if ty == 'boolean':
      types = [bool]
    if ty == 'int':
      types = [int]
    elif ty == 'float':
      types = [int, float]
    if ty == 'string':
      types = [str]
    return type(value) in types
    
    
class Confidences(object):
  def __init__(self, db):
    self.collection = db.confidences
    self.setup()

  def setup(self):
    self.collection.create_index([('account_id', pymongo.TEXT),
                                  ('timestamp', pymongo.DESCENDING)])

  def oneNew(self, accountId):
    """
    (self: Confidences, accountId: str) -> Confidence
    """
    conditions = {'$and': [
      {'account_id': accountId}, {'status': Confidence.StatusNew}
    ]}
    cur = self.collection.find(conditions).sort('timestamp', -1).limit(1)
    confidence = next(cur, None)
    if confidence is not None:
      confidence = Confidence.fromDict(confidence)
    return confidence

  def all(self, accountId, status=None, before=None, count=None):
    """
    (self: Confidences, accountId: str) -> (Confidences)
    """
    conditions = [{'account_id': accountId}]
    if status is not None:
      conditions.append({'status': status})
    if before is not None:
      conditions.append({'timestamp': {'$lt': before}})
    conditions = {'$and': conditions}
    cur = self.collection.find(conditions).sort('timestamp', -1)
    if count is not None:
      cur = cur.limit(count)
    return (Confidence.fromDict(i) for i in cur)
  
  def save(self, confidence, accountId):
    """
    (self: Confidences, confidence: Confidence, accountId: str) -> Confidence
    """
    obj = confidence.toDict()
    obj['account_id'] = accountId
    conditions = {'$and': [
      {'account_id': accountId}, {'timestamp': obj['timestamp']}
    ]}
    result = self.collection.replace_one(conditions, obj, upsert=True)
    if result.upserted_id is None:
      return None
    else:
      return confidence
  
  def delete(self, confidence, accountId):
    """
    (self: Confidences, confidence: Confidence, accountId: str) -> Confidence
    """
    obj = confidence.toDict()
    conditions = {'$and': [
      {'account_id': accountId}, {'timestamp': obj['timestamp']}
    ]}
    result = self.collection.delete_one(conditions)
    if result.deleted_count == 0:
      return None
    else:
      return confidence

class Trades(object):
  def __init__(self, db):
    self.collection = db.conditions
    self.setup()
  
  def setup(self):
    self.collection.create_index([('account_id', pymongo.TEXT),
                                  ('timestamp', pymongo.DESCENDING)])

  def all(self, accountId, before=None, count=None):
    """
    (self: Trades, accountId: str) -> [Trade]
    """
    conditions = [{'account_id': accountId}]
    if before is not None:
      conditions.append({'timestamp': {'$lt': before}})
    conditions = {'$and': conditions}
    cur = self.collection.find(conditions).sort('timestamp', -1)
    if count is not None:
      cur = cur.limit(count)
    trades = [Trade.fromDict(c) for c in cur]
    return trades

  def save(self, trade, accountId):
    """
    (self: Trades, trade: Trade, accountId: str) -> Trade
    """
    obj = trade.toDict()
    obj['account_id'] = accountId
    condition = {'$and': [
      {'account_id': accountId},
      {'timestamp': obj['timestamp']}
    ]}
    result = self.collection.replace_one(condition, obj, upsert=True)
    if result.upserted_id is None:
      return None
    else:
      return trade

