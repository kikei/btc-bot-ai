import logging

from classes import PlayerActions
from ActionsDispatcher import ActionsDispatcher, Action
from monitors.AbstractMonitor import FinishMonitoring
from BudgetManager import BudgetManager
from TradeExecutor import TradeExecutor

class TradingPlayer(object):
  """
  Connect actions creator and executor.
  """
  def __init__(self, models, accountId, ActionCreator=None, ActionExecutor=None,
               logger=None):
    self.models = models
    self.accountId = accountId
    if ActionCreator is None:
      ActionCreator = BudgetManager
    if ActionExecutor is None:
      ActionExecutor = TradeExecutor
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    
    executor = ActionExecutor(models, accountId=accountId, logger=logger)
    self.actionCreator = ActionCreator(models, accountId=accountId, logger=logger)
    self.actionExecutor = executor
    
    dispatcher = ActionsDispatcher()
    dispatcher.adds({
      PlayerActions.OpenLong: executor.handleOpenLong,
      PlayerActions.OpenShort: executor.handleOpenShort,
      PlayerActions.IgnoreConfidence: executor.handleIgnoreConfidence,
      PlayerActions.CloseForProfit: executor.handleClose,
      PlayerActions.CloseForLossCut: executor.handleClose,
      PlayerActions.Exit: lambda: FinishMonitoring.raiseEvent('Exit')
    })
    self.dispatcher = dispatcher

  def run(self):
    models = self.models
    confidence = models.Confidences.oneNew(accountId=self.accountId)
    action = self.actionCreator.createAction(confidence)
    processed = self.dispatcher.dispatch(action)
