from abc import ABC, abstractmethod

class AbstractListener(ABC):
  
  @abstractmethod
  def handleEntry(self):
    raise NotImplementedError('handleEntry')
