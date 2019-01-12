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
from utils import readConfig, getLogger, loadnpy

logger = getLogger()
config = readConfig('predict.ini')
logger.info('Training started.')

ACCURACY_MIN = config['train'].getfloat('accuracy.min')

def fit(X, y, model, rateTrain=0.9, epochs=1000):
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
  model.add(Dense(512, activation='relu', input_shape=inputShape))
  model.add(Dropout(0.5))
  model.add(Dense(128, activation='relu'))
  model.add(Dropout(0.5))
  model.add(Dense(64, activation='relu'))
  model.add(Dropout(0.5))
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


X1 = loadnpy(config, 'bitflyer', 'daily', 'askAverage')
X2 = loadnpy(config, 'bitflyer', 'daily', 'askMax')
X3 = loadnpy(config, 'bitflyer', 'daily', 'askMin')
X4 = loadnpy(config, 'quoine', 'daily', 'askAverage')
X5 = loadnpy(config, 'quoine', 'daily', 'askMax')
X6 = loadnpy(config, 'quoine', 'daily', 'askMin')
Xbh1 = loadnpy(config, 'bitflyer', 'hourly', 'askAverage')
Xbh2 = loadnpy(config, 'bitflyer', 'hourly', 'askMax')
Xbh3 = loadnpy(config, 'bitflyer', 'hourly', 'askMin')
Xbhb1 = loadnpy(config, 'bitflyer', 'hourly', 'askAverageBB+2')
Xbhb2 = loadnpy(config, 'bitflyer', 'hourly', 'askAverageBB-2')
Xbhi1 = loadnpy(config, 'bitflyer', 'hourly', 'askAverageConv')
Xbhi2 = loadnpy(config, 'bitflyer', 'hourly', 'askAverageBase')
Xbhi3 = loadnpy(config, 'bitflyer', 'hourly', 'askAveragePrc1')
Xbhi4 = loadnpy(config, 'bitflyer', 'hourly', 'askAveragePrc2')
#Xbhi5 = loadnpy(config, 'bitflyer', 'hourly', 'askOpenLag')
longs = loadnpy(config, 'bitflyer', 'daily', 'askAverageLong')
shorts = loadnpy(config, 'bitflyer', 'daily', 'askAverageShort')
lbh1 = loadnpy(config, 'bitflyer', 'hourly', 'askAverageLong')
sbh1 = loadnpy(config, 'bitflyer', 'hourly', 'askAverageShort')

longs = validated(longs)
shorts = validated(shorts)
lbh1 = validated(lbh1)
sbh1 = validated(sbh1)

sampleSize = 24 * 7 * 1
batchSize = 64
featureCount = 9

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

dataSize = Xbh0.shape[0]
Xbh = np.zeros((dataSize, Xbh0.shape[1] * Xbh0.shape[2]))
for i in range(0, dataSize):
  for j in range(0, featureCount):
    Xbh[i,j*sampleSize:(j+1)*sampleSize] = Xbh0[i,:,j]

lbh0 = lbh1[len(lbh1)-availableSize+sampleSize-1:]
sbh0 = sbh1[len(sbh1)-availableSize+sampleSize-1:]

trainRate = 1.0
unsupervisedSize = 36
trainSize = int((Xbh.shape[0] - unsupervisedSize) * trainRate)
XbhTrain, XbhTest = Xbh[0:trainSize], Xbh[trainSize:]

lbh0Train, lbh0Test = lbh0[0:trainSize], lbh0[trainSize:]
sbh0Train, sbh0Test = sbh0[0:trainSize], sbh0[trainSize:]

XbhTrain = zscore(XbhTrain)
XbhTest = zscore(XbhTest)

logger.warn('Training for long timings...')

lmodel = buildModel((XbhTrain.shape[1],))
lmodel.compile(optimizer='adadelta', loss='binary_crossentropy',
               metrics=[round_binary_accuracy])
lhist = fit(XbhTrain, lbh0Train, lmodel, epochs=300)
plotHistory('../figures/lhist.svg', lhist,
            keyAccuracy='round_binary_accuracy')

logger.warn('Training for short timings...')

smodel = buildModel((XbhTrain.shape[1],))
smodel.compile(optimizer='adadelta', loss='binary_crossentropy',
               metrics=[round_binary_accuracy])
shist = fit(XbhTrain, sbh0Train, smodel, epochs=300)
plotHistory('../figures/shist.svg', shist, keyAccuracy='round_binary_accuracy')

longAcc = lhist.history['val_round_binary_accuracy'][-1]
shortAcc = shist.history['val_round_binary_accuracy'][-1]

logger.warn('Training done, longAcc.={long:.2f}, shortAcc.={short:.2f}.'
            .format(long=longAcc * 100, short=shortAcc * 100))

logger.info('Last accuracies are: long={long:.2f}, short={short:.2f}'
            .format(long=longAcc * 100, short=shortAcc * 100))


if longAcc < ACCURACY_MIN or shortAcc < ACCURACY_MIN:
  logger.error('Aborted because of insufficient accuracy.')
  exit()

saveModel(config, lmodel, 'long')
saveModel(config, smodel, 'short')

lbhPred = lmodel.predict(zscore(Xbh))[:,0]
sbhPred = smodel.predict(zscore(Xbh))[:,0]
Xbh1_ = Xbh1[len(Xbh1)-availableSize+sampleSize-1:]

thresExp = 0.9
thresPred = 0.8

logger.info('#lExpect={lex}, #lPredict={lpr}, #sExpect={sex}, #sPredict={spr}'
            .format(lex=np.where(lbh0 > thresExp)[0].shape[0],
                    lpr=np.where(lbhPred > thresPred)[0].shape[0],
                    sex=np.where(sbh0 > thresExp)[0].shape[0],
                    spr=np.where(sbhPred > thresPred)[0].shape[0]))

ys = [(lbh0, lbhPred, 'long'), (sbh0, sbhPred, 'short')]
plotPredicted(Xbh1_, ys, thresPredict=thresPred, thresExpect=thresExp,
              xlim=(Xbh1_.shape[0] - 1000, Xbh1_.shape[0]))

plotDiff(Xbh1_, ys)

logger.info('#Ticks={tick}, #Train={train}, #Predicted={predict}.'
            .format(tick=Xbh.shape[0], train=trainSize,
                    predict=Xbh.shape[0] - trainSize))

logger.info('Training completed.')
