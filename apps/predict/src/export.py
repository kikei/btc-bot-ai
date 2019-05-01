import datetime
import numpy as np

from classes import Tick, Summary
from models import Summaries
from utils import readConfig, getDBInstance, getLogger, savenpy

logger = getLogger()
config = readConfig('predict.ini')

DIR_DATA = config['export'].get('data.dir')
FILE_DATA = config['export'].get('data.npy')
EXCHANGERS = config['export'].getlist('exchangers')
UNITS = ['minutely', 'hourly', 'daily', 'weekly']

def completion(f, sums, step):
  size = len(sums)
  if size == 0:
    return None
  v = np.zeros(size * 4)
  i = -1
  start = sums[0].date.timestamp()
  for s in sums:
    timestamp = s.date.timestamp()
    j = int((timestamp - start) / step)
    if j == i + 1:
      v[j] = f(s)
    else:
      # Linear completion
      v[i:j+1] = np.linspace(v[i], f(s), j - i + 1)
    i = j
  w = v[:i+1]
  return w

def removeNaN(w):
  for i in np.argwhere(np.isnan(w)):
    if i == 0:
      w[i] = w[0]
    else:
      w[i] = w[i-1]
  return w

def seriesDate(sums, step):
  if len(sums) == 0:
    return None
  start = sums[0].date.timestamp()
  end = sums[-1].date.timestamp()
  return np.arange(start, end + 1.0, step)

def main():
  db = getDBInstance(config)
  summaries = Summaries(db.tick_summary_db)
  stepSeconds = {
    'minutely': 60,
    'hourly': 60 * 60,
    'daily': 24 * 60 * 60,
    'weekly': 7 * 24 * 60 * 60
  }

  for exchanger in EXCHANGERS:
    for unit in UNITS:
      sums = list(summaries.all(exchanger, unit))
      logger.debug('Copying {e}\'s {u} ticks to np.array, #items={n}...'
                   .format(e=exchanger, u=unit, n=len(sums)))
      step = stepSeconds[unit]
      dates = seriesDate(sums, step)
      completes = {
        'askMax': completion(lambda s:s.askMax, sums, step),
        'askMin': completion(lambda s:s.askMin, sums, step),
        'askAverage': completion(lambda s:s.askAverage, sums, step),
        'askOpen': completion(lambda s:s.askOpen, sums, step),
        'askClose': completion(lambda s:s.askClose, sums, step)
      }
      for ty in completes:
        completes[ty] = removeNaN(completes[ty])
      for ty in completes:
        completed = completes[ty]
        if len(dates) != len(completed):
          raise Exception('Length unmatch, #date={date}, #completed={completed}.'
                          .format(date=len(dates), completed=len(completed)))
        savenpy(config, completed, exchanger, unit, ty)
      savenpy(config, dates, exchanger, unit, 'date')

if __name__ == '__main__':
  main()
