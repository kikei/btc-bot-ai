import numpy as np


def mergeDicts(*dicts):
  if len(dicts) == 0:
    return {}
  m = dicts[0].copy()
  for d in dicts[1:]:
    m.update(d)
  return m


class Plotter(object):
  def __init__(self, plt, subplots=None, **kwargs):
    self.plt = plt
    if subplots is not None:
      fig, axs = self.plt.subplots(*subplots)
      self.fig = fig
      self.axs = axs
    else:
      plt.clf()
      self.fig = None
      self.axs = None
    self.colors = [
      '#b80117', '#222584', '#00904a', '#0168b3', '#6d1782',
      '#d16b16', '#a0c238'
    ]
    self.indexColors = 0
    self.kwargs = kwargs
  
  def subplot(self, n):
    return self.axs[n]
  
  def plot(self, x, y, n=None, **kwargs):
    kwargs = mergeDicts(self.kwargs, kwargs)
    if 'color' not in kwargs:
      kwargs['color'] = self.colors[self.indexColors % len(self.colors)]
      self.indexColors += 1
    if self.fig is None:
      self.plt.plot(x, y, **kwargs)
    else:
      self.axs[n].plot(x, y, **kwargs)
  
  def scatter(self, x, y, n=None, **kwargs):
    kwargs = mergeDicts(self.kwargs, kwargs)
    if 'color' not in kwargs:
      kwargs['color'] = self.colors[self.indexColors % len(self.colors)]
      self.indexColors += 1
    if self.fig is None:
      self.plt.scatter(x, y, **kwargs)
    else:
      self.axs[n].scatter(x, y, **kwargs)
  
  def hlines(self, y, x0, x1, n=None, **kwargs):
    kwargs = mergeDicts(self.kwargs, kwargs)
    if 'color' not in kwargs:
      kwargs['color'] = self.colors[self.indexColors % len(self.colors)]
      self.indexColors += 1
    if self.fig is None:
      self.plt.hlines(y, x0, x1, **kwargs)
    else:
      self.axs[n].hlines(y, x0, x1, **kwargs)
  
  def vlines(self, x, y0, y1, n=None, **kwargs):
    kwargs = mergeDicts(self.kwargs, kwargs)
    if 'color' not in kwargs:
      kwargs['color'] = self.colors[self.indexColors % len(self.colors)]
      self.indexColors += 1
    if self.fig is None:
      self.plt.vlines(x, y0, y1, **kwargs)
    else:
      self.axs[n].vlines(x, y0, y1, **kwargs)
  
  def limit(self, y, xlim, n=0, padding=1e-2):
    if isinstance(y, np.ndarray):
      if xlim[0] > xlim[1]:
        raise ValueError('invalid limit')
      x = y[xlim[0]:xlim[1]]
      ylim = np.min(x) * (1. - padding), np.max(x) * (1. + padding)
    else:
      ylim = y
    if self.fig is None:
      self.plt.xlim(xlim)
      self.plt.ylim(ylim)
    else:
      self.axs[n].set_xlim(xlim)
      self.axs[n].set_ylim(ylim)
      
  def show(self):
    if self.fig is None:
      self.plt.legend()
      self.plt.show()
    else:
      for ax in self.axs:
        ax.legend()
  
  def savefig(self, fname, dpi=1280):
    if self.fig is None:
      self.plt.legend()
    else:
      for ax in self.axs:
        ax.legend()
    self.plt.savefig(fname, dpi=dpi)
  
  def nextColor(self):
    color = self.colors[self.indexColors % len(self.colors)]
    self.indexColors += 1
    return color    
