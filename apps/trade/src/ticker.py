import datetime
import os
import pymongo
import sys
import time

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'conf'))

import Properties

from Models import Models
from CrossTrader import CrossTrader

DO_LOOP = True

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

def runMain(logger):
  try:
    models = getModels(getDBInstance())
    trader = CrossTrader(models, logger)
    tick = trader.get_tick()
    logger.info(str(tick))
    models.Ticks.save(tick)
  except Exception as e:
    logger.exception('例外が発生して終了しました。(e:{})'.format(e))


def loopMain(logger):
  try:
    models = getModels(getDBInstance())
    trader = CrossTrader(logger)
    while True:
      tick = trader.get_tick()
      logger.info(str(tick))
      models.Ticks.save(tick)
      time.sleep(3)
  except Exception as e:
    logger.exception('例外が発生して終了しました。(e:{})'.format(e))


if __name__ == '__main__':
  logger = Properties.getTickerLogger(CWD)
  if DO_LOOP:
    loopMain(logger)
  else:
    runMain(logger)
