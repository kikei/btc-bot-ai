import logging

import datetime
import dateutil.parser
import json
import jwt
import os
import sys
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
        self.logger.debug("Quoine.__init__処理開始")

        now = datetime.datetime.now()
        self.starttime = time.mktime(now.timetuple())

        # For Authentication
        self.user_id = user_id
        self.user_secret = user_secret
        
        self.logger.debug("Quoine.__init__処理完了")

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
        self.logger.debug('Quoine API 実行開始, retry={}/{}, path={}'
                          .format(c + 1, RETRY_API_CALL, path))
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
      self.logger.debug("Quoine Tick取得開始")
      try:
        board = self.call_json_api('GET', API_PATH_BOARD)
      except QuoineAPIError as e:
        self.logger.warn('Quoine Tick取得失敗, APIエラー')
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
            
      self.logger.debug('Quoine Tick取得完了, ask={}, bid={}'
                        .format(price_ask, price_bid))
      return OneTick(price_ask, price_bid)
            
    def get_balance(self):
      """
      Get balance.

      Refer:
      [Get all Account Balances](https://developers.quoine.com/#get-all-account-balances)
      """
      self.logger.debug('Quoine Balance取得開始')
      try:
        balances = self.call_json_api('GET', API_PATH_BALANCE)
      except QuoineAPIError as e:
        self.logger.warn('Quoine Balance取得失敗, APIエラー')
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
        self.logger.warn('Quoine Balance取得失敗, JPY={}, BTC={}'
                         .format(jpy, btc))
        return None
      self.logger.info('Quoine Balance取得完了, JPY={:.1f}, BTC={:.1f}'
                       .format(jpy, btc))
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
      self.logger.debug('Quoine Trading Account情報取得開始')
      try:
        accs = self.call_json_api('GET', API_PATH_ACCOUNT)
      except QuoineAPIError as e:
        self.logger.warn('Quoine Trading Account情報取得失敗, APIエラー')
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
          self.logger.info('Quoine Trading Account情報取得完了, account={}'
                           .format(acc))
          return acc
      self.logger.debug('Quoine Trading Account取得失敗, product_id該当無し')
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
      self.logger.info('Quoine order list 取得開始')
      try:
        orders = self.call_json_api('GET', API_PATH_LIST_ORDERS)
      except QuoineAPIError as e:
        self.logger.warn('Quoine order list 取得失敗, APIエラー')
        return None
      models = orders[ORDER_MODELS]
      self.logger.info('Quoine order list 取得完了, orders={}'.format(models))
      return models

    def get_executions(self):
      self.logger.warn('Quoine executions 取得開始')
      try:
        executions = self.call_json_api('GET', API_PATH_EXECUTIONS)
      except QuoineAPIError as e:
        self.logger.warn('Quoine executions 取得失敗, APIエラー')
        return None
      self.logger.warn('Quoine executions 取得成功, excutions={}'
                       .format(executions))
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
        
      self.logger.info('Quoine trades 取得開始')
      try:
        trades = self.call_json_api('GET', path)
      except QuoineAPIError as e:
        self.logger.error('Quoine trades 取得失敗, APIエラー')
        return None
      models = trades['models']
      self.logger.info('Quoine trades 取得完了, trades={}'
                       .format(models))
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
      self.logger.info('Quoine オーダー開始, data={}'.format(data))
      try:
        result = self.call_json_api('POST', API_PATH_ORDERS, data)
      except QuoineAPIError as e:
        self.logger.info('Quoine オーダー失敗, e={}'.format(e))
        return None
      self.logger.info('Quoine オーダー完了, result={}'.format(result))
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
          self.logger.info('Quoine オーダー執行待ち retry={}/{}, #orders={}'
                           .format(c, ORDER_EXECUTED_RETRY,len(orders)))
          continue
        self.logger.info('Quoine オーダーは執行されました')
        return True
      self.logger.info('Quoine オーダーは執行されませんでした, retry={}/{}'
                       .format(c, ORDER_EXECUTED_RETRY))
      return False

    def get_last_order(self, starttime):
      for c in range(0, ORDER_EXECUTED_RETRY):
        time.sleep(ORDER_EXECUTED_RETRY_INTERVAL)
        trades = self.get_trades()
        if trades is None:
          self.logger.info('Quoine オーダー結果取得待ち retry={}/{}'
                           .format(c, ORDER_EXECUTED_RETRY))
          continue
        trades = self.filter_closed(trades, starttime)
        self.logger.debug('Quoine trades={}'.format(trades))
        if len(trades) == 0:
          self.logger.info('Quoine オーダー結果取得待ち retry={}/{}, #orders={}'
                           .format(c, ORDER_EXECUTED_RETRY,len(trades)))
          continue
        self.logger.info('Quoine オーダー結果取得されました')
        sizes = [float(e['quantity']) for e in trades]
        prices = [float(e['open_price']) for e in trades]
        ids = [e['id'] for e in trades]
        position = OnePosition(sizes, prices, ids, trades[0]['side'])
        return position
      self.logger.error('Quoine オーダー結果取得に失敗しました')
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
      self.logger.debug(('Quoine オープンオーダー開始, ' +
                         'side={}, price={}, size={}'
                         .format(side, price,size)))
      now = datetime.datetime.now()
      starttime = time.mktime(now.timetuple())
      self.create_order(side, price, size)
      executed = self.wait_last_order_executed()
      if not executed:
        self.logger.warn('Quoine オーダーは執行されませんでした')
        if not ORDER_IGNORE_TIMEOUT:
          self.logger.info('Quoineオーダーは執行されたとみなし処理を続行')
        else:
          self.logger.warn('Quoineの発注処理に失敗しました')
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
      self.logger.debug("Quoine 決済処理開始, targets={}".format(position))

      closed_ids = []
      for position_id in position.ids:
        path = API_PATH_TRADE_CLOSE.format(id=position_id)
        try:
          closeqn = self.call_api('POST', path)
        except QuoineAPIError as e:
          self.logger.warn('Quoine 決済処理失敗, id={}, e={}'
                           .format(position_id, e))
          continue
        closed_ids.append(position_id)
      
      for position_id in closed_ids:
        # 該当する取引IDの取引が`close`になっていない場合エラー
        try:
          trade = self.get_trade_by_id(position_id)
        except QuoineAPIError as e:
          self.logger.warn("Quoine 決済処理失敗, e={}".format(e))
          continue
          
        if trade is not None and trade['status'] == 'closed':
          self.logger.info("Quoine 決済処理が正常に完了しました。")
        else:
          self.logger.error("Quoine 決済処理エラーかもしれません, " +
                            "手動で建て玉の解消をしてください, " +
                            "id={}, trade={}"
                            .format(position_id, trade))
      return True
