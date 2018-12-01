from abc import ABCMeta, abstractmethod

class AbstractListener(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def handleEntry(self):
    raise NotImplementedError('handleEntry')
