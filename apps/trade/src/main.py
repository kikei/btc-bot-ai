#!/bin/python3

import datetime
import logging
import os
import sys
sys.path.append('/usr/local/lib/python3.5/site-packages')

import pymongo

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'conf'))

from monitors.AbstractListener import AbstractListener
from monitors.monitors import ConfidenceMonitor, PositionMonitor

import Properties

from classes import Confidence
from Models import Models
from TradingPlayer import TradingPlayer
from PositionsPlayer import PositionsPlayer
from PositionsManager import PositionsManager
from TradeExecutor import TradeExecutor

def getDBInstance(host=None, port=None):
  if host is None:
    host = Properties.MONGO_HOST
  if port is None:
    port = Properties.MONGO_PORT
  client = pymongo.MongoClient(host=host, port=port)
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


class ConfidenceListener(object):
  def __init__(self, models, accountId, Player=None, logger=None):
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    if Player is None:
      Player = TradingPlayer
    self.player = Player(models, accountId=accountId, logger=logger)
  
  def handleEntry(self, confidence):
    expirePredict = datetime.timedelta(hours=1)
    now = datetime.datetime.now()
    if confidence is not None and \
       confidence.isStatusOf(Confidence.StatusNew) and \
       now - confidence.date < expirePredict:
      self.logger.info('New confidence received, confidence={confidence}.'
                       .format(confidence=confidence))
      self.player.run()
    else:
      self.logger.debug('No new confidence.')

class PositionListener(AbstractListener):
  def __init__(self, models, accountId, Player, logger=None):
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    self.player = Player(models, accountId=accountId, logger=logger)
  
  def handleEntry(self, positions):
    if len(positions) > 0:
      self.logger.info('Open positions exists, #p={n}.'
                       .format(n=len(positions)))
      self.player.run()
    else:
      self.logger.debug('No opening position.')

def createPositionsPlayer(models, accountId, logger=None):
  return PositionsPlayer(models,
		         ActionCreator=PositionsManager,
                         ActionExecutor=TradeExecutor,
                         accountId=accountId,
                         logger=logger)

def runStep(logger=None):
  accountId = Properties.ACCOUNT_ID
  models = getModels(getDBInstance())
  confidenceListener = ConfidenceListener(models, accountId=accountId, logger=logger)
  confidenceMonitor = ConfidenceMonitor(models, accountId=accountId, loop=False, logger=logger)
  confidenceMonitor.setListener(confidenceListener)
  
  positionListener = PositionListener(models, Player=createPositionsPlayer,
                                      accountId=accountId,
                                      logger=logger)
  positionMonitor = PositionMonitor(models, accountId=accountId,
                                    loop=False, logger=logger)
  positionMonitor.setListener(positionListener)
  
  confidenceMonitor.start()
  positionMonitor.start()

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
