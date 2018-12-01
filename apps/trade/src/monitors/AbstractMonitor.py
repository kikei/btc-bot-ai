from abc import ABCMeta
import logging

from .AbstractListener import AbstractListener, abstractmethod
from Models import Models, Values

class PassListener(AbstractListener):
  def handleEntry(self):
    return None

class AbstractMonitor(object):
  __metaclass__ = ABCMeta
  
  def __init__(self, models, loop=True, monitorInterval=3, logger=None):
    if logger is None:
      logger = logging.getLogger()
    self.models = models
    self.logger = logger
    self.listener = PassListener()
    self.monitorInterval = monitorInterval
    self.loop = loop
  
  def setListener(self, listener):
    self.listener = listener
    return self
  
  def getEnabled(self):
    return self.models.Values.get(Values.Enabled)
  
  def start(self):
    models = self.models
    try:
      while True:
        if not self.getEnabled():
          self.logger.debug('Currently disabled.')
        else:
          self.monitor()
        if not self.loop:
          break
        time.sleep(self.monitorInterval)
    except FinishMonitoring as e:
      self.logger.debug('Finished monitoring.')
 
  @abstractmethod
  def monitor(self):
    raise NotImplementedError('monitor')


class FinishMonitoring(Exception):
  @staticmethod
  def raiseEvent(msg):
    raise FinishMonitoring(msg)
