#!/bin/python3

import datetime
import logging
import os
import sys
sys.path.append('/usr/local/lib/python3.5/site-packages')

import pymongo

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'conf'))

from monitors.monitors import TrendMonitor, PositionsMonitor

import Properties

from classes import Confidence
from Models import Models
from MainOperator import MainOperator
from TrendPlayer import TrendPlayer
from PositionsPlayer import PositionsPlayer
from PositionsManager import PositionsManager
from TradeExecutor import TradeExecutor

def getDBInstance(host=None, port=None):
  server = 'mongodb://{user}:{password}@{host}:{port}'
  user = Properties.MONGO_USER
  password = Properties.MONGO_PASSWORD
  host = Properties.MONGO_HOST
  port  = Properties.MONGO_PORT
  assert all([user is not None,
              password is not None,
              host is not None,
              port is not None])
  server = server.format(host=host, port=port, user=user, password=password)
  client = pymongo.MongoClient(host=server)
  return client


def getModels(client):
  models = Models(client)
  return models


def getLogger():
  logger = Properties.getLogger(CWD)
  return logger


def checkProperties():
  names = []
  if Properties.ACCOUNT_ID is None:
    names.append('ACCOUNT_ID')
  if Properties.BITFLYER_USER_SECRET is None:
    names.append('BITFLYER_USER_SECRET')
  elif Properties.BITFLYER_ACCESS_KEY is None:
    names.append('BITFLYER_ACCESS_KEY')
  if len(names) != 0:
    print('Some properties are not set, {keys} is None.'
          .format(keys=', '.format(names)))
    return False
  return True

def defaultTrendMonitor(models, accountId, logger=None):
  creator = MainOperator(models, accountId=accountId, logger=logger)
  executor = TradeExecutor(models, accountId=accountId, logger=logger)
  player = TrendPlayer(models, accountId=accountId, logger=logger,
                       actionCreator=creator, actionExecutor=executor)
  return TrendMonitor(models, accountId=accountId, loop=False, logger=logger,
                      player=player)

def defaultPositionsMonitor(models, accountId, logger=None):
  creator = PositionsManager(models, accountId=accountId, logger=logger)
  executor = TradeExecutor(models, accountId=accountId, logger=logger)
  player = PositionsPlayer(models, accountId=accountId, logger=logger,
                           actionCreator=creator, actionExecutor=executor)
  return PositionsMonitor(models, accountId=accountId, loop=False, logger=logger,
                          player=player)


def runStep(logger=None):
  accountId = Properties.ACCOUNT_ID
  models = getModels(getDBInstance())
  monitors = [
    defaultTrendMonitor(models, accountId, logger),
    defaultPositionsMonitor(models, accountId, logger)
  ]
  for m in monitors: m.start()

def main():
  checkOk = checkProperties()
  if not checkOk:
    exit()
  logger = getLogger()
  try:
    runStep(logger)
  except Exception as e:
    logger.error(e)
    raise e

if __name__ == '__main__':
  main()
