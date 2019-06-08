import logging

from binance.client import Client
from classes import Tick, OneTick

class BinanceAPIError(RuntimeError):
  pass

class Binance(object):
  def __init__(self, apiKey, apiSecret, config, logger=None):
    assert apiKey is not None
    assert apiSecret is not None
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    self.client = Client(apiKey, apiSecret)
    self.tickUnit = config['tick.unit'] or 1.0

  def get_tick(self, pair, reverse=False):
    # book = {
    #   lastUpdateId: str,
    #   bids: [[price: float, volume: float]],
    #   asks: [[price: float, volume: float]]
    # }
    book = self.client.get_order_book(symbol=pair)
    def get_price(orders, unit):
      if len(orders) == 0:
        return None
      acc = 0
      for [price, volume] in orders:
        acc += float(volume)
        if acc >= unit:
          break
      return float(price)
    bid = get_price(book['bids'], self.tickUnit)
    ask = get_price(book['asks'], self.tickUnit)
    if bid is None or ask is None:
      return None
    if not reverse:
      return OneTick(ask, bid)
    else:
      return OneTick(1. / bid, 1. / ask)



