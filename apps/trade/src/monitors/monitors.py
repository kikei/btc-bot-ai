from .AbstractMonitor import AbstractMonitor

class PositionsMonitor(AbstractMonitor):
  def __init__(self, models, accountId, loop=False, logger=None, player=None):
    super().__init__(models, accountId, loop=loop, logger=logger)
    self.player = player
  
  def handleEntry(self, entry):
    if len(entry) > 0:
      self.logger.info('Open positions exists, #p={n}.'
                       .format(n=len(entry)))
      self.player.run()
    else:
      self.logger.debug('No opening position.')
  
  def getOpenPosition(self):
    return self.models.Positions.currentOpen(accountId=self.accountId)
  
  def monitor(self):
    self.logger.debug('Reading opening position.')
    position = self.getOpenPosition()
    self.handleEntry(position)

class TrendMonitor(AbstractMonitor):
  def __init__(self, models, accountId, loop=False, logger=None, player=None):
    super().__init__(models, accountId, loop=loop, logger=logger)
    self.player = player
    self.lastEntry = None

  def handleEntry(self, entry):
    if entry is not None and \
       (self.lastEntry is None or self.lastEntry < entry.date):
      self.logger.info('New trend entry received, entry={e}.'.format(e=entry))
      self.player.run()
    else:
      self.logger.debug('No new entry.')

  def getNewTrend(self):
    return self.models.TrendStrengths.oneNew(accountId=self.accountId)

  def monitor(self):
    self.logger.debug('Reading new trend strength.')
    strength = self.getNewTrend()
    self.handleEntry(strength)
