import time
from .AbstractMonitor import AbstractMonitor
from Models import Models, Values
from classes import Confidence

class ConfidenceMonitor(AbstractMonitor):
  def getNewConfidence(self):
    return self.models.Confidences.oneNew()
  
  def monitor(self):
    self.logger.debug('Reading new confidence.')
    confidence = self.getNewConfidence()
    self.listener.handleEntry(confidence)


class PositionMonitor(AbstractMonitor):
  def getOpenedPosition(self):
    return self.models.Positions.currentOpen()
  
  def monitor(self):
    self.logger.debug('Reading opening position.')
    position = self.getOpeningPoistion()
    self.listener.handleEntry(position)
