from threading import Thread
import logging
import os
import pymongo
import sys
import time

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'conf'))

import Properties
from Models import Models
from Markets import Markets
from market.Binance import Binance
from market.BitFlyer import BitFlyer
from market.Quoine import Quoine
from classes import Tick

def getMongoAddress(host=None, port=None, user=None, password=None):
  # mongodb://{user}:{password}@{host}:{port}
  server = 'mongodb://'
  if user is not None:
    server += user
    if password is not None:
      server += ':{password}'.format(password=password)
    server += '@'
  server += host
  if port is not None:
    server += ':{port}'.format(port=port)
  return server

def getDBInstance(host=None, port=None):
  user = Properties.MONGO_USER
  password = Properties.MONGO_PASSWORD
  host = Properties.MONGO_HOST or '127.0.0.1'
  port  = Properties.MONGO_PORT
  address = getMongoAddress(host, port, user, password)
  client = pymongo.MongoClient(host=address)
  return client

def getModels(client):
  models = Models(client)
  return models

class Ticker(object):
  def __init__(self, model, exchanger, ticker,
               count=None, interval=1000, logger=None):
    assert model is not None
    assert exchanger is not None
    assert ticker is not None
    self.model = model
    self.exchanger = exchanger
    self.ticker = ticker
    self.count = count
    self.interval = interval
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger

  def stop(self):
    self.count = 0

  def start(self):
    exchanger = self.exchanger
    self.logger.info('Ticker, start `{e}`.'.format(e=exchanger))
    while self.count is None or self.count >= 0:
      try:
        onetick = self.ticker()
        self.logger.debug('Ticker exchanger={e}, tick={t}.'
                          .format(e=exchanger, t=onetick))
        self.model.save(Tick({exchanger: onetick}), exchangers=[exchanger])
        time.sleep(self.interval)
        if self.count is not None:
          self.count -= 1
      except Exception as e:
        self.logger.exception('Exception occur, e:{e}.'.format(e=e))
    self.logger.info('Ticker, stopped `{e}`.'.format(e=exchanger))

def main():
  models = getModels(getDBInstance())
  logger = Properties.getTickerLogger(CWD)
  markets = Markets(logger)
  entries = [
    (Tick.BinanceETHBTC, lambda: markets.Binance.get_tick('ETHBTC')),
    (Tick.BinanceXRPBTC, lambda: markets.Binance.get_tick('XRPBTC')),
    (Tick.BitFlyer, markets.BitFlyer.get_tick),
    (Tick.Quoine, markets.Quoine.get_tick)
  ]
  options = {
    'interval': 30,
    'logger': logger
  }
  tickers = (Ticker(models.Ticks, name, getTick, **options)
             for name, getTick in entries)
  threads = [Thread(target=t.start) for t in tickers]
  for thread in threads:
    thread.start()
  logger.debug('Ticker all closed.')

if __name__ == '__main__':
  main()
