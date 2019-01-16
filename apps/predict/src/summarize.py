import datetime
import numpy as np
from classes import Summary
from models import Ticks, Summaries
from utils import readConfig, getDBInstance, getLogger, group

logger = getLogger()
config = readConfig('predict.ini')

EXCHANGERS = config['summarize'].getlist('exchangers')
UNITS = ['minutely', 'hourly', 'daily', 'weekly']

def summarizeTicks(allTicks, extractKey, itemsEnd, maxCount):
  asks = np.zeros(maxCount)
  for key, g in group(extractKey, allTicks):
    logger.debug('New group, size={size}, key={key}, start={start}'
                 .format(size=len(g), key=key, start=g[0].date))
    n = len(g)
    for i in range(0, n):
      asks[i] = g[i].ask
    date = datetime.datetime(*key)
    itemsEnd = min(n, itemsEnd)
    yield Summary(date=date,
                  askMax=np.max(asks[:n]),
                  askMin=np.min(asks[:n]),
                  askAverage=np.average(asks[:n]),
                  askOpen=np.mean(asks[0:itemsEnd]),
                  askClose=np.mean(asks[n-itemsEnd:n]))

def keyMinute(d):
  return (d.date.year, d.date.month, d.date.day, d.date.hour, d.date.minute)

def keyHour(d):
  return (d.date.year, d.date.month, d.date.day, d.date.hour)

def keyDate(d):
  return (d.date.year, d.date.month, d.date.day)

def keyWeek(d):
  weekDelta = datetime.timedelta(days=d.date.weekday() % 7)
  d = d.date - weekDelta
  return (d.year, d.month, d.day)

def ticksBy(ticks, exchanger, unit, dateStart=None):
  allTicks = ticks.all(exchanger, dateStart=dateStart)
  if unit == 'minutely':
    extractKey = keyMinute
    itemsEnd = 8
    maxCount = int(60)
  elif unit == 'hourly':
    extractKey = keyHour
    itemsEnd = 16
    maxCount = int(60 * 60)
  elif unit == 'daily':
    extractKey = keyDate
    itemsEnd = 16 * 60
    maxCount = int(24 * 60 * 60)
  elif unit == 'weekly':
    extractKey = keyWeek
    itemsEnd = 16 * 60 * 60
    maxCount = int(7 * 24 * 60 * 60)
  else:
    raise Exception('unknown unit, {unit}'.format(unit=unit))
  return summarizeTicks(allTicks, extractKey, itemsEnd, maxCount)


def main():
  db = getDBInstance(config)
  ticks = Ticks(db.tick_db)
  summaries = Summaries(db.tick_summary_db)
  for exchanger in EXCHANGERS:
    for unit in UNITS:
      logger.debug('Summarizing, exchanger={exchanger}, unit={unit}.'
                   .format(exchanger=exchanger, unit=unit))
      latest = summaries.one(exchanger, unit)
      if latest is not None:
        start = latest.date
      else:
        start = None
      sums = ticksBy(ticks, exchanger, unit, dateStart=start)
      logger.info('Saving summary...')
      summaries.saveAll(exchanger, unit, sums)

if __name__ == '__main__':
  main()
