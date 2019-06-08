import datetime
import numpy as np

from classes import Tick, Summary
from models import Summaries
from utils import readConfig, getDBInstance, getLogger, savenpy, StopWatch

logger = getLogger()
logger.debug('Start export.')

config = readConfig('predict.ini')

DIR_DATA = config['export'].get('data.dir')
FILE_DATA = config['export'].get('data.npy')
EXCHANGERS = config['export'].getlist('exchangers')
UNITS = config['export'].getlist('units')
EXPORT_WITHIN_SECONDS = config['export'].getfloat('within.seconds')
MAX_COMPLETION_HOURLY = config['export'].getint('completion.maxHourly')
MAX_COMPLETION_DAILY = config['export'].getint('completion.maxDaily')
COMPLETION_NOISE_SCALE = config['export'].getfloat('completion.noise.scale')
COMPLETION_CYCLE_HOURLY = config['export'].getfloat('completion.cycleHourly')

def completion(f, sums, step, maxN=None, error=np.nan, noise=None):
  if maxN is None:
    maxN = np.inf
  size = len(sums)
  if size == 0:
    return None
  v = np.zeros(size * 4)
  i = -1
  start = sums[0].date.timestamp()
  for s in sums:
    timestamp = s.date.timestamp()
    j = int((timestamp - start) / step)
    d = j - i
    if d == 1:
      v[j] = f(s)
    elif d < maxN:
      # Linear completion
      v[i:j+1] = np.linspace(v[i], f(s), j - i + 1)
      if noise is not None:
        v[i:j+1] += noise(j - i + 1)
    else:
      v[i:j+1] = error
    i = j
  w = v[:i+1]
  return w

def seriesDate(sums, step):
  if len(sums) == 0:
    return None
  start = sums[0].date.timestamp()
  end = sums[-1].date.timestamp()
  return np.arange(start, end + 1.0, step)

def completionNoise(n, cycle, scale):
  base = scale * np.sin(np.array(range(0, n))/ cycle * np.pi)
  noise = np.random.normal(scale=scale * 0.5, size=n)
  return base + noise

def main():
  # Measure run time
  timer = StopWatch()
  timer.start()
  # Setup models
  db = getDBInstance(config)
  summaries = Summaries(db.tick_summary_db)
  stepSeconds = {
    'minutely': 60,
    'hourly': 60 * 60,
    'daily': 24 * 60 * 60,
    'weekly': 7 * 24 * 60 * 60
  }
  maxCompletions = {
    'minutely': None,
    'hourly': MAX_COMPLETION_HOURLY,
    'daily': MAX_COMPLETION_DAILY,
    'weekly': None
  }
  noiseCycles = {
    'minutely': None,
    'hourly': COMPLETION_CYCLE_HOURLY,
    'daily': None,
    'weekly': None
  }
  now = datetime.datetime.now().timestamp()
  after = now - EXPORT_WITHIN_SECONDS
  for exchanger in EXCHANGERS:
    for unit in UNITS:
      sums = list(summaries.all(exchanger, unit, after=after))
      logger.debug('Copying {e}\'s {u} ticks to np.array, #items={n}...'
                   .format(e=exchanger, u=unit, n=len(sums)))
      step = stepSeconds[unit]
      maxCompletion = maxCompletions[unit]
      dates = seriesDate(sums, step)
      logger.debug('Completing {e}\'s {u} ticks to np.array, maxN={maxN}...'
                   .format(e=exchanger, u=unit, maxN=maxCompletion))
      opts = {
        'maxN': maxCompletion
      }
      if noiseCycles[unit] is not None:
        opts['noise'] = lambda n:completionNoise(n, cycle=noiseCycles[unit],
                                                 scale=COMPLETION_NOISE_SCALE)
      completes = {
        'askMax': completion(lambda s:s.askMax, sums, step, **opts),
        'askMin': completion(lambda s:s.askMin, sums, step, **opts),
        'askAverage': completion(lambda s:s.askAverage, sums, step, **opts),
        'askOpen': completion(lambda s:s.askOpen, sums, step, **opts),
        'askClose': completion(lambda s:s.askClose, sums, step, **opts)
      }
      for ty in completes:
        completed = completes[ty]
        if len(dates) != len(completed):
          raise Exception('Length unmatch, #date={date}, #completed={completed}.'
                          .format(date=len(dates), completed=len(completed)))
        savenpy(config, completed, exchanger, unit, ty)
      savenpy(config, dates, exchanger, unit, 'date')
  # Finished
  seconds = timer.stop()
  logger.debug('End export, elapsed={s:.2f}s'.format(s=seconds))

if __name__ == '__main__':
  main()
