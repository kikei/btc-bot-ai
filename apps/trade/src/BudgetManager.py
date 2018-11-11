import logging
from Models import Values
from classes import PlayerActions
from ActionsDispatcher import Action

class BudgetManagerDBException(RuntimeError):
  pass

class BudgetManager(object):
  def __init__(self, models, f=lambda x:0.5*0.8**x, logger=None):
    self.models = models
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    self.restore()
    self.f = f

  def restore(self):
    models = self.models
    step = models.Values.get(Values.AdjusterStep)
    if step is None:
      raise BudgetManagerDBException('Settings "{name}" not initialized.'
                                     .format(name=Values.AdjusterStep))
    self.step = step
    
    stop = models.Values.get(Values.AdjusterStop)
    if stop is None:
      raise BudgetManagerDBException('{name} not initialized.'
                                     .format(name=Values.AdjusterStop))
    self.stop = stop

    thresConf = models.Values.get(Values.AdjusterThresConf)
    if thresConf is None:
      raise BudgetManagerDBException('{name} not initialized.'
                                     .format(name=Values.AdjusterThresConf))
    self.thresConf = thresConf
    
    speed = models.Values.get(Values.AdjusterSpeed)
    if speed is None:
      speed = 0.0
    self.speed = speed
    
    lastDirection = models.Values.get(Values.AdjusterLastDirection)
    if lastDirection is None:
      lastDirection = 0.0
    self.lastDirection = lastDirection

  def save(self):
    self.models.Values.set(Values.AdjusterSpeed, self.speed)
    self.models.Values.set(Values.AdjusterLastDirection, self.lastDirection)

  def calc(self, direction):
    speed = self.speed
    if self.lastDirection * direction > 0:
      speed += direction * self.step
    else:
      speed = direction * self.step
    self.lastDirection = direction
    self.speed = speed
    self.save()
    if abs(speed) < self.stop:
      return self.f(abs(speed)) * direction
    else:
      return 0.0

  def makeDecision(self, confidence):
    if confidence.longConf > self.thresConf:
      return self.calc(+1)
    elif confidence.shortConf > self.thresConf:
      return self.calc(-1)
    return 0.
    
  def createAction(self, confidence):
    lot = self.makeDecision(confidence)
    self.logger.debug('Completed decision, lot={lot}.'.format(lot=lot))
    if lot > 0.0:
      return Action(PlayerActions.OpenLong, confidence, lot)
    elif lot < 0.0:
      return Action(PlayerActions.OpenShort, confidence, -lot)
    else:
      return None
