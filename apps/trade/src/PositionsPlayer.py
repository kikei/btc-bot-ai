import logging

from classes import PlayerActions
from ActionsDispatcher import ActionsDispatcher, Action
from monitors.AbstractMonitor import FinishMonitoring

class PositionsPlayer(object):
  """
  Connect actions creator and executor
  """
  def __init__(self, models, ActionCreator, ActionExecutor, logger=None):
    assert ActionsCreator is not None
    assert ActionExecutor is not None
    self.models = models
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
    
    executor = ActionExecutor(models, logger=logger)
    self.actionCreator = ActionCreator(models, logger=logger)
    self.actionExecutor = executor
    
    dispatcher = ActionsDispatcher()
    dispatcher.adds({
      PlayerActions.CloseForProfit: executor.handleClosePosition,
      PlayerActions.CloseForLossCut: executor.handleClosePosition,
      PlayerActions.Exit: lambda: FinishMonitoring.raiseEvent('Exit')
    })
    self.dispatcher = dispatcher
  
  def run(self):
    modles = self.models
    positions = models.Positions.currentOpen()
    action = self.actionCreator.createAction(positions)
    processed = self.dispatcher.dispatch(action)
