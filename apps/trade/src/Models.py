import pymongo
from classes import OnePosition, Confidence, Trade

class Models(object):
    def __init__(self, dbs):
      btctai_db = dbs.btctai_db
      self.Values = Values(btctai_db)
      self.Confidences = Confidences(btctai_db)
      self.Trades = Trades(btctai_db)

    def Values(self):
      return self.Values

    def Confidences(self):
      return self.Confidences

    def Trades(self):
      return self.Trades


class Values(object):
  Enabled = 'monitor.enabled'
  AdjusterStep = 'adjuster.step'
  AdjusterStop = 'adjuster.stop'
  AdjusterSpeed = 'adjuster.speed'
  AdjusterLastDirection = 'adjuster.direction'
  AdjusterThresConf = 'adjuster.confidence.thres'
  AdjusterLotMin = 'adjuster.lot.min'
  AllKeys = [
    Enabled,
    AdjusterStep,
    AdjusterStop,
    AdjusterSpeed,
    AdjusterLastDirection,
    AdjusterThresConf,
    AdjusterLotMin
  ]
  AllTypes = {
    Enabled: 'boolean',
    AdjusterStep: 'float',
    AdjusterStop: 'float',
    AdjusterSpeed: 'float',
    AdjusterLastDirection: 'int',
    AdjusterThresConf: 'float',
    AdjusterLotMin: 'float'
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

