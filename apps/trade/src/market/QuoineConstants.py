# -*- coding: utf-8 -*-

# 新規注文後、一定時間経ってもオーダーが残っている場合に
# 処理を続行するか否か
ORDER_IGNORE_TIMEOUT = True

# 注文完了待ち確認間隔
ORDER_EXECUTED_RETRY_INTERVAL = 2

# 注文完了待ち確認回数
ORDER_EXECUTED_RETRY = 40

# クローズ済みトレード取得時の許容時間誤差 [s]
TIME_ERROR_ALLOW = 3

# API呼び出しリトライ数
RETRY_API_CALL = 10

API_URI = 'https://api.liquid.com'
API_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240'

# Path Info
API_PATH_BOARD = '/products/5/price_levels'
API_PATH_TICK = '/products/5'
API_PATH_BALANCE = '/accounts/balance'
API_PATH_ACCOUNT = '/trading_accounts'
API_PATH_LIST_ORDERS = '/orders?currency_pair_code=BTCJPY&status=live&product_code=CASH'
API_PATH_EXECUTIONS = '/executions/me?product_id=5'
API_PATH_ORDERS = '/orders/'
API_PATH_TRADES = '/trades'
API_PATH_TRADE_CLOSE = '/trades/{id}/close'

PRICE_TICK_SIZE = 2.5

BOARD_SIDE_ASK = 'sell_price_levels'
BOARD_SIDE_BID = 'buy_price_levels'

BALANCE_CURRENCY = 'currency'
BALANCE_VALUE = 'balance'
BALANCE_CURRENCY_0 = 'JPY'
BALANCE_CURRENCY_1 = 'BTC'

ACCOUNT_PRODUCT_ID = 'product_id'
ACCOUNT_EQUITY = 'equity'
ACCOUNT_FREE_MARGIN = 'free_margin'
ACCOUNT_MARGIN = 'margin'
ACCOUNT_KEEPRATE = 'keep_rate'

# 成行買い
ORDER_TYPE = 'market'

ORDER_PRODUCT_ID = 5
ORDER_FUNDING_CURRENCY = 'JPY'
ORDER_SIDE_BUY = 'buy'
ORDER_SIDE_SELL = 'sell'
ORDER_LEVELAGE_LEVEL = 10
ORDER_MODELS = 'models'
