import time
from Models import Models, Values
from classes import Confidence

class PassListener(object):
  def __init__(self):
    pass

  def handleEntry(self):
    return None

class ConfidenceMonitor(object):
  def __init__(self, models, accountId, loop=True, monitorInterval=3, logger=None):
    self.models = models
    self.accountId = accountId
    self.logger = logger
    self.listener = PassListener()
    self.monitorInterval = monitorInterval
    self.loop = loop

  def setListener(self, listener):
    self.listener = listener
    return self

  def getEnabled(self):
    return self.models.Values.get(Values.Enabled, accountId=self.accountId)

  def getNewConfidence(self):
    Confidences = self.models.Confidences
    return Confidences.oneNew(accountId=self.accountId)

  def start(self):
    models = self.models
    while True:
      if not self.getEnabled():
        self.logger.debug('Currently disabled.')
      else:
        self.logger.debug('Reading new confidence.')
        confidence = self.getNewConfidence()
        try:
          self.listener.handleEntry(confidence)
        except FinishMonitoring as e:
          self.logger.debug('Finished monitoring.')
          break
      if not self.loop:
        break
      time.sleep(self.monitorInterval)
  
class FinishMonitoring(Exception):
  @staticmethod
  def raiseEvent(msg):
    raise FinishMonitoring(msg)
