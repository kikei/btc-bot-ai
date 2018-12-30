# Numpy
import numpy as np

# Matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from charts import BollingerBand, Ichimoku
from Plotter import Plotter
from learningUtils import sigmoid, differentiate
from utils import readConfig, getLogger, loadnpy, savenpy

logger = getLogger()
config = readConfig('predict.ini')

DIR_DATA = config['supervisor'].get('data.dir')
EXCHANGERS = config['supervisor'].getlist('exchangers')
UNITS = ['daily', 'hourly']

def load(exchanger, unit, ty):
  return loadnpy(config, exchanger, unit, ty)

def save(data, exchanger, unit, ty):
  savenpy(config, data, exchanger, unit, ty)

def lpfilter(size):
  return np.full(size, 1.0 / size)

def integral(v):
  w = np.zeros(v.shape)
  for i in range(0, len(v)):
    if i == 0:
      w[i] = v[i]
    else:
      w[i] = w[i-1] + v[i]
  return w

def pudding(z, a=0, b=0, k=1.):
  """
  Pudding function.
  a: center.
  b: size of ceil.
  k: scale of x.
  """
  v = 1 / (1 + np.exp(k * (-z + a - b))) - 1 / (1 + np.exp(k * (-z + a + b)))
  v = v / (np.max(v) - np.min(v)) # scale to 0 <= v <= 1
  return v

def crossZero(v, thres=0., ud=+1.0, du=-1.0):
  w = np.zeros(v.shape)
  udZero = None
  duZero = None
  for i in range(1, len(v)):
    if v[i-1] > 0. and v[i] < 0.:
      if thres != 0.:
        udZero = i
      else:
        w[i] = ud
    elif v[i-1] > -thres and v[i] < -thres and udZero is not None:
      w[udZero] = ud
      udZero = None
    elif v[i-1] < 0. and v[i] > 0.:
      if thres != 0.:
        duZero = i
      else:
        w[duZero] = du
    elif v[i-1] < thres and v[i] > thres and duZero is not None:
      w[duZero] = du
      duZero = None
  return w

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

def rectify(v, peeks):
  """
  Returns new vector where local maximum and mimimum alternate with even ones.
  v:     a base tick data.
  peeks: peeks vector with +1(local maximum) and -1(local minimum).
  """
  k1 = [(k, +1) for k in np.where(peeks >= +1.)[0]]
  k2 = [(k, -1) for k in np.where(peeks <= -1.)[0]]
  k = sorted(k1 + k2, key=lambda a:a[0])
  w = np.zeros(v.shape)
  for r in ranges(k, indexEnd=len(v)):
    start = r['start']
    end = r['end']
    peek = r['key']
    if peek == +1:
      k = np.argmax(v[start:end+1]) + start
    else:
      k = np.argmin(v[start:end+1]) + start
    w[k] = peek
  return w

def calcExpected(v, peeks,
                 medium=0.125, width=0.05, decay=0.025, sharpness=2**10):
  wInc = np.zeros(v.shape)
  wDec = np.zeros(v.shape)
  k = np.where(abs(peeks) >= +1.)[0]
  offset = int(v[k[0]] < v[k[1]])
  for w, offset in [(wDec, offset), (wInc, offset ^ 1)]:
    for i in range(offset, len(k), 2):
      if i >= len(k) - 1: break
      kStart = k[i]
      kEnd = k[i+1]
      vStart = v[kStart]
      vEnd = v[kEnd]
      vCenter = vStart * (1. - medium) + vEnd * medium
      vWidth = abs(vEnd - vStart) * width
      confidence = pudding(v[kStart:kEnd], vCenter, vWidth, k=sharpness)
      d = 1. - decay * integral(confidence)
      w[kStart:kEnd] = np.clip(confidence * d, 0., 1.)
  return wInc, wDec

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
  v6 = crossZero(v5, thres=5e-4)
  # Find peeks; v2[p] is max, v2[q] is min | v7[p] = +1, v7[q] = -1
  v7 = rectify(v2, v6)
  # Calculate continuouss expected value
  v8_1, v8_2 = calcExpected(v2, v7, medium=0.15, width=0.15,
                            decay=2e-3, sharpness=2**8)
  return v8_1, v8_2

def getLPFiltersSize(unit):
  if unit == 'daily':
    return 7, 5
  elif unit == 'hourly':
    return 24, 12
#   return 12, 7 # 0.5d, 0.5w
#   return 86, 120 # 0.5w, 1M

def runAnswer(values, exchanger, unit, ty):
  lpSize = getLPFiltersSize(unit)
  lpFilters = [lpfilter(size) for size in lpSize]
  longs, shorts = generateAnswer(values, lpfs=lpFilters)
  save(longs, exchanger, unit, ty + 'Long')
  save(shorts, exchanger, unit, ty + 'Short')

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
  types = ['askAverage', 'askOpen', 'askClose']
  runForAll(EXCHANGERS, UNITS, types)

if __name__ == '__main__':
  main()
