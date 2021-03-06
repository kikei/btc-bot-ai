import itertools
import datetime
import pymongo

from classes import Tick, OneTick, OnePosition, Confidence, TrendStrength, Trade, Position, datetimeToStr

class Models(object):
    def __init__(self, dbs, saveTickDateInString=False):
      btctai_db = dbs.btctai_db
      tick_db = dbs.tick_db
      self.Values = Values(btctai_db)
      self.Confidences = Confidences(btctai_db)
      self.TrendStrengths = TrendStrengths(btctai_db)
      self.Ticks = Ticks(tick_db, saveDateInString=saveTickDateInString)
      self.Trades = Trades(btctai_db)
      self.Positions = Positions(btctai_db)

    def Values(self):
      return self.Values

    def Confidences(self):
      return self.Confidences

    def TrendStrengths(self):
      return self.TrendStrengths

    def Ticks(self):
      return self.Ticks

    def Trades(self):
      return self.Trades

    def Positions(self):
      return self.Positions


class Ticks(object):
  def __init__(self, db, saveDateInString=False):
    self.db = db
    self.collections = {
      Tick.BitFlyer: self.db.tick_bitflyer,
      Tick.BitFlyerETHBTC: self.db.tick_bitflyer_ethbtc,
      Tick.Quoine: self.db.tick_quoine,
      Tick.BinanceETHBTC: self.db.tick_binance_ethbtc,
      Tick.BinanceXRPBTC: self.db.tick_binance_xrpbtc
    }
    self.saveDateInString = saveDateInString

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
        result[e] = OneTick.fromDict(t)
    return Tick(result)

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
      if self.saveDateInString:
        dateStart = datetime.datetime.fromtimestamp(start)
        dateStart = datetimeToStr(dateStart)
        conditions.append({'datetime': {'$gt': dateStart}})
      else:
        conditions.append({'datetime': {'$gt': start}})
    if end is not None:
      if self.saveDateInString:
        dateEnd = datetime.datetime.fromtimestamp(end)
        dateEnd = datetimeToStr(dateEnd)
        conditions.append({'datetime': {'$lt': dateEnd}})
      else:
        conditions.append({'datetime': {'$lt': end}})
    if len(conditions) > 0:
      curs = [c.find({'$and': conditions}) for c in collections]
    else:
      curs = [c.find() for c in collections]
    curs = [c.sort('datetime', order).limit(limit) for c in curs]
    result = {}
    for e, cur in zip(exchangers, curs):
      result[e] = [OneTick.fromDict(t) for t in cur]
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
        obj = t.toDict(dateInString=self.saveDateInString)
        result = self.collections[e].replace_one({'datetime': obj['datetime']},
                                                 obj, upsert=True)
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
  PositionThresProfit = 'position.profit.thres'
  PositionThresLossCut = 'position.losscut.thres'
  OperatorLastFired = 'operator.fired.last'
  OperatorSleepDuration = 'operator.fired.sleep'
  OperatorTrendStrengthLoad = 'operator.trendstrength.load'
  OperatorTrendWidth = 'operator.trend.width'
  OperatorTrendGradient = 'operator.trend.gradient'
  OperatorTrendSize = 'operator.trend.size'
  OperatorPositionsMax = 'operator.positions.max'
  OperatorLotInit = 'operator.lot.init'
  AllKeys = [
    Enabled,
    AdjusterStep,
    AdjusterStop,
    AdjusterSpeed,
    AdjusterLastDirection,
    AdjusterThresConf,
    AdjusterLotMin,
    AdjusterLotInit,
    AdjusterLotDecay,
    OperatorLastFired,
    OperatorSleepDuration,
    OperatorTrendStrengthLoad,
    OperatorTrendWidth,
    OperatorTrendGradient,
    OperatorTrendSize,
    OperatorPositionsMax,
    OperatorLotInit,
    PositionThresProfit,
    PositionThresLossCut
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
    AdjusterLotDecay: 'float',
    OperatorLastFired: 'float',
    OperatorSleepDuration: 'float',
    OperatorTrendStrengthLoad: 'int',
    OperatorTrendWidth: 'int',
    OperatorTrendGradient: 'float',
    OperatorTrendSize: 'int',
    OperatorPositionsMax: 'float',
    OperatorLotInit: 'float',
    PositionThresProfit: 'float',
    PositionThresLossCut: 'float'
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

class TrendStrengths(object):
  def __init__(self, db):
    self.collection = db.trendstrength
    self.setup()

  def setup(self):
    self.collection.create_index([('account_id', pymongo.TEXT),
                                  ('timestamp', pymongo.DESCENDING)])

  def oneNew(self, accountId):
    """
    (self: TrendStrengths, accountId: str) -> TrendStrengths
    """
    conditions = {'account_id': accountId}
    cur = self.collection.find(conditions).sort('timestamp', -1).limit(1)
    value = next(cur, None)
    if value is not None:
      value = TrendStrength.fromDict(value)
    return value

  def all(self, accountId, before=None, after=None, count=None):
    """
    (self: TrendStrengths, accountId: str) -> (TrendStrengths)
    """
    conditions = [{'account_id': accountId}]
    if before is not None:
      conditions.append({'timestamp': {'$lt': before}})
    if after is not None:
      conditions.append({'timestamp': {'$gt': after}})
    conditions = {'$and': conditions}
    cur = self.collection.find(conditions).sort('timestamp', -1)
    if count is not None:
      cur = cur.limit(count)
    return [TrendStrength.fromDict(i) for i in cur]
  
  def save(self, trendStrength, accountId):
    """
    (self: TrendStrength, trendStrength: TrendStrength, accountId: str)
    -> TrendStrength
    """
    obj = trendStrength.toDict()
    obj['account_id'] = accountId
    conditions = {'$and': [
      {'account_id': accountId}, {'timestamp': obj['timestamp']}
    ]}
    result = self.collection.replace_one(conditions, obj, upsert=True)
    if result.upserted_id is None:
      return None
    else:
      return trendStrength
  
  def delete(self, trendStrength, accountId):
    """
    (self: TrendStrength, trendStrength: TrendStrength, accountId: str)
    -> TrendStrength
    """
    obj = trendStrength.toDict()
    conditions = {'$and': [
      {'account_id': accountId}, {'timestamp': obj['timestamp']}
    ]}
    result = self.collection.delete_one(conditions)
    if result.deleted_count == 0:
      return None
    else:
      return trendStrength

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
    if result.upserted_id is None and result.matched_count == 0:
      return None
    else:
      return trade

class Positions(object):
  def __init__(self, db):
    self.collection = db.positions
    self.setup()
  
  def setup(self):
    self.collection.create_index([('account_id', pymongo.TEXT),
                                  ('timestamp', pymongo.DESCENDING)])
    self.collection.create_index([('account_id', pymongo.DESCENDING),
                                  ('status', pymongo.DESCENDING)])
  
  def one(self, accountId, timestamp=None):
    """
    (self: Positions, accountId: float?) -> Position
    """
    conditions = [{'account_id': accountId}]
    if timestamp is not None:
      conditions.append({'timestamp': timestamp})
    conditions = {'$and': conditions}
    position = self.collection.find_one(conditions)
    if position is not None:
      position = Position.fromDict(position)
    return position
  
  def all(self, accountId, before=None, count=None):
    """
    (self: Positions, accountId: str, before: float?, count: int?) -> [Position]
    """
    conditions = [{'account_id': accountId}]
    if before is not None:
      conditions.append({'timestamp': {'$lt': before}})
    conditions = {'$and': conditions}
    positions = self.collection.find(conditions).sort('timestamp', -1)
    if count is not None:
      positions = positions.limit(count)
    positions = [Position.fromDict(p) for p in positions]
    return positions

  @staticmethod
  def filterOpen(positions):
    """
    [Positions] -> [Position]
    """
    positions = itertools.takewhile(lambda p:p.isNotClosed(), positions)
    positions = filter(lambda p:p.isOpen(), positions)
    return list(positions)

  def currentOpen(self, accountId):
    """
    (self: Positions) -> [Position]
    """
    condition = {'$and': [{'account_id': accountId},
                          {'status': 'open'}]}
    positions = self.collection.find(condition).sort('timestamp', -1)
    positions = [Position.fromDict(p) for p in positions]
    #return Positions.filterOpen(positions)
    return positions
  
  def save(self, position, accountId):
    """
    (self: Positions, position: Position) -> Position
    """
    obj = position.toDict()
    obj['account_id'] = accountId
    condition = {'$and': [
      {'account_id': accountId},
      {'timestamp': obj['timestamp']}
    ]}
    result = self.collection.replace_one(condition, obj, upsert=True)
    if result.upserted_id is None and result.matched_count == 0:
      return None
    else:
      return position
  
  def delete(self, position, accountId):
    """
    (self: Positions, position: Position) -> Position
    """
    obj = position.toDict()
    condition = {'$and': [
      {'account_id': accountId},
      {'timestamp': obj['timestamp']}
    ]}
    result = self.collection.delete_one(condition)
    if result.deleted_count == 0:
        return None
    else:
        return position
