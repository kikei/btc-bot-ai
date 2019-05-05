import base64
import json
import requests
import logging

def decodeToken(token):
  ts = token.split('.')
  if len(ts) != 3:
    raise ValueError('Invalid JWT token: {token}'.format(token=token))
  s = ts[1]
  s += '=' * (4 - (len(s) % 4))
  s = base64.b64decode(s)
  obj = json.loads(s.decode())
  return obj

def identityInToken(token):
  obj = decodeToken(token)
  return obj['identity']

class Dashboard(object):
  def __init__(self, uri, logger=None):
    self.uri = uri
    self.uriLogin = uri + '/login'
    self.uriTicks = uri + '/ticks'
    self.uriRefresh = uri + '/refresh'
    self.uriConfidences = uri + '/btctai/{accountId:}/confidences'
    self.uriTrendStrength = uri + '/btctai/{accountId:}/trendStrength'
    self.accountId = None
    self.accessToken = None
    self.refreshToken = None
    if logger is None:
      logger = logging.getLogger()
    self.logger = logger
  
  def requestLogin(self, userName, password):
    payload = {'username': userName, 'password': password}
    headers = {'Content-Type': 'application/json'}
    r = requests.post(self.uriLogin, data=json.dumps(payload), headers=headers)
    if r.status_code != requests.codes.ok:
      raise Exception('Failed to login, status={status}'
                      .format(status=r.status_code))
    body = r.json()
    accessToken = body['access_token']
    refreshToken = body['refresh_token']
    self.logger.info('Login succeed, token={a}, refresh={r}'
                     .format(a=accessToken, r=refreshToken))
    self.accountId = identityInToken(accessToken)
    self.accessToken = accessToken
    self.refreshToken = refreshToken
    return accessToken
  
  def requestPrivate(self, uri, headers={}, payload=None, request=requests.get):
    if self.accessToken is None:
      raise Exception('Not be logged in.')
    if headers is None:
      hs = {}
    hs = {'Content-Type': 'application/json',
          'Authorization': 'Bearer {token}'.format(token=self.accessToken),
          **headers}
    if payload is None:
      data = {}
    else:
      data = json.dumps(payload)
    r = request(uri, data=data, headers=hs)
    if r.status_code == 401:
      self.accessToken = None
      r = self.requestRefreshToken()
      if self.accessToken is not None:
        return self.requestPrivate(uri, headers, payload)
      raise Exception('Failed to refresh token, status={status}'
                      .format(status=r.status_code))
    elif r.status_code != requests.codes.ok:
      raise Exception('Failed to request, url={url}, status={status}'
                      .format(url=uri, status=r.status_code))
    else:
      return r
  
  def requestRefreshToken(self):
    self.logger.debug('Requesting to refresh token, token={t}.'
                      .format(t=self.refreshToken))
    if self.refreshToken is None:
      raise Exception('Not be logged in.')
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer {t}'.format(t=self.refreshToken)}
    r = requests.post(self.uriRefresh, headers=headers)
    if r.status_code == 401:
      raise Exception('Failed to refresh token, status={s}.'
                      .format(s=r.status_code))
    body = r.json()
    self.logger.debug('Result: {r}.'.format(r=body))
    self.accessToken = body['access_token']
    self.logger.debug('Done, new access token is {t}.'.format(t=self.accessToken))
    return r
  
  def requestTicks(self, exchanger, start):
    uri = ('{uri}?exchangers={ex}&start={s}&limit={l}&order=1'
           .format(uri=self.uriTicks, ex=exchanger,
                   s=start, l=8192))
    r = self.requestPrivate(uri)
    ticks = r.json()
    return ticks
  
  def saveConfidence(self, date, long, short, status):
    """
    (self: Dashboard, date: datetime, long: float, short: float, status: str)
    -> json: dict
    """
    url = self.uriConfidences.format(accountId=self.accountId)
    payload = {
      'timestamp': date.timestamp(),
      'long': long,
      'short': short,
      'status': status
    }
    r = self.requestPrivate(url, payload=payload, request=requests.put)
    if r.status_code != requests.codes.ok:
      raise Exception('Failed to login, status={status}'
                      .format(status=r.status_code))
    body = r.json()
    return body
  
  def saveTrend(self, date, trend):
    """
    (self: Dashboard, date: datetime, trend: float) -> json: dict
    """
    url = self.uriTrendStrength.format(accountId=self.accountId)
    payload = {
      'timestamp': date.timestamp(),
      'strength': trend
    }
    r = self.requestPrivate(url, payload=payload, request=requests.put)
    if r.status_code != requests.codes.ok:
      raise Exception('Failed to login, status={status}'
                      .format(status=r.status_code))
    body = r.json()
    return body
