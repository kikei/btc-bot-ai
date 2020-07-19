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
      Values.OperatorTrendStrengthLoad,
      Values.OperatorPositionsMax
    ]
    for k in required:
      value = self.getStoredValue(k)
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
    values = self.models.TrendStrengths.all(after=after,
                                            accountId=self.accountId)
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
  
  def isSleeping(self):
    now = datetime.datetime.now().timestamp()
    lastDate = self.getStoredValue(Values.OperatorLastFired)
    sleepDuration = self.getStoredValue(Values.OperatorSleepDuration)
    return \
      lastDate is not None and \
      sleepDuration is not None and \
      lastDate + sleepDuration >= now
  
  def updateLastFired(self):
    now = datetime.datetime.now().timestamp()
    self.setStoredValue(Values.OperatorLastFired, now)
  
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

  def getPositionVariation(self):
    tick = self.models.Ticks.one()
    longs, shorts = self.getOpenPositions()
    onePosition = None
    varLongs = []
    varShorts = []
    if len(longs) > 0:
      onePosition = longs[0].positions[0]
    elif len(shorts) > 0:
      onePosition = shorts[0].positions[0]
    if onePosition is not None:
      varLongs = [sum(tick.exchanger(o.exchanger).ask / o.priceMean()
                      for o in p.positions) for p in longs]
      varShorts = [sum(tick.exchanger(o.exchanger).bid / o.priceMean()
                       for o in p.positions) for p in shorts]
    return {
      'long': varLongs,
      'short': varShorts
    }

  def getPositionSize(self):
    longs, shorts = self.getOpenPositions()
    amountLong = sum(sum(o.sizeWhole() for o in p.positions) for p in longs)
    amountShort = sum(sum(o.sizeWhole() for o in p.positions) for p in shorts)
    return {
      'long': amountLong,
      'short': amountShort,
      'total': amountLong - amountShort
    }
  
  def checkPositionsCount(self, chance):
    maxPositions = self.getStoredValue(Values.OperatorPositionsMax)
    position = self.getPositionSize()
    amountLong = position['long']
    amountShort = position['short']
    self.logger.info('Check positions count, long={l}, short={s}'
                     .format(l=amountLong, s=amountShort))
    if chance > 0:
      return amountLong - amountShort < maxPositions
    elif chance < 0:
      return amountShort - amountLong < maxPositions
    else:
      return False
  
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
                      'f={f}, f(0)={f0}, f(1)={f1}.'
                      .format(f=f, f0=f0, f1=f1))
    strength1 = 0.0
    strength2 = 0.02
    chance = None
    if f[0] > minGradient and \
      ((f0 < strength1 < f1 and strength1 < v[0]) or \
       (strength1 < f0 < strength2 and strength1 < v[0])):
      self.logger.warning('Decision is +1(long, open), ' +
                          'f={f}, f(0)={f0:.5f}, f(1)={f1:.5f}, entries=[{e}].'
                          .format(f=f, f0=f0, f1=f1,
                                  e=', '.join(map(str, entries))))
      chance = +1
    if f[0] < -minGradient and \
      ((f0 > -strength1 > f1 and -strength1 > v[0]) or \
       (-strength1 > f0 > -strength2 and -strength1 > v[0])):
      self.logger.warning('Decision is -1(down, open), ' +
                          'f={f}, f(0)={f0:.5f}, f(1)={f1:.5f}, entries=[{e}].'
                          .format(f=f, f0=f0, f1=f1,
                                  e=', '.join(map(str, entries))))
      chance = -1
    position = self.getPositionSize()
    variations = self.getPositionVariation()
    amount = position['total']
    self.logger.warning('Positions: amount={a}, variations={v}'.format(a=amount, v=variations))
    if chance is None and f[0] < 0 and amount > 0 and \
       len(variations['long']) > 0 and variations['long'][-1] > 1.0:
      self.logger.warning('Decision is -1(short, profit), positions oppose trend, ' +
                          'f={f}, f(0)={f0:.5f}, f(1)={f1:.5f}, entries=[{e}].'
                          .format(f=f, f0=f0, f1=f1,
                                  e=', '.join(map(str, entries))))
      chance = -1
    if chance is None and f[0] > 0 and amount < 0 and \
       len(variations['short']) > 0 and variations['short'][-1] < 1.0:
      self.logger.warning('Decision is +1(long, profit), positions oppose trend, ' +
                          'f={f}, f(0)={f0:.5f}, f(1)={f1:.5f}, entries=[{e}].'
                          .format(f=f, f0=f0, f1=f1,
                                  e=', '.join(map(str, entries))))
      chance = +1
    minGradientLossCut = 0.
       #f0 < 0 and 
    if chance is not None and \
       f[0] < -minGradientLossCut and \
       f1 < 0 and \
       len(variations['long']) > 0 and variations['long'][-1] < 1.0:
      self.logger.warning('Decision is -1(short, losscut), positions oppose trend, ' +
                          'f={f}, f(0)={f0:.5f}, f(1)={f1:.5f}, entries=[{e}].'
                          .format(f=f, f0=f0, f1=f1,
                                  e=', '.join(map(str, entries))))
      chance = -1
       #f0 > 0 and 
    if chance is not None and \
       f[0] > minGradientLossCut and \
       f1 > 0 and \
       len(variations['short']) > 0 and variations['short'][-1] > 1.0:
      self.logger.warning('Decision is +1(long, losscut), positions oppose trend, ' +
                          'f={f}, f(0)={f0:.5f}, f(1)={f1:.5f}, entries=[{e}].'
                          .format(f=f, f0=f0, f1=f1,
                                  e=', '.join(map(str, entries))))
      chance = +1
    if chance is None: return 0
    if not self.checkPositionsCount(chance): return 0
    return chance
  
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

  def getAction(self):
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
      self.logger.info('Action is CloseForProfit, ' +
                       'chance={c}, position={p}, #short={n}'
                       .format(c=chance, p=shorts[-1], n=len(shorts)))
      return Action(PlayerActions.CloseForProfit, shorts[-1])
    elif chance == -1 and len(longs) > 0:
      self.logger.info('Action is CloseForProfit, ' +
                       'chance={c}, position={p}, #long={n}'
                       .format(c=chance, p=longs[-1], n=len(longs)))
      return Action(PlayerActions.CloseForProfit, longs[-1])
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
  
  def createAction(self):
    # Don't do anything just after last action.
    if self.isSleeping():
      self.logger.debug('Main operator is sleeping.')
      return None
    action = self.getAction()
    if action is not None:
      self.logger.warning('New action created, action={a}.'.format(a=action))
      self.updateLastFired()
    return action
