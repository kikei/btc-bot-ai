import datetime
import logging

from Trader import Trader
from decimal import Decimal
from classes import Trade, Confidence

class TradeExecutor(object):
  def __init__(self, models, accountId, trader=None, logger=None):
    self.models = models
    self.accountId = accountId
    if trader is None:
      trader = Trader(logger=logger)
    self.trader = trader
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    self.minPrecision = 2

  def roundLot(self, lot):
    return float(round(Decimal.from_float(lot), self.minPrecision))
  
  def openPosition(self, lot, traderFun):
    """
    (self: TradeExecutor, lot: float) -> Trade
    """
    models = self.models
    try:
      position = traderFun(lot)
      self.logger.debug('Result of opening position is, position={position}.'
                        .format(position=position))
      if position is None:
        return None
    except Exception as e:
      self.logger.error(('Unexpected error occured in opening position, e={e}'
                         .format(e=e)))
      return None
    trade = Trade(datetime.datetime.now(), position)
    trade = models.Trades.save(trade, accountId=self.accountId)
    return trade

  def handleOpen(self, confidence, lot, traderFun):
    """
    (self: TradeExecutor, confidence: Confidence, lot: float,
     traderFun: (lot: float) -> OnePosition) -> Trade
    """
    # Open position
    lot = self.roundLot(lot)
    if lot == 0.0:
      self.logger.warning('Skipped opening position as too little lot.')
      return False
    self.logger.warning('Start opening position, lot={lot}.'.format(lot=lot))
    trade = self.openPosition(lot, traderFun)
    if trade is None:
      self.logger.error('Failed to open position, lot={lot}.'.format(lot=lot))
      return False
    # Update DB
    models = self.models
    confidence.updateStatus(Confidence.StatusUsed)
    models.Confidences.save(confidence, accountId=self.accountId)
    self.logger.warning('Successfully opened, trade={}'.format(trade))
    return True

  def handleOpenLong(self, confidence, lot):
    """
    (self: TradeExecutor, confidence: Confidence, lot: float) -> Trade
    """
    return self.handleOpen(confidence, lot, self.trader.openLongPosition)
  
  def handleOpenShort(self, confidence, lot):
    """
    (self: TradeExecutor, confidence: Confidence, lot: float) -> Trade
    """
    return self.handleOpen(confidence, lot, self.trader.openShortPosition)
    
  def handleIgnoreConfidence(self, confidence):
    """
    (self: TradeExecutor, confidence: Confidence) -> None
    """
    self.logger.info('Updating to ignored, conf={c}'.format(c=confidence))
    models = self.models
    confidence.updateStatus(Confidence.StatusIgnored)
    models.Confidences.save(confidence, accountId=self.accountId)
    self.logger.info('Successfully updated, conf={c}'.format(c=confidence))

