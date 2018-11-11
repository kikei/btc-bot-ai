class ActionsDispatcher(object):
  def __init__(self):
    self.mapping = {}

  def add(self, name, func):
    self.mapping[name] = func

  def adds(self, mapping):
    for name, func in mapping.items():
      self.mapping[name] = func
  
  def dispatch(self, action):
    if action is not None and action.name in self.mapping:
      f = self.mapping[action.name]
      return f(*action.args)


class Action(object):
  def __init__(self, name, *args):
    self.name = name
    self.args = args

  def __str__(self):
    def mystr(x):
      if isinstance(x, list):
        text = '[{t}]'.format(t=', '.join(mystr(a) for a in x))
        return text
      else:
        return str(x)
    text = ('Action(name={name}, args[{i}]=[{t}])'
            .format(name=self.name, i=len(self.args),
                    t=', '.join(mystr(a) for a in self.args)))
    return text
