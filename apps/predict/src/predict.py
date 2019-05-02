import datetime

# Numpy
import numpy as np

# Matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from Plotter import Plotter
from dsp import crosszero
from learningUtils import validated, to2d, zscore, loadModel
from utils import readConfig, getLogger, reportTrend, loadnpy

logger = getLogger()
logger.debug('Start prediction.')

config = readConfig('predict.ini')

INPUT_SIZE = config['predict'].getint('fitting.inputsize')

def load(exchanger, unit, ty):
  return loadnpy(config, exchanger, unit, ty, nan=0.)

Xbh1 = load('bitflyer', 'hourly', 'askAverage')
Xbh2 = load('bitflyer', 'hourly', 'askMax')
Xbh3 = load('bitflyer', 'hourly', 'askMin')
Xbhb1 = load('bitflyer', 'hourly', 'askAverageBB+2')
Xbhb2 = load('bitflyer', 'hourly', 'askAverageBB-2')
Xbhi1 = load('bitflyer', 'hourly', 'askAverageConv')
Xbhi2 = load('bitflyer', 'hourly', 'askAverageBase')
Xbhi3 = load('bitflyer', 'hourly', 'askAveragePrc1')
Xbhi4 = load('bitflyer', 'hourly', 'askAveragePrc2')
Xbm1 = loadnpy(config, 'bitflyer', 'minutely', 'askAverage')
Xqm1 = loadnpy(config, 'quoine', 'minutely', 'askAverage')
ybh1 = load('bitflyer', 'hourly', 'askCloseTrend')

ybh1 = validated(ybh1)

sampleSize = INPUT_SIZE
featureCount = 11

availableSize = len(Xbhi4)
dataSize = availableSize - sampleSize + 1
Xbh0 = np.zeros((dataSize, sampleSize, featureCount))
Xbh0[:,:,0] = to2d(Xbh1, sampleSize, available=availableSize)
Xbh0[:,:,1] = to2d(Xbh2, sampleSize, available=availableSize)
Xbh0[:,:,2] = to2d(Xbh3, sampleSize, available=availableSize)
Xbh0[:,:,3] = to2d(Xbhb1, sampleSize, available=availableSize)
Xbh0[:,:,4] = to2d(Xbhb2, sampleSize, available=availableSize)
Xbh0[:,:,5] = to2d(Xbhi1, sampleSize, available=availableSize)
Xbh0[:,:,6] = to2d(Xbhi2, sampleSize, available=availableSize)
Xbh0[:,:,7] = to2d(Xbhi3, sampleSize, available=availableSize)
Xbh0[:,:,8] = to2d(Xbhi4, sampleSize, available=availableSize)
# setup minutely
availableSizeM = (dataSize - 1) * 60 + sampleSize
d = datetime.datetime.now()
minutesToday = d.hour * 60 + d.minute
Xbh0[-1:,:,9] = Xbm1[-sampleSize:]
Xbh0[:-1,:,9] = to2d(Xbm1[:-minutesToday], sampleSize,
                     available=availableSizeM, stride=60)
Xbh0[-1:,:,10] = Xqm1[-sampleSize:]
Xbh0[:-1,:,10] = to2d(Xqm1[:-minutesToday], sampleSize,
                      available=availableSizeM, stride=60)

dataSize = Xbh0.shape[0]
Xbh = np.zeros((dataSize, Xbh0.shape[1] * Xbh0.shape[2]))
for i in range(0, dataSize):
  for j in range(0, featureCount):
    Xbh[i,j*sampleSize:(j+1)*sampleSize] = Xbh0[i,:,j]

ybh0 = ybh1[len(ybh1)-availableSize+sampleSize-1:]

# Restore models.
yModel = loadModel(config, 'trend')

# Prediction
logger.debug('Predicting current trend, Xbh.shape={x}...'.format(x=Xbh.shape))

ybhPred = yModel.predict(zscore(Xbh))[:,0]

def smoothPredicted(y, n, z=None):
  if z is None:
    z = lambda i:i/n
  f = np.zeros(n * 2)
  for i in range(0, n):
    f[n+i] = z(i)
  f = f / np.sum(f)
  y = np.convolve(y, f, mode='same')
  return y

p = Plotter(plt, subplots=(3, 1), linewidth=0.4)
Xbh1_ = Xbh1[len(Xbh1)-availableSize+sampleSize-1:]
ybhAvr = smoothPredicted(ybhPred, 11)
ybhZero = crosszero(ybhAvr - 0.5, thres=5e-3)

xlim = (Xbh1_.shape[0] - 8000, Xbh1_.shape[0] - 0)
xlim = (16000, 16500)

xPlot = np.arange(0, len(Xbh1_), 1)
p.plot(xPlot, Xbh1_, n=0, label='ask avr.')
for k, label in [(np.argwhere(ybhZero == -1.), 'short'),
                 (np.argwhere(ybhZero == +1.), 'long')]:
  p.scatter(k, Xbh1_[k], n=0, marker='x', linewidth=0.4, label=label)
p.limit(Xbh1_, xlim, n=0)
p.plot(xPlot, ybh0, n=1, label='exp.')
p.plot(xPlot, ybhPred, n=1, label='pred.')
p.plot(xPlot, ybhAvr, n=1, label='avr.')
p.hlines(0.5, 0, len(Xbh1_), n=1, linewidth=0.4)
p.limit(ybh0, xlim, n=1)
p.plot(xPlot, np.abs(ybh0 - ybhPred), n=2, label='delta')
p.savefig('../figures/predicted.svg')

# Plot predicted
# Xbh1_ = Xbh1[len(Xbh1)-availableSize+sampleSize-1:]
# thresExp = 0.9
# thresPred = 0.8
# ys = [(lbh0, lbhPred, 'long'), (sbh0, sbhPred, 'short')]
# plotPredicted(Xbh1_, ys, thresPredict=thresPred, thresExpect=thresExp,
#               xlim=(Xbh1_.shape[0] - 1000, Xbh1_.shape[0]))

# Plot diff
# plotDiff(Xbh1_, ys)

# xlbhPred = np.where(lbhPred > thresPred)[0]
# xsbhPred = np.where(sbhPred > thresPred)[0]
#
# logger.info('#lExpect={lex}, #lPredict={lpr}, #sExpect={sex}, #sPredict={spr}'
#             .format(lex=np.where(lbh0 > thresExp)[0].shape[0],
#                     lpr=np.where(lbhPred > thresPred)[0].shape[0],
#                     sex=np.where(sbh0 > thresExp)[0].shape[0],
#                     spr=np.where(sbhPred > thresPred)[0].shape[0]))
#
SHOW_LAST_PREDICTS = 24 * 3

for i in range(SHOW_LAST_PREDICTS, 0, -1):
  if i == 1:
    logger.warn('Current predicts are trend={trend:0.2f}.'
                .format(trend=ybhPred[-i]))
  else:
    logger.info('Predicts[{i:2.0f}] are trend={trend:0.2f}.'
                .format(i=i, trend=ybhPred[-i]))

# if lbhPred[-1] > thresPred:
#   logger.warn('Predicted chance to get LONG!, conf={conf:2.0f}, ask={ask:.0f}.'
#               .format(conf=lbhPred[-1] * 100, ask=Xbh1[-1]))
#
# if sbhPred[-1] > thresPred:
#   logger.warn('Predicted chance to get SHORT!, conf={conf:2.0f}, ask={ask:.0f}.'
#               .format(conf=sbhPred[-1] * 100, ask=Xbh1[-1]))

logger.debug('End prediction.')

yTrend = ybhPred[-1].item()
# longConf = lbhPred[-1].item()
# shortConf = sbhPred[-1].item()

logger.debug('Registering confidences, trend={trend:.3f}.'.format(trend=yTrend))

#reportTrend(config, yTrend, logger)
#reportConfidence(config, longConf, shortConf, logger)

logger.debug('End registering.')
