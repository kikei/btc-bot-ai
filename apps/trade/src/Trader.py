import logging
from Markets import Markets
import market.MarketConstants as MarketConst

class Trader(object):
  def __init__(self, logger=None):
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    self.markets = Markets(logger)

  def openLongPosition(self, lot):
    """
    (self: Trader, lot: float) -> OnePosition
    """
    position = self.openBitflyer(MarketConst.LONG, None, lot)
    if position is None:
      self.logger.error('Failed to open position, side={side}, lot={lot}.'
                        .format(side=side, lot=lot))
      return None
    return position

  def openShortPosition(self, lot):
    """
    (self: Trader, lot: float) -> OnePosition
    """
    position = self.openBitflyer(MarketConst.SHORT, None, lot)
    if position is None:
      self.logger.error('Failed to open position, side={side}, lot={lot}.'
                        .format(side=side, lot=lot))
      return None
    return position

  def openBitflyer(self, side, price, lot):
    """
    (self: Trader, side: str, price: float, lot: float) -> OnePosition
    """
    bitflyer = self.markets.BitFlyer
    position = bitflyer.open_position(side, price, lot)
    return position
