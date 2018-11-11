# -*- coding: utf-8 -*-

import os
import logging

# BitFlyer設定
BITFLYER_USER_SECRET = None
BITFLYER_ACCESS_KEY = None
BITFLYER_PRICE_TICK_SIZE = 0.1

# Quoine設定
QUOINE_USER_ID = None # (= Token ID)
QUOINE_USER_SECRET = None
QUOINE_TICK_SIZE = 0.1

# MongoDB設定
MONGO_HOST = 'localhost'
MONGO_PORT = 27017

# リセット設定
N_RESET_FOR = 1

# 処理失敗時動作
ACTION_ON_OPENING = 'Exit'
ACTION_ON_CLOSING = 'Exit'
ACTION_ON_RESETTING = 'Exit'

# ログファイル設定
LOG_FILE_PATH = "../logs/Trader.log"
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'

TICKER_LOG_FILE_PATH = "../logs/Ticker.log"

# メール設定
MAIL_HOST = None
MAIL_FROM = None
MAIL_TO = None
MAIL_SUBJECT = None

LOGGER_LEVEL_STREAM = logging.DEBUG
LOGGER_LEVEL_FILE = logging.DEBUG
LOGGER_LEVEL_SLACK = None
LOGGER_LEVEL_MAIL = None

TICKER_LOGGER_LEVEL_STREAM = None
TICKER_LOGGER_LEVEL_FILE = logging.INFO
TICKER_LOGGER_LEVEL_SLACK = None
TICKER_LOGGER_LEVEL_MAIL = None

# Slack WebHook設定
SLACK_WEBHOOK_URL = None
SLACK_USERNAME = None

logging.getLogger('requests').setLevel(logging.ERROR)
formatter = logging.Formatter(LOG_FORMAT)

def getLogger(cwd):
    """
    Returns toplevel logger object.
    A logger supports
    - `debug`,
    - `info`,
    - `warn`,
    - `error` and
    - `critical'.
    """
    logger = get_base_logger()

    stream_handler = get_stream_handler(LOGGER_LEVEL_STREAM)
    if stream_handler is not None:
      logger.addHandler(stream_handler)

    logfile = os.path.join(cwd, LOG_FILE_PATH)
    file_handler = get_file_handler(logfile, LOGGER_LEVEL_FILE)
    if file_handler is not None:
      logger.addHandler(file_handler)

    if LOGGER_LEVEL_MAIL is not None:
      from logging.handlers import SMTPHandler
      smtp_handler = SMTPHandler(MAIL_HOST, MAIL_FROM, MAIL_TO, MAIL_SUBJECT)
      smtp_handler.setLevel(LOGGER_LEVEL_MAIL)
      smtp_handler.setFormatter(formatter)
      logger.addHandler(smtp_handler)

    if LOGGER_LEVEL_SLACK is not None:
      slack_handler = get_slack_handler()
      slack_handler.setLevel(LOGGER_LEVEL_SLACK)
      slack_handler.setFormatter(formatter)
      logger.addHandler(slack_handler)

    return logger


def getTickerLogger(cwd):
    """
    Returns toplevel logger object.
    A logger supports
    - `debug`,
    - `info`,
    - `warn`,
    - `error` and
    - `critical'.
    """
    logger = get_base_logger()

    stream_handler = get_stream_handler(TICKER_LOGGER_LEVEL_STREAM)
    if stream_handler is not None:
      logger.addHandler(stream_handler)

    logfile = os.path.join(cwd, TICKER_LOG_FILE_PATH)
    file_handler = get_file_handler(logfile, TICKER_LOGGER_LEVEL_FILE)
    if file_handler is not None:
      logger.addHandler(file_handler)

    if TICKER_LOGGER_LEVEL_SLACK is not None:
      slack_handler = get_slack_handler()
      slack_handler.setLevel(TICKER_LOGGER_LEVEL_SLACK)
      slack_handler.setFormatter(formatter)
      logger.addHandler(slack_handler)

    return logger

def get_base_logger():
  logger = logging.getLogger()
  logger.setLevel(logging.DEBUG)
  return logger

def get_stream_handler(level):
  if level is None:
    return None
  stream_handler = logging.StreamHandler()
  stream_handler.setLevel(level)
  stream_handler.setFormatter(formatter)
  return stream_handler

def get_file_handler(logfile, level):
  from logging.handlers import RotatingFileHandler
  if level is None:
    return None
  
  mkdir(logfile)
  file_handler = RotatingFileHandler(filename=logfile,
                                     maxBytes=1024 * 1024,
                                     backupCount=9)
  file_handler.setLevel(level)
  file_handler.setFormatter(formatter)
  return file_handler
  
def get_slack_handler():
  from slack_log_handler import SlackLogHandler
  slack_handler = SlackLogHandler(SLACK_WEBHOOK_URL,
                                  username=SLACK_USERNAME)
  return slack_handler

def mkdir(logfile):
  from pathlib import Path
  dirname = os.path.dirname(logfile)
  path = Path(dirname)
  path.mkdir(parents=True, exist_ok=True)
