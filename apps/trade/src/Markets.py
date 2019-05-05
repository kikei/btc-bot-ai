import os
import sys
import logging

from market.BitFlyer import BitFlyer
from market.Quoine import Quoine

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

  def create_bitflyer_instance(self):
    return BitFlyer(Properties.BITFLYER_USER_SECRET,
                    Properties.BITFLYER_ACCESS_KEY,
                    logger=self.logger)

  def create_quoine_instance(self):
    return Quoine(Properties.QUOINE_USER_ID,
                  Properties.QUOINE_USER_SECRET,
                  logger=self.logger)

"""
import main
from Markets import Markets
logger = main.get_logger()
markets = Markets(logger)
quoine = markets.Quoine
"""
