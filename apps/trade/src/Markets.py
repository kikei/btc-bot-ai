import os
import sys
import logging

from market.BitFlyer import BitFlyer
from market.Quoine import Quoine
from market.Binance import Binance

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'conf'))

import Properties

class Markets(object):
  def __init__(self, logger=None):
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    self.BitFlyer = self.create_bitflyer_instance()
    self.Quoine = self.create_quoine_instance()
    self.Binance = self.create_binance_instance()

  def create_bitflyer_instance(self):
    return BitFlyer(Properties.BITFLYER_USER_SECRET,
                    Properties.BITFLYER_ACCESS_KEY,
                    logger=self.logger)

  def create_quoine_instance(self):
    return Quoine(Properties.QUOINE_USER_ID,
                  Properties.QUOINE_USER_SECRET,
                  logger=self.logger)

  def create_binance_instance(self):
    return Binance(Properties.BINANCE_API_KEY,
                   Properties.BINANCE_SECRET_KEY,
                   config={
                     'tick.unit': 4.0
                   },
                   logger=self.logger)


"""
import main
from Markets import Markets
logger = main.get_logger()
markets = Markets(logger)
quoine = markets.Quoine
"""
