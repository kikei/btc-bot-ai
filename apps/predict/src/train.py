import datetime

# Numpy
import numpy as np

# Matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Keras
from keras.layers import Dense, Dropout, Flatten
from keras.models import Model, Sequential
from keras import backend as K

from Plotter import Plotter
from learningUtils import validated, to2d, zscore, round_binary_accuracy, underSampling, balance, saveModel
from utils import readConfig, getLogger, loadnpy, StopWatch

logger = getLogger()
config = readConfig('predict.ini')
logger.info('Training started.')

OFFSET_SAMPLES = config['train'].getint('samples.offset')
INPUT_SIZE = config['train'].getint('fitting.inputsize')
BATCH_SIZE = config['train'].getint('fitting.batchsize')
EPOCHS = config['train'].getint('fitting.epochs')
SAMPLES_PREDICT = config['train'].getint('samples.predict')
ACCURACY_MIN = config['train'].getfloat('accuracy.min')

# Measure run time
timer = StopWatch()
timer.start()

def load(exchanger, unit, ty):
  return loadnpy(config, exchanger, unit, ty, nan=0.)

def fit(X, y, model, rateTrain=0.9, epochs=1000, batchSize=64):
  Xu, yu = balance(X, y, thres=0.5)
  trainCount = int(Xu.shape[0] * rateTrain)
  indexRandom = np.random.permutation(Xu.shape[0])
  indexTrain = indexRandom[:trainCount]
  XTrain = Xu[indexTrain]
  yTrain = yu[indexTrain]
  hist = model.fit(XTrain, yTrain, batch_size=batchSize, epochs=epochs,
                   verbose=1, validation_split=0.1, shuffle=True)
  return hist


def buildModel(inputShape):
  model = Sequential()
  model.add(Dense(256, activation='relu', input_shape=inputShape))
  model.add(Dropout(0.5))
  model.add(Dense(256, activation='relu'))
  model.add(Dropout(0.5))
  model.add(Dense(32, activation='relu'))
  model.add(Dense(32, activation='relu'))
  model.add(Dense(1, activation='sigmoid'))
  return model


def plotHistory(fname, hist, keyAccuracy='acc'):
  valKeyAccuracy = 'val_' + keyAccuracy
  plt.clf()
  fig, axs = plt.subplots(2, 1)
  fig.set_dpi(200)
  axs[0].set_xlabel('epochs')
  axs[0].plot(np.arange(0, len(hist.history['loss'])),
              hist.history['loss'], label='loss')
  axs[0].plot(np.arange(0, len(hist.history['loss'])),
              hist.history['val_loss'], label='val_loss')
  axs[0].legend()
  axs[1].set_xlabel('epochs')
  axs[1].plot(np.arange(0, len(hist.history[keyAccuracy])),
              hist.history[keyAccuracy], label=keyAccuracy)
  axs[1].plot(np.arange(0, len(hist.history[valKeyAccuracy])),
              hist.history[valKeyAccuracy], label=valKeyAccuracy)
  axs[1].legend()
  plt.savefig(fname)


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


Xbh1 = load('bitflyer', 'hourly', 'askAverage')[OFFSET_SAMPLES:]
Xbh2 = load('bitflyer', 'hourly', 'askMax')[OFFSET_SAMPLES:]
Xbh3 = load('bitflyer', 'hourly', 'askMin')[OFFSET_SAMPLES:]
Xbhb1 = load('bitflyer', 'hourly', 'askAverageBB+2')[OFFSET_SAMPLES:]
Xbhb2 = load('bitflyer', 'hourly', 'askAverageBB-2')[OFFSET_SAMPLES:]
Xbhi1 = load('bitflyer', 'hourly', 'askAverageConv')[OFFSET_SAMPLES:]
Xbhi2 = load('bitflyer', 'hourly', 'askAverageBase')[OFFSET_SAMPLES:]
Xbhi3 = load('bitflyer', 'hourly', 'askAveragePrc1')[OFFSET_SAMPLES:]
Xbhi4 = load('bitflyer', 'hourly', 'askAveragePrc2')[OFFSET_SAMPLES:]
Xbm1 = load('bitflyer', 'minutely', 'askAverage')
Xqm1 = load('quoine', 'minutely', 'askAverage')
ybh1 = load('bitflyer', 'hourly', 'askCloseTrend')[OFFSET_SAMPLES:]

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

skipOld = 0
dataSize = Xbh0.shape[0] - skipOld
Xbh = np.zeros((dataSize, Xbh0.shape[1] * Xbh0.shape[2]))
for i in range(0, dataSize):
  for j in range(0, featureCount):
    Xbh[i,j*sampleSize:(j+1)*sampleSize] = Xbh0[i+skipOld,:,j]

ybh0 = ybh1[len(ybh1)-availableSize+sampleSize-1+skipOld:]

trainRate = 1.0
unsupervisedSize = SAMPLES_PREDICT
trainSize = int((Xbh.shape[0] - unsupervisedSize) * trainRate)
XbhTrain, XbhTest = Xbh[0:trainSize], Xbh[trainSize:]

ybh0Train, ybh0Test = ybh0[0:trainSize], ybh0[trainSize:]

XbhTrain = zscore(XbhTrain)
XbhTest = zscore(XbhTest)

# Run fitting
logger.warn('Training for trend...')
yTrainStart = datetime.datetime.now()
yModel = buildModel((XbhTrain.shape[1],))
yModel.compile(optimizer='adam', loss='binary_crossentropy',
                metrics=[round_binary_accuracy])
yHist = fit(XbhTrain, ybh0Train, yModel, epochs=EPOCHS, batchSize=BATCH_SIZE)
yTrainEnd = datetime.datetime.now()
yAcc = yHist.history['val_round_binary_accuracy'][-1]
plotHistory('../figures/yhist.svg', yHist, keyAccuracy='round_binary_accuracy')

logger.warn(('Training done, trendAcc.={trend:.2f}, ' +
             '#samples={ns:.0f}, #epochs={ne:.0f}, #batchSize={nb:.0f}, ' +
             'trendTime={tt:.1f}.')
            .format(trend=yAcc * 100,
                    ns=trainSize, ne=EPOCHS, nb=BATCH_SIZE,
                    tt=(yTrainEnd - yTrainStart).total_seconds()))
logger.info('Training accuracies are: trend={trend:.2f}.'
            .format(trend=yAcc * 100))

if yAcc < ACCURACY_MIN:
  logger.error('Aborted because of insufficient accuracy.')
  exit(1)

saveModel(config, yModel, 'trend')

logger.debug('Predicting, Xbh.shape={x}.'.format(x=Xbh.shape))
logger.info('#Ticks={tick}, #Train={train}, #Predicted={predict}.'
            .format(tick=Xbh.shape[0], train=trainSize,
                    predict=Xbh.shape[0] - trainSize))

# Finished
seconds = timer.stop()
logger.info('Training completed, elapsed={s:.2f}s'.format(s=seconds))
