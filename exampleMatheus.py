from backtesting import evaluateHist
from strategy import Strategy
from order import Order
import numpy as np

class EMA(Strategy):
  
  def __init__(self):
    self.signal = 0
    self.signal2 = 0
    self.prices = []
    self.sizeqS = 8
    self.sizeqB = 16
    self.r = 0.5
    self.multiplierS = 2 / (self.sizeqS + 1)
    self.multiplierB = 2 / (self.sizeqB + 1)
    self.prev_emaS = None
    self.prev_emaB = None

  def _calc_EMA(self, prices, window):
    a = []
    b = []
    for i in range(len(prices[-window:])):
        a.append(pow(self.r,i) * prices[i])
        b.append(pow(self.r,i))
    return sum(a)/sum(b)


  def push(self, event):
    price = event.price[3]
    self.prices.append(price)
    orders = []

    if len(self.prices) >= self.sizeqB:
        emaS = self._calc_EMA(self.prices, self.sizeqS)
        if self.prev_emaS is None:
            self.prev_emaS = emaS
        emaB = self._calc_EMA(self.prices, self.sizeqB)
        if self.prev_emaB is None:
            self.prev_emaB = emaB
    
        if (self.prev_emaS > self.prev_emaB and emaB > emaS):
            if self.signal == -1:
                orders.append(Order(event.instrument, 1, 0))
            orders.append(Order(event.instrument, 1, 0))
            self.signal = 1

        elif self.prev_emaS > price and self.signal == 1:
            if self.signal == 1:
                orders.append(Order(event.instrument, 1, 0))
            orders.append(Order(event.instrument, 1, 0))
            self.signal = -1
        
        if (self.prev_emaS > self.prev_emaB and emaB > emaS) and self.signal2 != -1:
            orders.append(Order(event.instrument, -1, 0))
            self.signal = -1
        
        elif self.prev_emaS > price and self.signal2 == -1:
            if self.signal == 1:
                orders.append(Order(event.instrument, -1, 0))
            orders.append(Order(event.instrument, -1, 0))
            self.signal = -1

        self.prev_emaS = emaS
        self.prev_emaB = emaB
        del self.prices[0]

    return orders

class TheOneChoice(Strategy):
  
  def __init__(self):
    self.countS = 0
    self.countB = 0
    self.signal = 0
    self.prev = 0
    self.numB = 6
    self.numS = 2
      

  def push(self, event):
    price = event.price[3]
    # self.prices.append(price)
    orders = []
    
    # #count-down
    if price < self.prev: 
        self.countS+=1

    #count-up
    if price > self.prev: 
        self.countB+=1

    if self.countS > self.numS and self.signal != -1: 
        if self.signal == 1: 
            orders.append(Order(event.instrument, -1, 0))
        orders.append(Order(event.instrument, -1, 0))
        self.countS = 0
        self.signal = 1

    if self.countB > self.numB and self.signal != -1: 
        if self.signal == 1: 
            orders.append(Order(event.instrument, 1, 0))
        orders.append(Order(event.instrument, 1, 0))
        self.countS = 1
        self.signal = -1

    self.prev = price
    return orders

print(evaluateHist(EMA(), {'IBOV':'^BVSP.csv'}))
print(evaluateHist(TheOneChoice(), {'IBOV':'^BVSP.csv'}))