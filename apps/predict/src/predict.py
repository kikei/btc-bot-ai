import datetime

# Numpy
import numpy as np

# Matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from Plotter import Plotter
from learningUtils import validated, to2d, zscore, loadModel
from utils import readConfig, getLogger, reportConfidence, loadnpy

logger = getLogger()
logger.debug('Start prediction.')

config = readConfig('predict.ini')

INPUT_SIZE = config['predict'].getint('fitting.inputsize')

def load(exchanger, unit, ty):
  return loadnpy(config, exchanger, unit, ty)

def plotPredicted(X, ys, xlim=None, thresExpect=0.9, thresPredict=0.9, expected=True, predicted=True):
  p = Plotter(plt, subplots=(2, 1), linewidth=0.4)
  xPlot = np.arange(0, len(X), 1)
  p.plot(xPlot, X, n=0, label='ask avr.')
  for expect, predict, label in ys:
    expect = expect > thresExpect
    predict = predict > thresPredict
    expectPlot = np.where(expect)[0]
    predictPlot = np.where(predict)[0]
    p.scatter(expectPlot, (X * expect)[expectPlot], n=0,
              color=p.nextColor(), marker='x', label=label + ' exp.')
    p.scatter(predictPlot, (X * predict)[predictPlot], n=0,
              color=p.nextColor(), marker='+', label=label + ' pred.')
  p.limit(X, xlim, n=0)
  for expect, predict, label in ys:
    p.plot(xPlot, expect, n=1,
           color=p.nextColor(), label=label + ' exp.')
    p.plot(xPlot, predict, n=1,
           color=p.nextColor(), label=label + ' pred.')
  p.limit(expect, xlim, n=1)
  p.savefig('../figures/predicted.svg')


def plotDiff(X, ys, xlim=None, lpSize=168):
  p = Plotter(plt, linewidth=0.2)
  xPlot = np.arange(0, len(Xbh1_), 1)
  for expect, predict, label in ys:
    d = np.log2((expect - predict) ** 2 + 1) / 2.0
    p.plot(xPlot, d, color=p.nextColor(), label=label)
    if lpSize is not None:
      dm = np.convolve(d, np.full(lpSize, 1./lpSize), mode='same')
      p.plot(xPlot, dm, color=p.nextColor(), label=label + ' mean')
  if xlim is not None:
    p.limit(d, xlim=xlim)
  p.savefig('../figures/diff.svg')


X1 = load('bitflyer', 'daily', 'askAverage')
X2 = load('bitflyer', 'daily', 'askMax')
X3 = load('bitflyer', 'daily', 'askMin')
X4 = load('quoine', 'daily', 'askAverage')
X5 = load('quoine', 'daily', 'askMax')
X6 = load('quoine', 'daily', 'askMin')
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
#Xbhi5 = load('bitflyer', 'hourly', 'askOpenLag')
longs = load('bitflyer', 'daily', 'askAverageLong')
shorts = load('bitflyer', 'daily', 'askAverageShort')
lbh1 = load('bitflyer', 'hourly', 'askAverageLong')
sbh1 = load('bitflyer', 'hourly', 'askAverageShort')

longs = validated(longs)
shorts = validated(shorts)
lbh1 = validated(lbh1)
sbh1 = validated(sbh1)

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

lbh0 = lbh1[len(lbh1)-availableSize+sampleSize-1:]
sbh0 = sbh1[len(sbh1)-availableSize+sampleSize-1:]

# Restore models.
lmodel = loadModel(config, 'long')
smodel = loadModel(config, 'short')

# Prediction
logger.debug('Predicting if it\'s time for long...')
lbhPred = lmodel.predict(zscore(Xbh))[:,0]

logger.debug('Predicting if it\'s time for short...')
sbhPred = smodel.predict(zscore(Xbh))[:,0]

# Plot predicted
Xbh1_ = Xbh1[len(Xbh1)-availableSize+sampleSize-1:]
thresExp = 0.9
thresPred = 0.8
ys = [(lbh0, lbhPred, 'long'), (sbh0, sbhPred, 'short')]
plotPredicted(Xbh1_, ys, thresPredict=thresPred, thresExpect=thresExp,
              xlim=(Xbh1_.shape[0] - 1000, Xbh1_.shape[0]))

# Plot diff
plotDiff(Xbh1_, ys)

xlbhPred = np.where(lbhPred > thresPred)[0]
xsbhPred = np.where(sbhPred > thresPred)[0]

logger.info('#lExpect={lex}, #lPredict={lpr}, #sExpect={sex}, #sPredict={spr}'
            .format(lex=np.where(lbh0 > thresExp)[0].shape[0],
                    lpr=np.where(lbhPred > thresPred)[0].shape[0],
                    sex=np.where(sbh0 > thresExp)[0].shape[0],
                    spr=np.where(sbhPred > thresPred)[0].shape[0]))

SHOW_LAST_PREDICTS = 24 * 3

for i in range(SHOW_LAST_PREDICTS, 0, -1):
  if i == 1:

    logger.warn('Current predicts are long={long:2.0f}%, short={short:2.0f}%'
                .format(i=i, long=lbhPred[-i] * 100, short=sbhPred[-i] * 100))
  else:
    logger.info('Predicts[{i:2.0f}] are long={long:2.0f}%, short={short:2.0f}%'
                .format(i=i, long=lbhPred[-i] * 100, short=sbhPred[-i] * 100))

if lbhPred[-1] > thresPred:
  logger.warn('Predicted chance to get LONG!, conf={conf:2.0f}, ask={ask:.0f}.'
              .format(conf=lbhPred[-1] * 100, ask=Xbh1[-1]))

if sbhPred[-1] > thresPred:
  logger.warn('Predicted chance to get SHORT!, conf={conf:2.0f}, ask={ask:.0f}.'
              .format(conf=sbhPred[-1] * 100, ask=Xbh1[-1]))

logger.debug('End prediction.')

longConf = lbhPred[-1].item()
shortConf = sbhPred[-1].item()

logger.debug('Registering confidences, long={long:.3f}, short={short:.3f}.'
             .format(long=longConf, short=shortConf))

config = readConfig('predict.ini')
reportConfidence(config, longConf, shortConf, logger)

logger.debug('End registering.')
