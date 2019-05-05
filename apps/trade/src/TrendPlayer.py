import logging

from classes import PlayerActions
from ActionsDispatcher import ActionsDispatcher, Action
from monitors.AbstractMonitor import FinishMonitoring

class TrendPlayer(object):
  """
  Connect actions creator and executor
  """
  def __init__(self, models, actionCreator, actionExecutor, accountId, logger=None):
    assert actionCreator is not None
    assert actionExecutor is not None
    self.models = models
    self.executor = executor = actionExecutor
    self.actionCreator = actionCreator
    self.accountId = accountId
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    # Setup dispatcher
    dispatcher = ActionsDispatcher()
    dispatcher.adds({
      PlayerActions.OpenLong: executor.handleOpenLong,
      PlayerActions.OpenShort: executor.handleOpenShort,
      PlayerActions.CloseForProfit: executor.handleClose,
      PlayerActions.CloseForLossCut: executor.handleClose,
      PlayerActions.Exit: lambda: FinishMonitoring.raiseEvent('Exit')
    })
    self.dispatcher = dispatcher

  def run(self):
    modles = self.models
    action = self.actionCreator.createAction()
    processed = self.dispatcher.dispatch(action)
