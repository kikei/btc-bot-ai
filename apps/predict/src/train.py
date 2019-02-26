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
from keras.layers.recurrent import LSTM
from keras import backend as K

from Plotter import Plotter
from learningUtils import validated, to2d, zscore, round_binary_accuracy, underSampling, balance, saveModel
from utils import readConfig, getLogger, loadnpy

logger = getLogger()
config = readConfig('predict.ini')
logger.info('Training started.')

OFFSET_SAMPLES = config['train'].getint('samples.offset')
INPUT_SIZE = config['train'].getint('fitting.inputsize')
BATCH_SIZE = config['train'].getint('fitting.batchsize')
EPOCHS = config['train'].getint('fitting.epochs')
SAMPLES_PREDICT = config['train'].getint('samples.predict')
ACCURACY_MIN = config['train'].getfloat('accuracy.min')

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

def fitLSTM(X, y, model, rateTrain=0.9, epochs=1000, batchSize=64):
  Xu, yu = balance(X, y, thres=0.5)
  trainCount = int(Xu.shape[0] * rateTrain)
  indexRandom = np.random.permutation(Xu.shape[0])
  indexTrain = indexRandom[:trainCount]
  XTrain = Xu[indexTrain]
  yTrain = yu[indexTrain]
  #XTrain = np.reshape(XTrain, (XTrain.shape[0], 1, XTrain.shape[1]))
  hist = model.fit(XTrain, yTrain, batch_size=batchSize, epochs=epochs,
                   verbose=1, validation_split=0.1, shuffle=True)
  return hist

def buildModel_1(inputShape):
  model = Sequential()
  model.add(Dense(256, activation='relu', input_shape=inputShape))
  model.add(Dropout(0.5))
  model.add(Dense(256, activation='relu'))
  model.add(Dropout(0.5))
  model.add(Dense(32, activation='relu'))
  model.add(Dense(32, activation='relu'))
  model.add(Dense(1, activation='sigmoid'))
  return model

def buildModel(inputShape):
  model = Sequential()
  model.add(LSTM(128, input_shape=(inputShape), return_sequences=False))
  model.add(Dropout(0.5))
  model.add(Dense(128, activation='relu'))
  model.add(Dropout(0.5))
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


#X1 = loadnpy(config, 'bitflyer', 'daily', 'askAverage')
#X2 = loadnpy(config, 'bitflyer', 'daily', 'askMax')
#X3 = loadnpy(config, 'bitflyer', 'daily', 'askMin')
#X4 = loadnpy(config, 'quoine', 'daily', 'askAverage')
#X5 = loadnpy(config, 'quoine', 'daily', 'askMax')
#X6 = loadnpy(config, 'quoine', 'daily', 'askMin')
Xbh1 = loadnpy(config, 'bitflyer', 'hourly', 'askAverage')[OFFSET_SAMPLES:]
Xbh2 = loadnpy(config, 'bitflyer', 'hourly', 'askMax')[OFFSET_SAMPLES:]
Xbh3 = loadnpy(config, 'bitflyer', 'hourly', 'askMin')[OFFSET_SAMPLES:]
Xbhb1 = loadnpy(config, 'bitflyer', 'hourly', 'askAverageBB+2')[OFFSET_SAMPLES:]
Xbhb2 = loadnpy(config, 'bitflyer', 'hourly', 'askAverageBB-2')[OFFSET_SAMPLES:]
Xbhi1 = loadnpy(config, 'bitflyer', 'hourly', 'askAverageConv')[OFFSET_SAMPLES:]
Xbhi2 = loadnpy(config, 'bitflyer', 'hourly', 'askAverageBase')[OFFSET_SAMPLES:]
Xbhi3 = loadnpy(config, 'bitflyer', 'hourly', 'askAveragePrc1')[OFFSET_SAMPLES:]
Xbhi4 = loadnpy(config, 'bitflyer', 'hourly', 'askAveragePrc2')[OFFSET_SAMPLES:]
Xbm1 = loadnpy(config, 'bitflyer', 'minutely', 'askAverage')
Xqm1 = loadnpy(config, 'quoine', 'minutely', 'askAverage')
#Xbhi5 = loadnpy(config, 'bitflyer', 'hourly', 'askOpenLag')
#longs = loadnpy(config, 'bitflyer', 'daily', 'askAverageLong')
#shorts = loadnpy(config, 'bitflyer', 'daily', 'askAverageShort')
lbh1 = loadnpy(config, 'bitflyer', 'hourly', 'askAverageLong')[OFFSET_SAMPLES:]
sbh1 = loadnpy(config, 'bitflyer', 'hourly', 'askAverageShort')[OFFSET_SAMPLES:]

#longs = validated(longs)
#shorts = validated(shorts)
lbh1 = validated(lbh1)
sbh1 = validated(sbh1)

sampleSize = INPUT_SIZE
featureCount = 9 + 60 * 2
lookBack = 1

availableSize = len(Xbhi4)
dataSize = availableSize - sampleSize + 1
Xbh0 = np.zeros((dataSize, sampleSize, featureCount))
print('Xbh0.shape={s}.'.format(s=Xbh0.shape))

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
availableSizeM = dataSize * 60 + sampleSize
d = datetime.datetime.now()
minutesToday = d.hour * 60 + d.minute
minutesInHour = d.minute
Xbh0[-1,0,9:69] = Xbm1[-sampleSize*60:]
Xbh0[:-1,0,9:69] = to2d(Xbm1[:-minutesInHour], 60,
                        available=availableSizeM, stride=60)
Xbh0[-1,0,69:129] = Xqm1[-sampleSize*60:]
Xbh0[:-1,0,69:129] = to2d(Xqm1[:-minutesInHour], 60,
                      available=availableSizeM, stride=60)

# dataSize = Xbh0.shape[0]
# Xbh = np.zeros((dataSize, Xbh0.shape[1] * Xbh0.shape[2]))
# for i in range(0, dataSize):
#   for j in range(0, featureCount):
#     Xbh[i,j*sampleSize:(j+1)*sampleSize] = Xbh0[i,:,j]
Xbh = Xbh0

lbh0 = lbh1[len(lbh1)-availableSize+sampleSize-1:]
sbh0 = sbh1[len(sbh1)-availableSize+sampleSize-1:]

trainRate = 1.0
unsupervisedSize = SAMPLES_PREDICT
trainSize = int((Xbh.shape[0] - unsupervisedSize) * trainRate)
XbhTrain, XbhTest = Xbh[0:trainSize], Xbh[trainSize:]

lbh0Train, lbh0Test = lbh0[0:trainSize], lbh0[trainSize:]
sbh0Train, sbh0Test = sbh0[0:trainSize], sbh0[trainSize:]

def zscoreWindow(x, window=16, axis=1):
  y = np.zeros(x.shape)
  for i in range(0, x.shape[0]):
    if i < window:
      start = 0
      end = window
      j = i
    else:
      start = i - window
      end = i
      j = window - 1
    y[i] = zscore(x[start:end], axis=axis)[j]
  return y

normalizeWindowSize = 256
XbhTrain = zscoreWindow(XbhTrain, window=normalizeWindowSize, axis=None)
XbhTest = zscoreWindow(XbhTest, window=normalizeWindowSize, axis=None)

logger.warn('Training for long timings train.shape={s}...'
            .format(s=XbhTrain.shape))
tlTrainStart = datetime.datetime.now()

# Input needs to be [samples, timesteps, features] in LSTM.
lmodel = buildModel(inputShape=(XbhTrain.shape[1], XbhTrain.shape[2]))
lmodel.compile(optimizer='adadelta', loss='binary_crossentropy',
               metrics=[round_binary_accuracy])
lhist = fitLSTM(XbhTrain, lbh0Train, lmodel,
                epochs=EPOCHS, batchSize=BATCH_SIZE)
plotHistory('../figures/lhist.svg', lhist,
            keyAccuracy='round_binary_accuracy')
tlTrainEnd = datetime.datetime.now()

logger.warn('Training for short timings...')
tsTrainStart = datetime.datetime.now()

smodel = buildModel(inputShape=(XbhTrain.shape[1], XbhTrain.shape[2]))
smodel.compile(optimizer='adadelta', loss='binary_crossentropy',
               metrics=[round_binary_accuracy])
shist = fitLSTM(XbhTrain, sbh0Train, smodel,
                epochs=EPOCHS, batchSize=BATCH_SIZE)
plotHistory('../figures/shist.svg', shist, keyAccuracy='round_binary_accuracy')
tsTrainEnd = datetime.datetime.now()

longAcc = lhist.history['val_round_binary_accuracy'][-1]
shortAcc = shist.history['val_round_binary_accuracy'][-1]

logger.warn(('Training done, longAcc.={long:.2f}, shortAcc.={short:.2f}, ' +
             '#samples={ns:.0f}, #epochs={ne:.0f}, #batchSize={nb:.0f}, ' +
             'longTime={lt:.1f}, shortTime={st:.1f}.')
            .format(long=longAcc * 100, short=shortAcc * 100,
                    ns=trainSize, ne=EPOCHS, nb=BATCH_SIZE,
                    lt=(tlTrainEnd - tlTrainStart).total_seconds(),
                    st=(tsTrainEnd - tsTrainStart).total_seconds()))

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
