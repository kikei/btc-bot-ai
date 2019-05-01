import datetime
import time

from classes import OneTick
from models import Ticks
from utils import getDBInstance, readConfig, getLogger
from dashboard.Dashboard import Dashboard

logger = getLogger()
logger.debug('Start synchronization.')

config = readConfig('predict.ini')
AIMAI_DB_URI = config['aimai.db'].get('uri')
USERNAME = config['aimai.db'].get('username')
PASSWORD = config['aimai.db'].get('password')
SYNC_EXCHANGERS = config['sync'].getlist('exchangers')
SYNC_STEP_SECONDS = config['sync'].getint('step.seconds')
SYNC_INTERVAL_SECONDS = config['sync'].getint('listen.interval.seconds')
SYNC_DATE_START = datetime.datetime(2016, 12, 4)

def sync(dashb, ticksModel):
  finish = datetime.datetime.now().timestamp()
  for exchanger in SYNC_EXCHANGERS:
    latest = ticksModel.one(exchanger)
    if latest is not None:
      dateStart = latest.date
    else:
      dateStart = SYNC_DATE_START
    start = dateStart.timestamp()
    count = 0
    logger.debug('Start from {s} to {e}.'.format(s=start, e=finish))
    while start < finish:
      logger.info('Syncing {ex} after {s}.'
                  .format(ex=exchanger,
                          s=datetime.datetime.fromtimestamp(start).isoformat()))
      res = dashb.requestTicks(exchanger, start)
      ticks = res['ticks'][exchanger]
      if len(ticks) > 0:
        toSave = [OneTick.fromDict(t) for t in ticks]
        logger.debug('Writing {count} items.'.format(count=len(ticks)))
        ticksModel.saveAll(exchanger, toSave)
        start = ticks[-1]['datetime']
        count += len(ticks)
      else:
        start = start + SYNC_STEP_SECONDS
      time.sleep(SYNC_INTERVAL_SECONDS)
    if count == 0:
      logger.error('No ticks synchronized. Ticker may not be working!!')


def main():
  db = getDBInstance(config)
  ticksModel = Ticks(db.tick_db)
  dashb = Dashboard(uri=AIMAI_DB_URI, logger=logger)
  dashb.requestLogin(USERNAME, PASSWORD)
  sync(dashb, ticksModel)


if __name__ == '__main__':
  main()


logger.debug('End synchronization.')
