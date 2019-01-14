from pymongo.operations import ReplaceOne
from classes import OneTick, Summary

class Ticks(object):
  """
  Ticks local version.
  """
  def __init__(self, db):
    self.collections = {
      'bitflyer': db.tick_bitflyer,
      'quoine': db.tick_quoine
    }
    for e in self.collections:
      self.collections[e].create_index('datetime')
  
  def getCollection(self, exchanger):
    return self.collections[exchanger]
  
  def one(self, exchanger, order=-1):
    collection = self.collections[exchanger]
    items = collection.find().sort('datetime', order).limit(1)
    item = next(items, None)
    if item is not None:
      item = OneTick.fromDict(item)
    print(item)
    return item
  
  def all(self, exchanger, dateStart=None, dateEnd=None, order=1):
    collection = self.collections[exchanger]
    conditions = []
    if dateStart is not None:
      conditions.append({'datetime': {'$gte': dateStart.timestamp()}})
    if dateEnd is not None:
      conditions.append({'datetime': {'$lte': dateEnd.timestamp()}})
    if len(conditions) > 0:
      items = collection.find({'$and': conditions})
    else:
      items = collection.find({})
    items = items.sort('datetime', order)
    return (OneTick.fromDict(t) for t in items)
  
  def save(self, exchanger, tick):
    collection = self.collections[exchanger]
    item = t.toDict()
    collection.replace_one({'datetime': item['datetime']}, item, upsert=True)
  
  def saveAll(self, exchanger, ticks):
    batch_size = 2048
    collection = self.collections[exchanger]
    reqs = []
    for t in ticks:
      item = t.toDict()
      condition = {'datetime': item['datetime']}
      reqs.append(ReplaceOne(condition, item, upsert=True))
      if len(reqs) >= batch_size:
        collection.bulk_write(reqs)
        reqs = []
    if len(reqs) > 0:
      collection.bulk_write(reqs, ordered=False)


class Summaries(object):
  def __init__(self, db):
    self.collections = {
      'bitflyer': {
        'minutely': db.tick_bitflyer_minutely,
        'hourly': db.tick_bitflyer_hourly,
        'daily': db.tick_bitflyer_daily,
        'weekly': db.tick_bitflyer_weekly,
      },
      'quoine': {
        'minutely': db.tick_quoine_minutely,
        'hourly': db.tick_quoine_hourly,
        'daily': db.tick_quoine_daily,
        'weekly': db.tick_quoine_weekly,
      }
    }
    for e in self.collections:
      for un in self.collections[e]:
        self.collections[e][un].create_index('datetime')
  
  def getCollection(self, exchanger, unit):
    return self.collections[exchanger][unit]
  
  def one(self, exchanger, unit, order=-1):
    collection = self.getCollection(exchanger, unit)
    items = collection.find().sort('datetime', order).limit(1)
    item = next(items, None)
    if item is not None:
      item = Summary.fromDict(item)
    return item
  
  def all(self, exchanger, unit, order=1):
    collection = self.getCollection(exchanger, unit)
    items = collection.find().sort('datetime', order)
    return (Summary.fromDict(t) for t in items)
  
  def saveAll(self, exchanger, unit, sums):
    reqs = []
    for s in sums:
      item = s.toDict()
      condition = {'datetime': item['datetime']}
      reqs.append(ReplaceOne(condition, item, upsert=True))
    if len(reqs) > 0:
      self.getCollection(exchanger, unit).bulk_write(reqs)
  
  def clear(self, exchanger, unit):
    collection = self.getCollection(exchanger, unit)
    collection.remove({})

