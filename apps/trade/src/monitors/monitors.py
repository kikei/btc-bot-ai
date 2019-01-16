import time
from .AbstractMonitor import AbstractMonitor
from Models import Models, Values
from classes import Confidence

class ConfidenceMonitor(AbstractMonitor):
  def getNewConfidence(self):
    return self.models.Confidences.oneNew(accountId=self.accountId)
  
  def monitor(self):
    self.logger.debug('Reading new confidence.')
    confidence = self.getNewConfidence()
    self.listener.handleEntry(confidence)


class PositionMonitor(AbstractMonitor):
  def getOpenPosition(self):
    return self.models.Positions.currentOpen(accountId=self.accountId)
  
  def monitor(self):
    self.logger.debug('Reading opening position.')
    position = self.getOpenPosition()
    self.listener.handleEntry(position)
