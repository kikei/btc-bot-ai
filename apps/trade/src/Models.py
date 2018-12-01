from classes import OnePosition, Confidence, Trade

class Models(object):
    def __init__(self, dbs):
      btctai_db = dbs.btctai_db
      self.Values = Values(btctai_db)
      self.Confidences = Confidences(btctai_db)
      self.Trades = Trades(btctai_db)
      self.Positions = Position(btctai_db)

    def Values(self):
      return self.Values

    def Confidences(self):
      return self.Confidences

    def Trades(self):
      return self.Trades

    def Positions(self):
      return self.Positions


class Values(object):
  Enabled = 'monitor.enabled'
  AdjusterStep = 'adjuster.step'
  AdjusterStop = 'adjuster.stop'
  AdjusterSpeed = 'adjuster.speed'
  AdjusterLastDirection = 'adjuster.direction'
  AdjusterThresConf = 'adjuster.confidence.thres'
  AllKeys = [
    Enabled,
    AdjusterStep,
    AdjusterStop,
    AdjusterSpeed,
    AdjusterLastDirection,
    AdjusterThresConf
  ]
  AllTypes = {
    Enabled: 'boolean',
    AdjusterStep: 'float',
    AdjusterStop: 'float',
    AdjusterSpeed: 'float',
    AdjusterLastDirection: 'int',
    AdjusterThresConf: 'float'
  }
  
  def __init__(self, db):
    self.collection = db.values
    self.setup()
  
  def setup(self):
    self.collection.create_index('k')
  
  def all(self):
    """
    (self: Values) -> {str: any}
    """
    kvs = {k: None for k in Values.AllKeys}
    objs = self.collection.find()
    for kv in objs:
      kvs[kv['k']] = kv['v']
    return kvs

  def all2(self):
    """
    (self: Values) -> {str: (value: any, type: str)}
    """
    kvs = {k: (None, Values.AllTypes[k]) for k in Values.AllKeys}
    objs = self.collection.find()
    for kv in objs:
      kvs[kv['k']] = (kv['v'], Values.AllTypes[kv['k']])
    return kvs

  def get(self, key):
    """
    (self: Values, key: str) -> any
    """
    if key not in Values.AllKeys:
      raise KeyError(key)
    kv = self.collection.find_one({'k': key})
    if kv is None:
      return None
    else:
      return kv['v']
  
  def set(self, key, value):
    """
    (self: Values, key: str, value: any) -> any
    """
    if key not in Values.AllKeys:
      raise KeyError(key)
    kv = {'k': key, 'v': value}
    condition = {'k': key}
    result = self.collection.replace_one(condition, kv, upsert=True)
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
    self.collection.create_index('timestamp')

  def oneNew(self):
    """
    (self: Confidences) -> Confidence
    """
    condition = {'status': Confidence.StatusNew}
    cur = self.collection.find(condition).sort('timestamp', -1).limit(1)
    confidence = next(cur, None)
    if confidence is not None:
      confidence = Confidence.fromDict(confidence)
    return confidence

  def all(self, status=None):
    """
    (self: Confidences) -> (Confidences)
    """
    if status is not None:
      condition = {'status': status}
      cur = self.collection.find(condition)
    else:
      cur = self.collection.find()
    cur = cur.sort('timestamp', -1)
    return (Confidence.fromDict(i) for i in cur)
  
  def save(self, confidence):
    """
    (self: Confidences, confidence: Confidence) -> Confidence
    """
    obj = confidence.toDict()
    condition = {'timestamp': obj['timestamp']}
    result = self.collection.replace_one(condition, obj, upsert=True)
    if result.upserted_id is None:
      return None
    else:
      return confidence
  
  def delete(self, confidence):
    """
    (self: Confidences, confidence: Confidence) -> Confidence
    """
    obj = confidence.toDict()
    result = self.collection.delete_one({'timestamp': obj['timestamp']})
    if result.deleted_count == 0:
      return None
    else:
      return confidence

class Trades(object):
  def __init__(self, db):
    self.collection = db.conditions
    self.setup()
  
  def setup(self):
    self.collection.create_index('timestamp')
  
  def all(self):
    """
    (self: Trades) -> [Trade]
    """
    cur = self.collection.find().sort('timestamp', -1)
    trades = [Trade.fromDict(c) for c in cur]
    return trades

  def save(self, trade):
    """
    (self: Trades, trade: Trade) -> Trade
    """
    obj = trade.toDict()
    condition = {'timestamp': obj['timestamp']}
    result = self.collection.replace_one(condition, obj, upsert=True)
    if result.upserted_id is None:
      return None
    else:
      return trade

class Positions(object):
  def __init__(self, db):
    self.collection = self.db.positions
    self.setup()
  
  def setup(self):
    self.collection.create_index('timestamp')
  
  def all(self):
    """
    (self: Positions) -> [Position]
    """
    positions = self.collection.find().sort('timestamp', -1)
    positions = [Position.fromDict(p) for p in positions]
    return positions
  
  def save(self, position):
    """
    (self: Positions, position: Position) -> Position
    """
    obj = position.toDict()
    condition = {'timestamp': obj['timestamp']}
    result = self.collection.replace_one(condition, obj, upsert=True)
    if result.upserted_id is None:
      return None
    else:
      return position
  
  def delete(self, position):
    """
    (self: Positions, position: Position) -> Position
    """
    obj = position.toDict()
    result = self.collection.delete_one({'timestamp': obj['timestamp']})
    if result.deleted_count == 0:
        return None
    else:
        return position
