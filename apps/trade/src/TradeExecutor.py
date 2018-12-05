import datetime
import logging

from Trader import Trader
from decimal import Decimal
from classes import Trade, Confidence, Position

class TradeExecutor(object):
  def __init__(self, models, trader=None, logger=None):
    self.models = models
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
    (self: TradeExecutor, lot: float) -> Trade, Position
    """
    models = self.models
    try:
      position = traderFun(lot)
      self.logger.debug('Result of opening position is, position={position}.'
                        .format(position=position))
      if position is None:
        return None, None
    except Exception as e:
      self.logger.error(('Unexpected error occured in opening position, e={e}'
                         .format(e=e)))
      return None, None
    now = datetime.datetime.now()
    trade_ = Trade(now, position)
    trade = models.Trades.save(trade_)
    position_ = Position(now, Position.StatusOpen, [position])
    position = models.Positions.save(position_)
    return trade, position

  def closePosition(self, position):
    """
    (self: TradeExecutor, position: Position) -> Trade, Position
    """
    models = self.models
    ones = []
    for p in position.positions:
      try:
        one = self.trader.closePosition(p)
        if one is None:
          continue
        ones.append(one)
      except Exception as e:
        self.logger.error('Unexpected error occured in closing position, e={e}'
                          .format(e=e))
        continue
    if len(ones) == 0:
      return None, None
    now = datetime.datetime.now()
    trades = []
    for one in ones:
      trade_ = Trade(now, one)
      trade = models.Trades.save(trade_)
      trades.append(trade)
    position.status = Position.StatusClose
    position = models.Positions.save(position)
    return trades, position
  
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
    trade, position = self.openPosition(lot, traderFun)
    if trade is None or position is None:
      self.logger.error('Failed to open position, lot={lot}.'.format(lot=lot))
      return False
    # Update DB
    models = self.models
    confidence.updateStatus(Confidence.StatusUsed)
    models.Confidences.save(confidence)
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
  
  def handleClose(self, position):
    """
    (self: TraderExecutor, position: Position) -> bool
    """
    if not position.isOpen():
      return False
    # Closing
    trade, position = self.closePosition(position)
    if trade is None or position is None:
      self.logger.error('Failed to close position, position={p}'
                        .format(p=position))
      return False
    # Update DB
    models = self.models
    models.Positions.save(position)
    self.logger.warning('Successfully closed, trade={t}'.format(t=trade))
    return True
