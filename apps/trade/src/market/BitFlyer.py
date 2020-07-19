import logging

import base64
import datetime
import dateutil.parser
import hashlib
import hmac
import json
import os
import sys
import time
import requests

from classes import Tick, OneTick, Balance, OnePosition
from .BitFlyerConstants import *
import market.MarketConstants as Const

class BitFlyerAPIError(RuntimeError):
  pass

class BitFlyer(object):
  """
  BitFlyer Lightning API
    
  # Reference
  - [API Documentation](https://lightning.bitflyer.jp/docs?lang=ja)

  # Limitation
  > HTTP API は、以下のとおり呼び出し回数を制限いたします。
  > - Private API は 1 分間に約 200 回を上限とします。
  > - IP アドレスごとに 1 分間に約 500 回を上限とします。
  """

  def __init__(self, user_secret, access_key, logger=None):
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    self.name = Tick.BitFlyer
    now = datetime.datetime.now()
    self.starttime = time.mktime(now.timetuple())
    self.user_secret = user_secret
    self.access_key = access_key

  def get_nonce(self):
    return str(int(time.time() * 1000))

  def get_signature(self, nonce, method, path, body):
    msg = str(nonce) + method + path + body
    hmac0 = hmac.new(self.user_secret.encode('utf-8'),
                     msg.encode('utf-8'),
                     hashlib.sha256)
    signature = hmac0.hexdigest()
    return signature

  def get_headers(self, nonce, signature):
    headers = {}
    headers['Content-Type'] = API_CONTENT_TYPE
    headers['User-Agent'] = API_USER_AGENT
    headers['ACCESS-KEY'] = self.access_key
    headers['ACCESS-TIMESTAMP'] = nonce
    headers['ACCESS-SIGN'] = signature
    return headers

  def call_api(self, method, path, data=None):
    for c in range(0, RETRY_API_CALL):
      self.logger.debug(('Calling BitFlyer API, ' +
                         'retry={count}/{retry}, path={path}.')
                        .format(count=c + 1, retry=RETRY_API_CALL, path=path))
      uri = API_URI + path
      if data is not None:
        body = json.dumps(json.loads(data))
      else:
        body = ""
      nonce = self.get_nonce()
      signature = self.get_signature(nonce, method, path, body)
      headers = self.get_headers(nonce, signature)

      try:
        if method == 'GET':
          res = requests.get(uri, headers=headers)
        else:
          body = json.dumps(json.loads(data))
          res = requests.post(uri, data=body, headers=headers)
      except ValueError as e:
        self.logger.error(('ValueError occured during calling BitFlyer API, ' +
                          'e={e}').format(e=e))
        raise BitFlyerAPIError('path={path}'.format(path=path))
      except requests.RequestException as e:
        self.logger.error(('RequestException occured ' +
                           'during calling BitFlyer API, e={e}').format(e=e))
        raise BitFlyerAPIError('path={path}'.format(path=path))
      if res is not None and res.status_code == requests.codes.ok:
        return res.text
      self.logger.info('BitFlyer API error, code={code}, text={text}'
                       .format(code=res.status_code, text=res.text))
      if res is not None and res.status_code == requests.codes.bad_request:
        break
      time.sleep(1)
    self.logger.warning(('Gave up calling BitFlyer API, ' +
                         'retried {count} times, path={path}')
                        .format(count=RETRY_API_CALL, path=path))
    raise BitFlyerAPIError('api returns error, path={path}'.format(path=path))

  def call_json_api(self, method, path, data=None):
    text = self.call_api(method, path, data)
    try:
      res = json.loads(text)
      return res
    except json.JSONDecodeError as e:
      raise BitFlyerAPIError('api response parse error, path={}'.format(path))
    
  def get_tick(self, code='FX_BTC_JPY'):
    self.logger.debug('Fetching BitFlyer tick.')
    try:
      path = API_PATH_BOARD.format(product_code=code)
      board = self.call_json_api('GET', path)
    except BitFlyerAPIError as e:
      self.logger.warning('Failed to fetch BitFlyer tick, API error={e}'
                          .format(e=e))
      return None
    ask_levels = board[BOARD_SIDE_ASK]
    bid_levels = board[BOARD_SIDE_BID]
    self.logger.debug('#asks={asks}, #bids={bids}'
                      .format(asks=len(ask_levels), bids=len(bid_levels)))
    price_ask = None
    price_bid = None
        
    sum = 0
    for v in ask_levels:
      sum = sum + float(v[BOARD_SIZE])
      if sum >= PRICE_TICK_SIZE:
        price_ask = v[BOARD_PRICE]
        break
    if price_ask is None:
      price_ask = ask_levels[-1][BOARD_PRICE]

    sum = 0
    for v in bid_levels:
      sum = sum + float(v[BOARD_SIZE])
      if sum >= PRICE_TICK_SIZE:
        price_bid = v[BOARD_PRICE]
        break
    if price_bid is None:
      price_bid = ask_levels[-1][BORAD_PRICE]

    self.logger.debug('Completed fetching BitFlyer tick, ask={ask}, bid={bid}.'
                      .format(ask=price_ask, bid=price_bid))
    return OneTick(price_ask, price_bid)

  def get_balance(self):
    """
    Get balance.

    Refer:
    [資産残高を取得](https://lightning.bitflyer.jp/docs?lang=ja#資産残高を取得)
    """
    self.logger.debug('Fetching BitFlyer balance information.')
    try:
      balances = self.call_json_api('GET', API_PATH_BALANCE)
    except BitFlyerAPIError as e:
      self.logger.warning('Failed to fetch BitFlyer balance information, e={e}.'
                          .format(e=e))
      return None
    jpy = None
    btc = None
    for b in balances:
      currency_code = b[BALANCE_CURRENCY]
      if currency_code == BALANCE_CURRENCY_0:
        jpy = b[BALANCE_VALUE]
      elif currency_code == BALANCE_CURRENCY_1:
        btc = b[BALANCE_VALUE]
    if jpy is None or btc is None:
      self.logger.warning(('Failed to fetch BitFlyer balance information, ' +
                           'JPY={jpy}, BTC={btc}')
                          .format(jpy=jpy, btc=btc))
      return None
    self.logger.warning(('Completed fetching BitFlyer balance information, ' +
                         'JPY={jpy}, BTC={btc}')
                        .format(jpy=jpy, btc=btc))
    return Balance(jpy=jpy, btc=btc)

  def get_collateral(self):
    """
    Get collateral.

    {
      "collateral": 100000,        # 預け入れた証拠金の評価額 [円]
      "open_position_pnl": -715,   # 建玉の評価損益 [円]
      "require_collateral": 19857, # 現在の必要証拠金 [円]
      "keep_rate": 5.000           # 現在の証拠金維持率 [%]
    }

    Refer:
    [証拠金の状態を取得](https://lightning.bitflyer.jp/docs?lang=ja#証拠金の状態を取得)
    """
    self.logger.debug('Fetching BitFlyer collateral information.')
    try:
      coll = self.call_json_api('GET', API_PATH_COLLATERAL)
    except BitFlyerAPIError as e:
      self.logger.warning(('Failed to fetch BitFlyer collateral information, ' +
                           'API error={e}.')
                          .format(e=e))
      return None
    self.logger.debug(('Completed fetching BitFlyer collateral information. ' +
                       'coll={coll}')
                      .format(coll=coll))
    return coll

  def get_positions(self):
    """
    Get positions.
    Refer:
    [建玉の一覧を取得](https://lightning.bitflyer.jp/docs?lang=ja#建玉の一覧を取得)
    """
    self.logger.debug('Fetching positions of BitFlyer')
    try:
      positions = self.call_json_api('GET', API_PATH_POSITIONS)
    except BitFlyerAPIError as e:
      self.logger.warning(('Failed to fetch positions of BitFlyer, ' +
                           'API error={e}.')
                          .format(e=e))
      return None
    self.logger.debug(('Completed to fetch positions of BitFlyer.' +
                       '#positions={positions}')
                      .format(positions=len(positions)))
    return positions

  def get_net_asset(self):
    collateral = self.get_collateral()
    if collateral is None:
      return 0
    return collateral[COLLATERAL_COLLATERAL] + collateral[COLLATERAL_PNL]

  def exec_order(self, side, price, size):
    self.logger.debug(('Requesting order to BitFlyer, ' +
                       'side={side}, price={price}, size={size}')
                      .format(side=side, price=price, size=size))
    now = datetime.datetime.now()
    starttime = time.mktime(now.timetuple())
    if side == Const.LONG:
      side_value = ORDER_SIDE_BUY
    else:
      side_value = ORDER_SIDE_SELL
    values = {
      'product_code': ORDER_PRODUCT_CODE,
      'child_order_type': ORDER_TYPE,
      'side': side_value,
      'size': size,
      'minute_to_expire': ORDER_EXPIRE,
      'time_in_force': ORDER_RULE
    }
    try:
      result = self.call_json_api('POST', API_PATH_ORDER, json.dumps(values))
    except BitFlyerAPIError as e:
      self.logger.error('Failed to request order to BitFlyer, API error={e}'
                        .format(e=e))
      return None
    order_id = result[ORDER_ORDER_ID]
    self.logger.debug(('Completed to request order to BitFlyer, ' +
                       'order_acceptance_id={id}')
                      .format(id=order_id))
    return order_id

  def wait_last_order_executed(self):
    for c in range(0, ORDER_EXECUTED_RETRY):
      time.sleep(ORDER_EXECUTED_RETRY_INTERVAL)
      orders = self.get_orders()
      if orders is not None and len(orders) > 0:
        self.logger.debug(('Waiting order executed in BitFlyer, ' +
                           'retry={count}/{retry}, #orders={orders}.')
                          .format(count=c, retry=ORDER_EXECUTED_RETRY,
                                  orders=len(orders)))
        continue
      self.logger.info('Order in BitFlyer executed.')
      return True
    self.logger.warning(('Failed to execute order in BitFlyer, ' +
                         'retry={count}/{retry}.')
                        .format(count=c, retry=ORDER_EXECUTED_RETRY))
    return False

  def open_position(self, side, price, size):
    """
    Open position.

    Type:
    (
      side: str,
      price: float,
      size: float
    ) -> OnePosition

    Refer:
    [新規注文を出す](https://lightning.bitflyer.jp/docs?lang=ja#新規注文を出す)

    NOTE: The minimum order size is 0.001 BTC.
    """
    if side not in [Const.LONG, Const.SHORT]:
        self.logger.error('BitFlyer API parameter error, side={side}.'
                          .format(side=side))
        return None
    self.logger.debug(('Opening a position in bitFlyer, ' +
                       'side={side}, price={price}, size={size}.')
                      .format(side=side, price=price, size=size))
    now = datetime.datetime.now()
    starttime = time.mktime(now.timetuple())
    order_id = self.exec_order(side, price, size)
    if order_id is None:
       self.logger.warning('Failed to execute order in BitFlyer.')
       return None
    executed = self.wait_last_order_executed()
    if not executed:
      self.logger.warning('Failed to request order in BitFlyer.')
      if not ORDER_IGNORE_TIMEOUT:
        self.logger.info('Failed to request order in BitFlyer; ignored.')
      else:
        self.logger.warning('Failed to request order in BitFlyer; error.')
        return None
    position = self.get_order(starttime, order_id)
    position.side = side
    self.logger.debug('Completed to open a position, position={p}.'
                      .format(p=position))
    return position
      
  def close_position(self, position):
    """
    Close position.

    { position: OnePosition ) -> OnePosition

    Refer:
    [新規注文を出す](https://lightning.bitflyer.jp/docs?lang=ja#新規注文を出す)

    NOTE: The minimum order size is 0.001 BTC.
    """
    side = position.sideReverse()
    size = position.sizeWhole()
    size = round(size,3)
    price = position.amount() / size
    starttime = datetime.datetime.now().timestamp()
    order_id = self.exec_order(side, price, size)
    executed = self.wait_last_order_executed()
    if not executed:
      self.logger.warning('The order in BitFlyer not executed.')
      if not ORDER_IGNORE_TIMEOUT:
        self.logger.info('Continue to execute order in BitFlyer ' +
                         'as last order is assumed to be executed')
      else:
        self.logger.warning('Failed to execute order in BitFlyer.')
        return None
    position = self.get_order(starttime, order_id)
    position.side = side
    self.logger.debug('Completed to close a position, position={p}.'
                      .format(p=position))
    return position

  def get_orders(self):
    """
    Get orders list.

    Refer:
    [注文の一覧を取得](https://lightning.bitflyer.jp/docs/#注文の一覧を取得)
    """
    self.logger.debug('Fetching orders in BitFlyer.')
    try: 
      orders = self.call_json_api('GET', API_PATH_LIST_ORDERS)
    except BitFlyerAPIError as e:
      self.logger.warning(('Failed to fetch orders in BitFlyer, ' +
                           'API error={e}')
                          .format(e=e))
      return None
    self.logger.debug('Completed to fetch orders in BitFlyer, #orders={orders}.'
                     .format(orders=len(orders)))
    return orders


  def get_order(self, starttime, order_id):
    self.logger.debug('Fetching the order in BitFlyer, order_id={id}.'
                      .format(id=order_id))
    for c in range(0, ORDER_EXECUTED_RETRY):
      time.sleep(ORDER_EXECUTED_RETRY_INTERVAL)
      try:
        executions = self.get_executions(order_id)
      except BitFlyerAPIError as e:
        self.logger.debug(('Waiting for the order in BitFlyer fetched, ' +
                           'retry={count}/{retry}')
                          .format(count=c, retry=ORDER_EXECUTED_RETRY))
        continue
      if len(executions) == 0 or \
         not self.is_all_executed(executions, starttime):
        self.logger.debug(('Waiting for the order\'s result in BitFlyer, ' +
                           'retry={count}/{retry}, #orders={orders}.')
                          .format(count=c, retry=ORDER_EXECUTED_RETRY,
                                  orders=len(executions)))
        continue
      sizes = [float(e['size']) for e in executions]
      prices = [float(e['price']) for e in executions]
      position = OnePosition(self.name, sizes, prices, None)
      return position
    self.logger.debug(('Failed to fetch the order result in BitFlyer, ' +
                       'order_id={id}')
                      .format(id=order_id))
    return None
    

  def get_executions(self, order_parent_id=None, count=100):
      """
      Get all executions.

      Refer:
      [約定の一覧を取得](https://lightning.bitflyer.jp/docs/#約定の一覧を取得)
      """
      path = '/v1/me/getexecutions'
      queries = [
          'product_code=FX_BTC_JPY',
          'count={count}'.format(count=count)
      ]
      if order_parent_id is not None:
          queries.append('child_order_acceptance_id={parent_id}'
                         .format(parent_id=order_parent_id))
      path = '{p}?{q}'.format(p=path, q='&'.join(queries))
      listbf = self.call_json_api('GET', path)
      return listbf

  def is_all_executed(self, executions, starttime):
    """
    Returns True when all executions done.
    """
    TIME_ERROR_ALLOW = 3
      
    for e in executions:
      retry_flg = 0
      # UTC
      open_date = e[EXECUTION_DATE]
      open_date = dateutil.parser.parse(open_date)
      # UTC+09:00
      open_date += datetime.timedelta(hours=9)
      pass_time = time.mktime(open_date.timetuple())
      self.logger.info("passtime:{}, starttime:{}"
                       .format(pass_time, starttime))
      if pass_time < starttime - TIME_ERROR_ALLOW:
        return False
    return True

  def is_busy(self):
    """
    Returns True when exchange is surper busy state.
    """
    health = self.call_json_api('GET', API_PATH_HEALTH)
    if not health['status'] in ['NORMAL', 'BUSY', 'VERY BUSY']:
      return True
    return False
