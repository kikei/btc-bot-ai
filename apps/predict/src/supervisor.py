# Numpy
import numpy as np

# Matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from charts import RSI, BollingerBand, Ichimoku
from dsp import lpfilter, crosszero
from learningUtils import sigmoid, differentiate
from utils import readConfig, getLogger, loadnpy, savenpy, nanIn, StopWatch

logger = getLogger()
config = readConfig('predict.ini')

DIR_DATA = config['supervisor'].get('data.dir')
EXCHANGERS = config['supervisor'].getlist('exchangers')
UNITS = config['supervisor'].getlist('units')

def load(exchanger, unit, ty):
  return loadnpy(config, exchanger, unit, ty)

def save(data, exchanger, unit, ty):
  savenpy(config, data, exchanger, unit, ty)

def ranges(lst, f=lambda x:x, indexEnd=-1):
  indexStart = 0
  lastKey = None
  for item in lst:
    index, key = f(item)
    if lastKey is not None and lastKey != key:
      yield {'start': indexStart, 'end': index, 'key': lastKey}
      indexStart = index + 1
    lastKey = key
  yield {'start': indexStart, 'end': indexEnd, 'key': lastKey}

def rectify(v1, v2):
  """
  Returns new vector where local maximum and mimimum alternate with even ones.
  v1: a base tick data.
  v2: peeks vector with +1(local maximum) and -1(local minimum).
  """
  k1 = [(k, +1) for k in np.where(v2 >= +1.)[0]]
  k2 = [(k, -1) for k in np.where(v2 <= -1.)[0]]
  ks = sorted(k1 + k2, key=lambda a:a[0])
  w = np.zeros(v1.shape)
  rs = list(ranges(ks, indexEnd=len(v1)))
  k = None
  for i in range(0, len(rs)):
    if k is None:
      start = rs[i]['start']
    else:
      start = k
    end = rs[i]['end']
    peek = rs[i]['key']
    if peek == +1:
      k = np.argmax(v1[start:end+1]) + start
    else:
      k = np.argmin(v1[start:end+1]) + start
    w[k] = peek
  return w

def easing(v, v2, minWidth):
  def easing_(ks, i, minWidth, fkey=lambda xy:xy[0]):
    while i + 1 < len(ks) and fkey(ks[i+1]) - fkey(ks[i]) < minWidth:
      ks.pop(i+1)
  ks = [(k, v2[k]) for k in np.where(np.abs(v2) >= 1.)[0]]
  i = 0
  while i < len(ks) - 1:
    easing_(ks, i, minWidth)
    i += 1
  w = np.zeros(v.shape)
  for k, v in ks:
    w[k] = v
  return w

def trend(peeks):
  t = np.zeros(peeks.shape)
  k = peeks[np.where(peeks != 0)[0][-1]]
  for i in range(0, peeks.shape[0]):
    j = peeks.shape[0] - i - 1
    if peeks[j] != 0:
      k = peeks[j]
    t[j] = k
  return t

def trendStrength(values, vt):
  ks = [(k, vt[k]) for k in np.where(np.abs(vt) >= 1.)[0]]
  w = np.array(values)
  for i in range(0, len(ks) - 1):
    k0, v0 = ks[i]
    k1, v1 = ks[i+1]
    if k0 + 1 == k1:
      continue
    v = values[k0+1:k1]
    vmax = np.max(v)
    vmin = np.min(v)
    if v0 <= -1. and vmin < 0: # incremental trend
      w[k0+1:k1] = (v - vmin) / (vmax - vmin) * vmax
    elif v0 >= +1. and vmax > 0: # decremental trend
      w[k0+1:k1] = (vmax - v) / (vmax - vmin) * vmin
  return w

def generateAnswer(v1, lpfs):
  """
  Generate supervisor data that should be expected by prediction.
  v1:   the raw ticks as 1d vector.
  lpfs: list of low pass filters.
  """
  lpf1 = lpfs[0]
  lpf2 = lpfs[1]
  # Log of original series
  v2 = np.log10(v1)
  # Smooth moving of log of original series
  v3 = np.convolve(v2, lpf1, mode='same')
  # Derivative of the moving average
  v4 = differentiate(v3, sameSize=True)
  # Smooth moving of derivative
  v5 = np.convolve(v4, lpf2, mode='same')
  # Find trend conversions
  v6 = crosszero(v5, thres=5e-4)
  # Find peeks; v2[p] is max, v2[q] is min | v7[p] = +1, v7[q] = -1
  v7 = rectify(v2, v6)
  # Remove peeks close to another
  v8 = easing(v2, v7, minWidth=11)
  v9 = rectify(v2, v8)
  #v10 = trend(v9)
  v11 = RSI(v2, 23, slide=11) - 0.5
  v12 = trendStrength(v11, v9)
  v13 = np.power(v12 * 2, 2) * np.sign(v12) * 0.5 + 0.5
  return {'Trend': v13}

def getLPFiltersSize(unit):
  if unit == 'daily':
    return 7, 5
  elif unit == 'hourly':
    return 24, 12

def runAnswer(values, exchanger, unit, ty):
  lpSize = getLPFiltersSize(unit)
  lpFilters = [lpfilter(size) for size in lpSize]
  # Period without data may be NaN
  errorIndex = np.argwhere(np.isnan(values))
  values[errorIndex] = 1.
  answers = generateAnswer(values, lpfs=lpFilters)
  for k in answers:
    answer = answers[k]
    answer[errorIndex] = 0.5
    save(answer, exchanger, unit, ty + k)

def runBollingerBand(values, exchanger, unit, ty):
  bb = BollingerBand(values, k=28)
  save(bb.sigmaLine(2), exchanger, unit, ty + 'BB+2')
  save(bb.sigmaLine(-2), exchanger, unit, ty + 'BB-2')

def runIchimoku(values, exchanger, unit, ty):
  if unit == 'daily':
    kConv = 13
    kBase = 36
    kPrec = 72
  else:
    kConv = 11
    kBase = 31
    kPrec = 62
  ichimoku = Ichimoku(values, kConv=kConv, kBase=kBase, kPrec=kPrec)
  save(ichimoku.convertionLine(), exchanger, unit, ty + 'Conv')
  save(ichimoku.baseLine(), exchanger, unit, ty + 'Base')
  save(ichimoku.precedingLine1(shift=kBase-1), exchanger, unit, ty + 'Prc1')
  save(ichimoku.precedingLine2(shift=kBase-1), exchanger, unit, ty + 'Prc2')
  save(ichimoku.laggingLine(), exchanger, unit, ty + 'Lag')

def run(exchanger, unit, ty):
  values = load(exchanger, unit, ty)
  runAnswer(values, exchanger, unit, ty)
  runBollingerBand(values, exchanger, unit, ty)
  runIchimoku(values, exchanger, unit, ty)

def runForAll(exchangers, units, types):
  for exchanger in exchangers:
    for unit in units:
      for ty in types:
        logger.info('Processing..., exchanger={e}, unit={u}, type={ty}'
                    .format(e=exchanger, u=unit, ty=ty))
        run(exchanger, unit, ty)

def main():
  # Measure run time
  timer = StopWatch()
  timer.start()
  # Execution
  types = ['askAverage', 'askOpen', 'askClose']
  runForAll(EXCHANGERS, UNITS, types)
  # Finished
  seconds = timer.stop()
  logger.debug('End supervising, elapsed={s:.2f}s'.format(s=seconds))

if __name__ == '__main__':
  main()
