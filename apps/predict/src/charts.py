import numpy as np


def SMA(k, x):
  n = x.size
  y = np.zeros(n)
  for i in range(1, n+1):
    e = n - i + k + 1
    if e > n:
      e = n
    y[n-i] = np.average(x[n-i:e])
  return y

def Sigma(k, x):
  n = x.size
  d = x - SMA(k, x)
  y = np.zeros(n)
  for i in range(1, n+1):
    e = n - i + k + 1
    if e > n:
      e = n
    y[n-i] = np.sum(d[n-i:e] * d[n-i:e]) / k
  return np.sqrt(y)

def Medium(k, x):
  n = x.size
  y = np.zeros(n-k+1)
  for i in range(0, n-k+1):
    y[i] = (np.max(x[i:i+k]) + np.min(x[i:i+k])) / 2
  return y

def RSI(x, k, slide=None):
  N = x.shape[0]
  if slide is None:
    slide = 0
  y = np.zeros(x.shape)
  dx = x[1:] - x[:N-1]
  for i in range(0, N - 1):
    s = i - k + slide
    if s < 0: s = 0
    e = i + slide
    if e >= N - 1: e = N - 2
    inc = np.sum(dx[s + np.where(dx[s:e] > 0)[0]])
    dec = np.sum(dx[s + np.where(dx[s:e] < 0)[0]])
    if inc - dec == 0:
      y[i+1] = 0
    else:
      y[i+1] = inc / (inc - dec)
  return y

class BollingerBand(object):
  def __init__(self, x, k=28):
    self.x = x
    self.k = k
  
  def sigmaLine(self, n):
    return SMA(self.k, self.x) + n * Sigma(self.k, self.x)

class Ichimoku(object):
  def __init__(self, x, kConv=9, kBase=26, kPrec=52, kLag=25, sameSize=False):
    self.x = x
    self.kConv = kConv
    self.kBase = kBase
    self.kPrec = kPrec
    self.kLag = kLag
    self.sameSize = sameSize
  
  def convertionLine(self, kConv=None, sameSize=None):
    if kConv is None: kConv = self.kConv
    if sameSize is None: sameSize = self.sameSize
    conv = Medium(kConv, self.x)
    if sameSize:
      y = np.zeros(self.x.shape)
      y[kConv-1:] = conv
      return y
    else:
      return conv
  
  def baseLine(self, kBase=None, sameSize=None):
    if kBase is None: kBase = self.kBase
    if sameSize is None: sameSize = self.sameSize
    base = Medium(kBase, self.x)
    if sameSize:
      y = np.zeros(self.x.shape)
      y[kBase-1:] = base
      return y
    else:
      return base
  
  def precedingLine1(self, shift=None, kConv=None, kBase=None, sameSize=None):
    if shift is None: shift = self.kBase - 1
    if kConv is None: kConv = self.kConv
    if kBase is None: kBase = self.kBase
    if sameSize is None: sameSize = self.sameSize
    conv = self.convertionLine(kConv, sameSize=True)
    base = self.baseLine(kBase, sameSize=True)
    prec = ((conv + base) / 2)[kBase-1:]
    if sameSize:
      y = np.zeros(self.x.shape)
      y[kBase+shift-1:] = prec[:-shift]
      return y
    else:
      return prec
  
  def precedingLine2(self, shift=None, kPrec=None, sameSize=None):
    if shift is None: shift = self.kBase - 1
    if kPrec is None: kPrec = self.kPrec
    if sameSize is None: sameSize = self.sameSize
    prec = Medium(kPrec, self.x)
    if sameSize:
      y = np.zeros(self.x.shape)
      y[kPrec+shift-1:] = prec[:-shift]
      return y
    else:
      return prec
  
  def laggingLine(self, kLag=None, sameSize=None):
    if kLag is None: kLag = self.kLag
    if sameSize is None: sameSize = self.sameSize
    lagg = self.x[kLag:]
    if sameSize:
      y = np.zeros(self.x.shape)
      y[0:-kLag] = lagg
      return y
    else:
      return lagg
