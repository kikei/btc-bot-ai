import os
import pytest
import sys

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'src'))

from classes import OnePosition

def test_priceMean():
  exchanger = 'test'
  price = 500000
  one = OnePosition(exchanger, [1.0], [price], side=OnePosition.SideLong)
  assert price == one.priceMean()
