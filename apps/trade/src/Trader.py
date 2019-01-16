import logging
from Markets import Markets
import market.MarketConstants as MarketConst
from classes import Tick

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
      self.logger.error('Failed to open long position for bitflyer, lot={lot}.'
                        .format(lot=lot))
      return None
    return position

  def openShortPosition(self, lot):
    """
    (self: Trader, lot: float) -> OnePosition
    """
    position = self.openBitflyer(MarketConst.SHORT, None, lot)
    if position is None:
      self.logger.error('Failed to open position for bitflyer, lot={lot}.'
                        .format(lot=lot))
      return None
    return position

  def closePosition(self, position):
    """
    (self: Trader, position: OnePosition) -> OnePosition
    """
    side = MarketConst.SHORT
    lot = position.sizeWhole()
    if position.exchanger == Tick.BitFlyer:
      position = self.closeBitflyer(position)
      if position is None:
        self.logger.error('Failed to close position, side={s}, lot={l}.'
                          .format(s=side, l=lot))
        return None
      return position
    raise NotImplementedError('Closing position for position.exchanger={e}'
                              .format(e=position.exchanger))

  def openBitflyer(self, side, price, lot):
    """
    (self: Trader, side: str, price: float, lot: float) -> OnePosition
    """
    bitflyer = self.markets.BitFlyer
    position = bitflyer.open_position(side, price, lot)
    return position

  def closeBitflyer(self, position):
    """
    (self: Trader, position: OnePosition) -> OnePosition
    """
    bitflyer = self.markets.BitFlyer
    position = bitflyer.close_position(position)
    return position
