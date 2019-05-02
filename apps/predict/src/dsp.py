import numpy as np

def lpfilter(size):
  return np.full(size, 1.0 / size)

def crosszero(v, thres=0., ud=+1.0, du=-1.0):
  w = np.zeros(v.shape)
  iud = idu = None
  for i in range(1, len(v)):
    if v[i-1] > 0. > v[i]:
      if -thres > v[i]:
        w[i] = du
      else:
        idu = i
    elif v[i-1] > -thres > v[i] and idu is not None:
      w[idu] = du
      idu = None
    elif v[i-1] < 0. < v[i]:
      if thres < v[i]:
        w[i] = ud
      else:
        iud = i
    elif v[i-1] < thres < v[i] and iud is not None:
      w[iud] = ud
      iud = None
  return w
