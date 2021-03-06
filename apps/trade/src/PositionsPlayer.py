import logging

from classes import PlayerActions
from ActionsDispatcher import ActionsDispatcher, Action
from monitors.AbstractMonitor import FinishMonitoring

class PositionsPlayer(object):
  """
  Connect actions creator and executor
  """
  def __init__(self, models, actionCreator, actionExecutor, accountId, logger=None):
    assert actionCreator is not None
    assert actionExecutor is not None
    self.models = models
    self.actionCreator = actionCreator
    self.actionExecutor = executor = actionExecutor
    self.accountId = accountId
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    dispatcher = ActionsDispatcher()
    dispatcher.adds({
      PlayerActions.CloseForProfit: executor.handleClose,
      PlayerActions.CloseForLossCut: executor.handleClose,
      PlayerActions.Exit: lambda: FinishMonitoring.raiseEvent('Exit')
    })
    self.dispatcher = dispatcher
  
  def run(self):
    action = self.actionCreator.createAction()
    processed = self.dispatcher.dispatch(action)
