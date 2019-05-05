import datetime
import logging
import numpy as np
from Models import Values
from classes import PlayerActions, OnePosition
from ActionsDispatcher import Action

class MainOperatorDBException(RuntimeError):
  pass

class MainOperator(object):
  def __init__(self, models, accountId, logger=None):
    self.models = models
    self.accountId = accountId
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    self.checkValues()

  def checkValues(self):
    required = [
      Values.OperatorSleepDuration,
      Values.OperatorLotInit,
      Values.OperatorTrendGradient,
      Values.OperatorTrendSize,
      Values.OperatorTrendWidth,
      Values.OperatorTrendStrengthLoad
    ]
    for k in required:
      value = self.getStoredValue(Values.OperatorSleepDuration)
      if value is None:
        msg = 'Setting "{k}" not initialized.'.format(k=k)
        raise MainOperatorDBException(msg)

  def getStoredValue(self, name):
    return self.models.Values.get(name, accountId=self.accountId)

  def setStoredValue(self, name, value):
    self.models.Values.set(name, value, accountId=self.accountId)

  def getCurrentEntries(self):
    durationRead = self.getStoredValue(Values.OperatorTrendStrengthLoad)
    now = datetime.datetime.now()
    after = now.timestamp() - durationRead
    values = self.models.TrendStrengths.all(after=after)
    return values
  
  def getOpenPositions(self):
    positions = self.models.Positions.currentOpen(accountId=self.accountId)
    positions = list(positions)
    def isSide(side):
      def _f(p):
        ones = p.positions
        return len(ones) > 0 and ones[0].side == side
      return _f
    longs = list(filter(isSide(OnePosition.SideLong), positions))
    shorts = list(filter(isSide(OnePosition.SideShort), positions))
    return longs, shorts
  
#   def save(self):
#     self.models.Values.set(Values.AdjusterSpeed, self.speed,
#                            accountId=self.accountId)
#     self.models.Values.set(Values.AdjusterLastDirection, self.lastDirection,
#                            accountId=self.accountId)
#
#   def lotFunction(self, x):
#     return self.initLot * self.decayLot ** (x - 1.)
#
#   def calc(self, direction):
#     speed = self.speed
#     if self.lastDirection * direction > 0:
#       speed += direction * self.step
#     else:
#       speed = direction * self.step
#     self.lastDirection = direction
#     self.speed = speed
#     self.save()
#     if abs(speed) < self.stop:
#       lot = self.lotFunction(abs(speed))
#       return max(lot, self.minLot) * direction
#     else:
#       return 0.0
  
  def isSleeping(self):
    now = datetime.datetime.now().timestamp()
    lastDate = self.getStoredValue(Values.OperatorLastFired)
    sleepDuration = self.getStoredValue(Values.OperatorSleepDuration)
    return \
      lastDate is not None and \
      sleepDuration is not None and \
      lastDate + sleepDuration >= now
  
  def checkEntriesSize(self, entries):
    minSize = self.getStoredValue(Values.OperatorTrendSize)
    N = len(entries)
    result = N >= minSize
    if not result:
      self.logger.debug('#trend-entries is not enough, N={n}.'.format(n=N))
    return result
  
  def checkEntriesTimeWidth(self, entries):
    minTimeWidth = self.getStoredValue(Values.OperatorTrendWidth)
    N = len(entries)
    t = np.zeros(N)
    for i in range(0, N):
      trend = entries[i]
      t[i] = trend.date.timestamp()
    tmax = np.max(t)
    tmin = np.min(t)
    result = tmax - tmin >= minTimeWidth
    if not result:
      self.logger.debug('Time width of trend entries is not enough, ' +
                        'tmax={tmax}, tmin={tmin}.'.format(tmax=tmax, tmin=tmin))
    return result
  
  def makeDecision(self, entries):
    """
    Returns 0 when there are no chance to buy/sell,
    +1 when to buy, -1 when to sell.
    """
    minGradient = self.getStoredValue(Values.OperatorTrendGradient)
    N = len(entries)
    if not self.checkEntriesSize(entries): return 0
    if not self.checkEntriesTimeWidth(entries): return 0
    t = np.zeros(N)
    v = np.zeros(N)
    for i in range(0, N):
      trend = entries[i]
      t[i] = trend.date.timestamp()
      v[i] = trend.strength - 0.5      # -0.5 <= v <= 0.5
    tmax = np.max(t)
    tmin = np.min(t)
    t = (t - tmin) / (tmax - tmin)     # 0 <= t <= 1.0
    f = np.polyfit(t, v, 1)            # f = ax + b
    f0 = np.inner(f, np.array([0, 1])) # f0 = b
    f1 = np.inner(f, np.array([1, 1])) # f1 = x + b
    self.logger.debug('Decision calculation finished, ' +
                      'f={f}, f(0)={f0}, f(1)={f1}.'.format(f=f, f0=f0, f1=f1))
    print('Decision calculation finished, ' +
          'f={f}, f(0)={f0}, f(1)={f1}.'.format(f=f, f0=f0, f1=f1))
    if f[0] > minGradient and f0 < 0 and f1 > 0:
      return +1
    if f[0] < -minGradient and f0 > 0 and f1 < 0:
      return -1
    return 0
  
  def calculateLot(self, entries=None, chance=None, longs=None, shorts=None):
    initLot = self.getStoredValue(Values.OperatorLotInit)
    if initLot is None:
      raise MainOperatorDBException('Setting "{k}" not initialized.'
                                    .format(k=Values.OperatorLotInit))
    if chance > 0:
      return initLot
    elif chance < 0:
      return -initLot
    else:
      return 0.

  def createAction(self):
    # Don't do anything just after last action.
    if self.isSleeping():
      self.logger.debug('Main operator is sleeping.')
      return None
    # Get latest predictions.
    entries = self.getCurrentEntries()
    # Decide if it is chance for doing positions.
    chance = self.makeDecision(entries)
    self.logger.debug('Decision is: chance={c}.'.format(c=chance))
    if chance == 0:
      return None
    # Open/close existing positions
    longs, shorts = self.getOpenPositions()
    if chance == +1 and len(shorts) > 0:
      return Action(PlayerActions.CloseForProfit, shorts[0])
    elif chance == -1 and len(longs) > 0:
      return Action(PlayerActions.CloseForProfit, longs[0])
    # Open new position
    lot = self.calculateLot(entries=entries, chance=chance,
                            longs=longs, shorts=shorts)
    self.logger.debug('Calculated lot is: lot={l}.'.format(l=lot))
    if lot > 0.:
      return Action(PlayerActions.OpenLong, lot)
    elif lot < 0.:
      return Action(PlayerActions.OpenShort, -lot)
    else:
      return None
