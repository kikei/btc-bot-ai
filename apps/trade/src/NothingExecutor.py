import logging

class NothingExecutor(object):
  def __init__(self, models, accountId, trader=None, logger=None):
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    pass

  def handleOpenLong(self, lot):
    self.logger.warn('Requested opening long position, lot={lot}, ignored.'
                     .format(lot=lot))
    return True

  def handleOpenShort(self, lot):
    self.logger.warn('Requested opening short position, lot={lot}, ignored.'
                     .format(lot=lot))
    return True

  def handleClose(self, position):
    self.logger.warn('Requested closing position={p}, ignored'
                     .format(p=position))
    return True
