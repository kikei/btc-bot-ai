import logging

import datetime
import json
import jwt
import time
import requests

from classes import Tick, OneTick, Balance, OnePosition

from .QuoineConstants import *
import market.MarketConstants as Const

class QuoineAPIError(RuntimeError):
  pass

class Quoine(object):
    """
    Quoine Exchange API

    # Reference
    [Quoine Exchange API v2 Reference](https://developers.quoine.com/#introduction)
    [Quoine Exchange API Reference](https://developers.quoine.com/v1.html#introduction)
    """
    
    def __init__(self, user_id, user_secret, logger=None):
        if logger is None:
            logger = logging.getLogger()
        self.logger = logger
        self.name = Tick.Quoine
        now = datetime.datetime.now()
        self.starttime = time.mktime(now.timetuple())
        # For Authentication
        self.user_id = user_id
        self.user_secret = user_secret

    # def get_default_tick(self):
    #     return self.tick_default_return_value.copy()

    def get_headers(self, path, token_id, secret):
        nonce = int(datetime.datetime.now().timestamp() * 1000)
        auth = {
            'path': path,
            'nonce': nonce,
            'token_id': token_id
        }
        signature = jwt.encode(auth, secret, algorithm='HS256')
        return {
            'X-Quoine-API-Version': '2',
            'X-Quoine-Auth': signature,
            'Content-Type': 'application/json',
            'User-Agent': API_USER_AGENT
        }
        return headers

    def call_api(self, method, path, data=None):
      for c in range(0, RETRY_API_CALL):
        self.logger.debug(('Calling Quoine API, ' +
                           'retry={count}/{retry}, path={path}')
                          .format(count=c + 1, retry=RETRY_API_CALL, path=path))
        uri = API_URI + path
        headers = self.get_headers(path, self.user_id, self.user_secret)
        try:
          if method == 'GET':
            res = requests.get(uri, headers=headers)
          elif method == 'POST':
            res = requests.post(uri, data=data, headers=headers)
          elif method == 'PUT':
            res = requests.put(uri, data=data, headers=headers)
          else:
            body = json.dumps(json.loads(data))
            res = requests.post(uri, data=body, headers=headers)
        except ValueError as e:
          self.logger.error('ValueError occured during calling Quoine API, e={}'
                            .format(e))
          raise QuoineAPIError('path={}'.format(path))
        except requests.RequestException as e:
          self.logger.error(('RequestException occured ' +
                             'during calling Quoine API, e={}').format(e))
          raise QuoineAPIError('path={}'.format(path))
        
        if res.status_code == requests.codes.ok: # 200
          return res.text
        errors = [
          requests.codes.bad_request, # 400
          requests.codes.unauthorized, # 401
          requests.codes.unprocessable_entity, # 422
          requests.codes.too_many_requests # 429
        ]
        if res.status_code in errors: 
          self.logger.error(('Quoine API error, ' +
                             'you may need to do some solution, ' +
                             'code={}, text={}')
                            .format(res.status_code, res.text))
          raise QuoineAPIError('api returns bad error, path={}'.format(path))
        self.logger.info('Quoine API error, code={}, text={}'
                         .format(res.status_code, res.text))
        time.sleep(1)
      self.logger.warn('Gave up calling Quoine API, retried {} times, path={}'
                       .format(RETRY_API_CALL, path))
      raise QuoineAPIError('api returns error, path={}'.format(path))

    def call_json_api(self, method, path, data=None):
      text = self.call_api(method, path, data)
      try:
        res = json.loads(text)
        return res
      except json.JSONDecodeError as e:
        raise QuoineAPIError('api response parse error, path={}'.format(path))
            
    def get_tick(self):
      self.logger.debug("Fetching Quoine tick.")
      try:
        board = self.call_json_api('GET', API_PATH_BOARD)
      except QuoineAPIError as e:
        self.logger.warn('Failed to fetch Quoine tick, API error={e}'
                         .format(e=e))
        return None
      ask_levels = board[BOARD_SIDE_ASK]
      bid_levels = board[BOARD_SIDE_BID]
      price_ask = None
      price_bid = None
      
      sum = 0
      for price, amount in ask_levels:
        sum = sum + float(amount)
        if sum >= PRICE_TICK_SIZE:
          price_ask = price
          break
      if price_ask is None:
        price_ask, amount = ask_levels[-1]
            
      sum = 0
      for price, amount in bid_levels:
        sum = sum + float(amount)
        if sum >= PRICE_TICK_SIZE:
          price_bid = price
          break
      if price_bid is None:
        price_bid, amount = bid_levels[-1]
            
      self.logger.debug('Completed fetching Quoine tick, ask={ask}, bid={bid}'
                        .format(ask=price_ask, bid=price_bid))
      return OneTick(price_ask, price_bid)
            
    def get_balance(self):
      """
      Get balance.

      Refer:
      [Get all Account Balances](https://developers.quoine.com/#get-all-account-balances)
      """
      self.logger.debug('Fetching Quoine balance information.')
      try:
        balances = self.call_json_api('GET', API_PATH_BALANCE)
      except QuoineAPIError as e:
        self.logger.warn('Failed to fetch Quoine balance information, e={e}.'
                         .format(e=e))
        return None
      jpy = None
      btc = None
      for b in balances:
        currency_code = b[BALANCE_CURRENCY]
        if currency_code == BALANCE_CURRENCY_0:
          jpy = float(b[BALANCE_VALUE])
        elif currency_code == BALANCE_CURRENCY_1:
          btc = float(b[BALANCE_VALUE])
      if jpy is None or btc is None:
        self.logger.warn(('Failed to fetch Quoine balance information, ' +
                          'JPY={jpy}, BTC={btc}.')
                         .format(jpy=jpy, btc=btc))
        return None
      self.logger.info(('Completed fetcing Quoine balance information, ' +
                        'JPY={jpy:.1f}, BTC={btc:.1f}.')
                       .format(jpy=jpy, btc=btc))
      return Balance(jpy=jpy, btc=btc)

    def get_account(self, product_id=5):
      """
      {
        'position': '4.3',              # 合計ポジション数 [BTC]
        'free_margin': '536836.48475',  # 有効証拠金 [JPY]
        'trader_id': 23160,
        'currency_pair_code': 'BTCJPY',
        'created_at': 1479572413,
        'funding_currency': 'JPY',
        'pnl': '17061.92',              # 評価損益 [JPY]
        'max_leverage_level': 2,
        'status': 'active',
        'equity': '634234.55281',       # 純資産
        'id': 67914,
        'pusher_channel': 'trading_account_67914',
        'current_leverage_level': 2,
        'leverage_level': 2,
        'product_id': 5,
        'product_code': 'CASH',
        'updated_at': 1479572413,
        'balance': '617172.63281',      # 残高
        'margin_percent': '0.1',
        'margin': '97398.06806'         # 使用中証拠金
      }
      """
      self.logger.debug('Fetching Quoine account information.')
      try:
        accs = self.call_json_api('GET', API_PATH_ACCOUNT)
      except QuoineAPIError as e:
        self.logger.warn(('Failed to fetch Quoine account information. ' +
                          'API error={e}.')
                         .format(e=e))
        return None
      for acc in accs:
        if acc[ACCOUNT_PRODUCT_ID] == product_id:
          acc[ACCOUNT_EQUITY] = float(acc[ACCOUNT_EQUITY])
          acc[ACCOUNT_FREE_MARGIN] = float(acc[ACCOUNT_FREE_MARGIN])
          acc[ACCOUNT_MARGIN] = float(acc[ACCOUNT_MARGIN])
          # 証拠金維持率
          if acc[ACCOUNT_MARGIN] == 0.0:
            keeprate = 0.0
          else:
            keeprate = acc[ACCOUNT_EQUITY] / acc[ACCOUNT_MARGIN]
          acc[ACCOUNT_KEEPRATE] = 100.0 * keeprate
          self.logger.info(('Completed fetching Quoine account information, ' +
                            'account={a}')
                           .format(a=acc))
          return acc
      self.logger.debug('Failed to fetch Quoine account information, ' +
                        'no product_id')
      return None

    def get_net_asset(self):
      account = self.get_account()
      return account[ACCOUNT_EQUITY]
    
    def get_orders(self):
      """
      Get orders list.

      Refer:
      [3.4. List Orders](https://developers.quoine.com/v1.html#3.4.-list-orders)
      """
      self.logger.info('Fetching order list of Quoine.')
      try:
        orders = self.call_json_api('GET', API_PATH_LIST_ORDERS)
      except QuoineAPIError as e:
        self.logger.warn('Failed to fetch order list of Quoine, API error={e}.'
                         .format(e=e))
        return None
      models = orders[ORDER_MODELS]
      self.logger.info('Completed fetching order list of Quoine, orders={o}.'
                       .format(o=models))
      return models

    def get_executions(self):
      self.logger.warn('Fetching Quoine executions.')
      try:
        executions = self.call_json_api('GET', API_PATH_EXECUTIONS)
      except QuoineAPIError as e:
        self.logger.warn('Failed to fetch Quoine executions, API error={e}.'
                         .format(e=e))
        return None
      self.logger.warn('Completed to fetch Quoine executions, excutions={e}'
                       .format(e=executions))
      return executions

    def get_trades(self, limit=100, status=None):
      """
      Get trades list.

      API response is like

      ```
      {
        "models": [
          {
            "id": "3906",
            "currency_pair_code": "BTCUSD",
            "status": "open",
            "side": "long",
            "margin_used": 2335.7376002,
            "quantity": 0.1,
            "leverage_level": 2,
            "product_code": "CASH",
            "open_price": 403.31,
            "close_price": 0,
            "trader_id": 4807,
            "pnl": 157,
            "stop_loss": 0,
            "take_profit": 0,
            "funding_currency": "JPY",
            "created_at": 1455607142,
            "updated_at": 1456285826
          }
        ],
        "current_page": 1,
        "total_pages": 1
      }
      ```

      Refer
      [9.1. List Trades](https://developers.quoine.com/v1.html#9.1.-list-trades)
      """
      params = []

      if limit is not None:
        params.append('limit={}'.format(limit))
        
      if status is not None:
        params.append('status={}'.format(status))

      path = API_PATH_TRADES
      if len(params) > 0:
        path = '{}?{}'.format(path, '&'.join(params))
        
      self.logger.info('Fetching Quoine trades.')
      try:
        trades = self.call_json_api('GET', path)
      except QuoineAPIError as e:
        self.logger.error('Failed to fetch Quoine trades, API error={e}.'
                          .format(e=e))
        return None
      models = trades['models']
      self.logger.info('Completed fetching Quoine trades, trades={t}.'
                       .format(t=models))
      return models

    def get_trade_by_id(self, order_id):
      trades = self.get_trades()
      if trades is not None:
        for trade in trades:
          if trade['id'] == order_id:
            return trade
      return None

    def filter_closed(self, trades, starttime=None):
      """
      Returns closed trades.
      """
      results = []
      for p in trades:
        if p['status'] != 'closed':
          open_date = p['created_at']
          self.logger.info("filter_closed, open_date:{}, starttime:{}"
                           .format(open_date, starttime))
          if starttime <= open_date + TIME_ERROR_ALLOW:
            results.append(p)
      return results

    def create_order(self, side, price, size):
      """
      Create an Order.

      Refer:
      [3.1. Create an Order](https://developers.quoine.com/v1.html#3.-orders)
      """
      if side == Const.LONG:
        order_side = ORDER_SIDE_BUY
      elif side == Const.SHORT:
        order_side = ORDER_SIDE_SELL
      else:
        raise QuoineAPIError('side must be {} or {}.'
                             .format(Const.LONG, Const.SHORT))
      
      order = {
        'order_type': ORDER_TYPE,
        'product_id': ORDER_PRODUCT_ID,
        'side': order_side,
        'quantity': size,
        'price': price,
        'leverage_level': ORDER_LEVELAGE_LEVEL,
        'funding_currency': ORDER_FUNDING_CURRENCY
      }
      data = json.dumps({'order': order})
      self.logger.info('Requesting order for Quoine, data={d}.'.format(d=data))
      try:
        result = self.call_json_api('POST', API_PATH_ORDERS, data)
      except QuoineAPIError as e:
        self.logger.info('Failed to request order for Quoine, API error={e}.'
                         .format(e=e))
        return None
      self.logger.info('Completed to request order for Quoine, result={r}.'
                       .format(r=result))
      return result

    def wait_last_order_executed(self):
      """
      直前のオーダーが執行されるまでブロックする。
      執行されたらすぐに True を返す。
      """
      for c in range(0, ORDER_EXECUTED_RETRY):
        time.sleep(ORDER_EXECUTED_RETRY_INTERVAL)
        orders = self.get_orders()
        if orders is not None and len(orders) > 0:
          self.logger.info(('Waiting order executed in Quoine, ' +
                            'retry={c}/{r}, #orders={n}.')
                           .format(c=c, r=ORDER_EXECUTED_RETRY, n=len(orders)))
          continue
        self.logger.info('Order for Quoine executed.')
        return True
      self.logger.info('Failed to execute order in Quoine, retry={c}/{r}.'
                       .format(c=c, r=ORDER_EXECUTED_RETRY))
      return False

    def get_last_order(self, starttime):
      for c in range(0, ORDER_EXECUTED_RETRY):
        time.sleep(ORDER_EXECUTED_RETRY_INTERVAL)
        trades = self.get_trades()
        if trades is None:
          self.logger.info(('Waiting result of the last order for Quoine, ' +
                            'retry={c}/{r}.')
                           .format(c=c, r=ORDER_EXECUTED_RETRY))
          continue
        trades = self.filter_closed(trades, starttime)
        self.logger.debug('Fetched trades for Quoine trades={t}.'
                          .format(t=trades))
        if len(trades) == 0:
          self.logger.info(('Waiting result of the last order for Quoine, ' +
                            'retry={c}/{r}, #orders={n}.')
                           .format(c=c, r=ORDER_EXECUTED_RETRY, n=len(trades)))
          continue
        self.logger.info('Completed to fetch result of the order for Quoine.')
        sizes = [float(e['quantity']) for e in trades]
        prices = [float(e['open_price']) for e in trades]
        ids = [e['id'] for e in trades]
        position = OnePosition(sizes, prices, ids, trades[0]['side'])
        return position
      self.logger.error('Failed to fetch result of the last order for Quoine.')
      return None
        
    def open_position(self, side, price, size):
      """
      Returns executions list.

      (
        side: string,
        price: float,
        size: float
      ) -> {
        sizes  : [float],
        prices : [float],
        ids    : [int]
      }
      """
      self.logger.debug(('Fetching open orders for Quoine, ' +
                         'side={s}, price={p}, size={z}.')
                         .format(s=side, p=price, z=size))
      now = datetime.datetime.now()
      starttime = time.mktime(now.timetuple())
      self.create_order(side, price, size)
      executed = self.wait_last_order_executed()
      if not executed:
        self.logger.warn('The last order for Quoine was not executed.')
        if not ORDER_IGNORE_TIMEOUT:
          self.logger.info('The last order might fail, but we continue task.')
        else:
          self.logger.warn('Failed to order for Quoine.')
          return None
      position = self.get_last_order(starttime)
      return position

    def close_position(self, position):
      """
      Close positions.

      ( position: OnePosition ) -> bool

      Refer:
      [Close a trade](https://developers.quoine.com/#close-a-trade)
      """
      self.logger.debug("Closing position on Quoine, positions={p}."
                        .format(p=position))

      closed_ids = []
      for position_id in position.ids:
        path = API_PATH_TRADE_CLOSE.format(id=position_id)
        try:
          closeqn = self.call_api('POST', path)
        except QuoineAPIError as e:
          self.logger.warn('Failed to close position on Quoine, id={id}, e={e}.'
                           .format(id=position_id, e=e))
          continue
        closed_ids.append(position_id)
      
      for position_id in closed_ids:
        # 該当する取引IDの取引が`close`になっていない場合エラー
        try:
          trade = self.get_trade_by_id(position_id)
        except QuoineAPIError as e:
          self.logger.warn('Failed to close position on Quoine, API error={e}.'
                           .format(e=e))
          continue
          
        if trade is not None and trade['status'] == 'closed':
          self.logger.info('Completed to close position on Quoine.')
        else:
          self.logger.error(('It might failed to close position on Quoine, ' +
                             'close it manually if you need.' + 
                             'id={id}, trade={t}.')
                            .format(id=position_id, t=trade))
      return True
