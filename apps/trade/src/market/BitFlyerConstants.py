# -*- coding: utf-8 -*-

# 新規注文後、一定時間経ってもオーダーが残っている場合に
# 処理を続行するか否か
ORDER_IGNORE_TIMEOUT = False

# API呼び出しリトライ数
RETRY_API_CALL = 30

API_URI = 'https://api.bitflyer.jp'
API_PATH_BOARD = '/v1/getboard?product_code={product_code}'
API_PATH_BALANCE = '/v1/me/getbalance'
API_PATH_COLLATERAL = '/v1/me/getcollateral'
API_PATH_POSITIONS = '/v1/me/getpositions?product_code=FX_BTC_JPY'

API_PATH_ORDER = '/v1/me/sendchildorder'
API_PATH_LIST_ORDERS = '/v1/me/getchildorders?product_code=FX_BTC_JPY&child_order_state=ACTIVE'
API_PATH_HEALTH = '/v1/gethealth?product_code=FX_BTC_JPY'

API_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240'

API_CONTENT_TYPE = 'application/json'

PRICE_TICK_SIZE = 2.5

BOARD_SIDE_ASK = 'asks'
BOARD_SIDE_BID = 'bids'
BOARD_SIZE = 'size'
BOARD_PRICE = 'price'

BALANCE_CURRENCY = 'currency_code'
BALANCE_VALUE = 'available'
BALANCE_CURRENCY_0 = 'JPY'
BALANCE_CURRENCY_1 = 'BTC'

COLLATERAL_COLLATERAL = 'collateral'
COLLATERAL_PNL = 'open_position_pnl'

EXECUTION_DATE = 'exec_date'

ORDER_ORDER_ID = 'child_order_acceptance_id'
ORDER_PRODUCT_CODE = 'FX_BTC_JPY'
ORDER_TYPE = 'MARKET'
ORDER_EXPIRE = 10000
ORDER_RULE = 'GTC'
ORDER_SIDE_BUY = 'BUY'
ORDER_SIDE_SELL = 'SELL'

ORDER_MODELS = 'models'

# 注文完了待ち確認間隔
ORDER_EXECUTED_RETRY_INTERVAL = 2

# 注文完了待ち確認回数
ORDER_EXECUTED_RETRY = 80
