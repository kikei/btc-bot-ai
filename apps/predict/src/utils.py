import configparser
import datetime
import numpy as np
import os
import logging
import pymongo

from classes import Confidence
from dashboard.Dashboard import Dashboard

def mkdir(logfile):
  from pathlib import Path
  dirname = os.path.dirname(logfile)
  path = Path(dirname)
  path.mkdir(parents=True, exist_ok=True)

def group(f, lst):
  start = None
  current = []
  for item in lst:
    current.append(item)
    key = f(item)
    if start is None:
      start = key
    elif start != key:
      start = key
      yield start, current
      current = []
  if len(current) > 0:
    yield start, current

def getCWD():
  CWD = os.path.dirname(os.path.abspath(__file__))
  return CWD

def readConfig(path):
  def parseListConfig(t):
    return [a.strip() for a in t.split(',')]
  config = configparser.ConfigParser(converters={'list': parseListConfig})
  config.read(path)
  return config

def getDBInstance(config):
  server = 'mongodb://{user}:{password}@{host}:{port}'
  config = config['database']
  user = config.get('mongo.user')
  password = config.get('mongo.password')
  host = config.get('mongo.host')
  port  = config.getint('mongo.port')
  assert all([user is not None,
              password is not None,
              host is not None,
              port is not None])
  server = server.format(host=host, port=port, user=user, password=password)
  client = pymongo.MongoClient(host=server)
  return client

def loadnpy(config, exchanger, unit, ty, nan=None):
  DIR_DATA = config['train'].get('data.dir')
  NPY_DATA = config['train'].get('data.npy')
  path = (DIR_DATA + '/' + NPY_DATA).format(exchanger=exchanger, unit=unit, ty=ty)
  data = np.load(path)
  if nan is not None:
    data[np.argwhere(np.isnan(data))] = nan
  return data

def savenpy(config, data, exchanger, unit, ty):
  DIR_DATA = config['train'].get('data.dir')
  NPY_DATA = config['train'].get('data.npy')
  path = (DIR_DATA + '/' + NPY_DATA).format(exchanger=exchanger, unit=unit, ty=ty)
  return np.save(path, data)

def nanIn(x):
  nans = np.argwhere(np.isnan(x))
  if len(nans) == 0:
    return None
  else:
    return nans

def getDashboardIf(config, logger=None, login=True):
  AIMAI_DB_URI = config['aimai.db'].get('uri')
  USERNAME = config['aimai.db'].get('username')
  PASSWORD = config['aimai.db'].get('password')
  dashb = Dashboard(uri=AIMAI_DB_URI, logger=logger)
  if login:
    dashb.requestLogin(USERNAME, PASSWORD)
  return dashb

def reportConfidence(config, longConf, shortConf, logger):
  dashb = getDashboardIf(config, logger=logger)
  now = datetime.datetime.now()
  status = Confidence.StatusNew
  dashb.saveConfidence(now, longConf, shortConf, status)

def reportTrend(config, trend, logger):
  dashb = getDashboardIf(config, logger=logger)
  now = datetime.datetime.now()


# ログファイル設定
LOG_FILE_PATH = "../logs/bot.log"
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'

LOGGER_LEVEL_STREAM = logging.DEBUG
LOGGER_LEVEL_FILE = logging.DEBUG
LOGGER_LEVEL_SLACK = logging.WARN

# Slack WebHook設定
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/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'
SLACK_USERNAME = 'fujii'

logging.getLogger('requests').setLevel(logging.ERROR)
formatter = logging.Formatter(LOG_FORMAT)

def getBaseLogger():
  logger = logging.getLogger()
  logger.setLevel(logging.DEBUG)
  return logger

def getStreamHandler(level):
  if level is None:
    return None
  streamHandler = logging.StreamHandler()
  streamHandler.setLevel(level)
  streamHandler.setFormatter(formatter)
  return streamHandler

def getFileHandler(logfile, level):
  from logging.handlers import RotatingFileHandler
  if level is None:
    return None
  mkdir(logfile)
  fileHandler = RotatingFileHandler(filename=logfile,
                                    maxBytes=1024 * 1024,
                                    backupCount=9)
  fileHandler.setLevel(level)
  fileHandler.setFormatter(formatter)
  return fileHandler

def getSlackHandler(level, formatter):
  from slack_log_handler import SlackLogHandler
  if level is None:
    return None
  slackHandler = SlackLogHandler(SLACK_WEBHOOK_URL, username=SLACK_USERNAME)
  slackHandler.setLevel(level)
  slackHandler.setFormatter(formatter)
  return slackHandler

def getLogger(cwd=None):
    """
    Returns toplevel logger object.
    A logger supports
    - `debug`,
    - `info`,
    - `warn`,
    - `error` and
    - `critical'.
    """
    if cwd is None:
      cwd = getCWD()
    logger = getBaseLogger()
    handlers = [
      getStreamHandler(level=LOGGER_LEVEL_STREAM),
      getFileHandler(os.path.join(cwd, LOG_FILE_PATH), level=LOGGER_LEVEL_FILE),
      getSlackHandler(level=LOGGER_LEVEL_SLACK, formatter=formatter)
    ]
    for h in handlers:
      if h is not None: logger.addHandler(h)
    return logger

