from keras.models import model_from_json
from keras import backend as K
import numpy as np


def loadModel(config, label):
  DIR_MODEL = config['train'].get('model.dir')
  JSON_MODEL = config['train'].get('model.json')
  H5_MODEL = config['train'].get('model.h5')
  pathJSON = (DIR_MODEL + '/' + JSON_MODEL).format(label=label)
  pathH5 = (DIR_MODEL + '/' + H5_MODEL).format(label=label)
  model = model_from_json(open(pathJSON).read())
  model.load_weights(pathH5)
  return model


def saveModel(config, model, label):
  DIR_MODEL = config['train'].get('model.dir')
  JSON_MODEL = config['train'].get('model.json')
  H5_MODEL = config['train'].get('model.h5')
  pathJSON = (DIR_MODEL + '/' + JSON_MODEL).format(label=label)
  pathH5 = (DIR_MODEL + '/' + H5_MODEL).format(label=label)
  open(pathJSON, 'w').write(model.to_json())
  model.save_weights(pathH5)


def sigmoid(z):
  z[np.where(z > 709)] = 709
  z[np.where(z < -745)] = -745
  return 1. / (1. + np.exp(-z))


def differentiate(v, sameSize=False):
  if sameSize:
    a = np.zeros(v.shape)
    a[0] = v[0]
    a[1:] = v[1:] - v[:-1]
    return a
  else:
    return v[1:] - v[:-1]


def isEqual(a, b, rate):
  return abs(1. * a / b - 1.) < rate


def validated(x):
  return x + 1e-5 if np.min(x) <= 0. else x


def round_binary_accuracy(y_true, y_pred):
  return K.mean(K.equal(K.round(y_true), K.round(y_pred)), axis=-1)


def zscore(x, axis=1, d=1e-5):
  xmean = np.mean(x, axis=axis, keepdims=True)
  xstd = np.std(x, axis=axis, keepdims=True)
  zscore = (x - xmean) / (xstd + d)
  return zscore


def to2d(X, sampleSize, stride=1, available=None):
  if available is not None:
    X = X[len(X) - available:]
  dataSize = (len(X) - sampleSize + 1) // stride
  X2 = np.zeros((dataSize, sampleSize))
  for i in range(0, dataSize):
    start = i * stride
    end = i * stride + sampleSize
    X2[i,:] = X[start:end]
  return X2


def underSampling(X, interval):
  indexes = np.arange(0, X.shape[0], interval)
  return X[indexes]


def balance(X, y, thres=0.5):
  positives = np.where(y > thres)[0] # long
  negatives = np.where(y < thres)[0]
  if positives.shape[0] > negatives.shape[0]:
    c = round(1.0 * positives.shape[0] / negatives.shape[0])
    positives = underSampling(positives, c)
  else:
    c = int(round(1.0 * negatives.shape[0] / positives.shape[0]))
    negatives = underSampling(negatives, c)
  indexes = np.concatenate([negatives, positives])
  return X[indexes,:], y[indexes]

