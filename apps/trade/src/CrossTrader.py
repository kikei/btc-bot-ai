import os
import sys
import concurrent.futures

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'config'))

from Markets import Markets
import market.MarketConstants as Const
from classes import Tick

def get_executor():
  executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
  return executor

class CrossTrader(object):
  def __init__(self, logger=None):
    self.logger = logger
    self.markets = Markets(logger)

  def get_tick(self):
    """
    (self: CrossTrader) -> Tick
    """
    bitflyer = self.markets.BitFlyer
    quoine = self.markets.Quoine

    bitflyer.get_tick()

    tick = {}

    def on_bitflyer(future):
      tick[Tick.BitFlyer] = future.result()
    
    def on_quoine(future):
      tick[Tick.Quoine] = future.result()

    fs = [
      (bitflyer.get_tick, on_bitflyer),
      (quoine.get_tick, on_quoine)
    ]
    
    with get_executor() as executor:
      def to_future(fs):
        f, callback = fs
        future = executor.submit(f)
        future.add_done_callback(callback)
        return future
      futures = [to_future(f) for f in fs]
      timeout = 300 # seconds
      try:
        concurrent.futures.wait(futures, timeout=timeout)
      except concurrent.futures.TimeoutError as e:
        self.logger.error(('Tick取得処理がタイムアウトしました, ' +
                           'timeout={}').format(timeout))
    if Tick.BitFlyer not in tick or tick[Tick.BitFlyer] is None:
      self.logger.error('BitFlyerのTick取得に失敗しました')
    if Tick.Quoine not in tick or tick[Tick.Quoine] is None:
      self.logger.error('QuoineのTick取得に失敗しました')
    
    return Tick(tick)
  
  def open_position(self, upper, lower, tick, lot):
    """
    (
      upper: str, lower: str, tick: Tick, lot: float
    ) -> {
      lower: OneTick, upper: OneTick
    }
    """
    f_short = None
    f_long = None
    
    if upper == Tick.BitFlyer:
      f_short = lambda: self.open_bitflyer(Const.SHORT,
                                           tick.exchanger(Tick.BitFlyer).ask,
                                           lot)
    elif upper == Tick.Quoine:
      f_short = lambda: self.open_quoine(Const.SHORT,
                                         tick.exchanger(Tick.Quoine).ask,
                                         lot)

    if lower == Tick.BitFlyer:
      f_long = lambda: self.open_bitflyer(Const.LONG,
                                          tick.exchanger(Tick.BitFlyer).bid,
                                          lot)
    elif lower == Tick.Quoine:
      f_long = lambda: self.open_quoine(Const.LONG,
                                        tick.exchanger(Tick.Quoine).bid,
                                        lot)

    if f_short is None or \
       f_long is None:
      self.logger.error('unknown exchanger, upper={}, lower={}'
                        .format(upper, lower))
      return

    exchangers = {}

    def on_short(future):
      exchangers[upper] = future.result()
      
    def on_long(future):
      exchangers[lower] = future.result()

    fs = [(f_short, on_short), (f_long, on_long)]
    
    with get_executor() as executor:
      def to_future(fs):
        f, callback = fs
        future = executor.submit(f)
        future.add_done_callback(callback)
        return future
      futures = [to_future(f) for f in fs]
      timeout = 300 # seconds
      try:
        concurrent.futures.wait(futures, timeout=timeout)
      except concurrent.futures.TimeoutError as e:
        self.logger.error(('オープン処理がタイムアウトしました, ' +
                           'timeout={}').format(timeout))

    if upper not in exchangers or exchangers[upper] is None:
      self.logger.error(('ショートポジションのオープンに失敗しました, ' +
                         'exchanger={}, lot={}').format(upper, lot))
      return None

    if lower not in exchangers or exchangers[lower] is None:
      self.logger.error(('ロングポジションのオープンに失敗しました, ' +
                         'exchanger={}, lot={}').format(upper, lot))
      return None

    return exchangers

  def close_position(self, position):
    name_short = position.short
    name_long = position.long
    ex_short = position.short_one() # : OnePosition
    ex_long = position.long_one()   # : OnePosition
    
    f_short = None
    f_long = None

    if name_short == Tick.BitFlyer:
      f_short = lambda: self.close_bitflyer(ex_short)
    elif name_short == Tick.Quoine:
      f_short = lambda: self.close_quoine(ex_short)

    if name_long == Tick.BitFlyer:
      f_long = lambda: self.close_bitflyer(ex_long)
    elif name_long == Tick.Quoine:
      f_long = lambda: self.close_quoine(ex_long)

    if f_short is None or \
       f_long is None:
      self.logger.error('unknow exchanger, short={}, long={}'
                        .format(name_short, name_long))
      return False

    results = {}

    def on_short(future):
      results[name_short] = future.result()

    def on_long(future):
      results[name_long] = future.result()
    
    fs = [(f_short, on_short), (f_long, on_long)]

    with get_executor() as executor:
      def to_future(fs):
        f, callback = fs
        future = executor.submit(f)
        future.add_done_callback(callback)
        return future
      futures = [to_future(f) for f in fs]
      timeout = 300 # seconds
      try:
        concurrent.futures.wait(futures, timeout=timeout)
      except concurrent.futures.TimeoutError as e:
        self.logger.error(('クローズ処理がタイムアウトしました, ' +
                           'timeout={}').format(timeout))

    if name_short not in results or results[name_short] is None:
      self.logger.error(('ショートポジションのクローズに失敗しました, ' +
                         'exchanger={}, lot={}')
                        .format(name_short,
                                sum(results[name_short]['sizes'])))
      return False

    if name_short not in results or results[name_long] is None:
      self.logger.error(('ロングポジションのクローズに失敗しました, ' +
                         'exchanger={}, lot={}, ids={}')
                        .format(name_long,
                                sum(results[name_long]['sizes']),
                                results[name_long]['ids']))
      return False

    return True

  def open_bitflyer(self, side, price, lot):
    """
    ( side: str, price: float, lot: float ) -> OnePosition
    """
    bitflyer = self.markets.BitFlyer
    position = bitflyer.open_position(side, price, lot)
    return position

  def open_quoine(self, side, price, lot):
    """
    ( side: str, price: float, lot: float ) -> OnePosition
    """
    quoine = self.markets.Quoine
    position = quoine.open_position(side, price, lot)
    return position

  def close_bitflyer(self, position):
    """
    ( position: OnePosition ) -> bool
    """
    bitflyer = self.markets.BitFlyer
    success = bitflyer.close_position(position)
    return success

  def close_quoine(self, position):
    """
    ( position: OnePosition ) -> bool
    """
    quoine = self.markets.Quoine
    success = quoine.close_position(position)
    return success

  def is_busy_bitflyer(self):
    bitflyer = self.markets.BitFlyer
    is_busy = bitflyer.is_busy()
    return is_busy
