import logging

from classes import PlayerActions
from ActionsDispatcher import ActionsDispatcher, Action
from monitors.AbstractMonitor import FinishMonitoring

class PositionsPlayer(object):
  """
  Connect actions creator and executor
  """
  def __init__(self, models, ActionCreator, ActionExecutor, accountId, logger=None):
    assert ActionCreator is not None
    assert ActionExecutor is not None
    self.accountId = accountId
    self.models = models
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    
    executor = ActionExecutor(models, accountId=accountId, logger=logger)
    self.actionCreator = ActionCreator(models,
                                       accountId=accountId, logger=logger)
    self.actionExecutor = executor
    
    dispatcher = ActionsDispatcher()
    dispatcher.adds({
      PlayerActions.CloseForProfit: executor.handleClose,
      PlayerActions.CloseForLossCut: executor.handleClose,
      PlayerActions.Exit: lambda: FinishMonitoring.raiseEvent('Exit')
    })
    self.dispatcher = dispatcher
  
  def run(self):
    models = self.models
    positions = models.Positions.currentOpen(accountId=self.accountId)
    action = self.actionCreator.createAction(positions)
    processed = self.dispatcher.dispatch(action)
