from backtesting import evaluateHist, evaluateIntr
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

class MarketMaker(Strategy):
  def __init__(self):
    self.orders = []
    self.two_orders = []
    self.petr3 = None
    self.usd_brl = None
    self.spread = 50
    self.order_ids = None
    self.f = 2
    self.ti = 1.01
    self.tc = -0.035

  def get_pbr(self, petr3, usd_brl):
    #Ppbr = Ppetr3 * F(quantas pbr=petr3)/Pusr-brl * ti + tc
    pbr = ((petr3 * self.f) / usd_brl) * self.ti + self.tc
    return pbr

  def push(self, event):
    orders = []
    #checa petr3
    if event.instrument == "PETR3":
        self.petr3 = event.price[3]

    #checa usd_brl
    if event.instrument == "USDBRL":
        self.usd_brl = event.price[3]
    
    if self.petr3 and self.usd_brl:
        #calcula pbr
        pbr = self.get_pbr(self.petr3, self.usd_brl)

        #calcula spread
        buy_price = pbr - self.spread
        sell_price = pbr + self.spread

        #cancela atuais
        if self.order_ids:
            for order_id in self.order_ids:
                self.cancel(self.id, self.order_id)

        #manda duas novas ordens
        self.order_ids = []
        orders.append(Order("PBR", 1,buy_price))
        orders.append(Order("PBR", -1,sell_price))
        for order in orders:
            self.order_ids.append(order.id)

        return orders
    return []

    def fill(self, instrument, price, quantity, status):
        super().fill(instrument, price, quantity, status)
        orders = []

        #só fill ids ordens de pbr
        if instrument == "PBR":
            #comprar pbr -> vende petr3, compra dolar (no preço que tiver)
            if quantity == 1:
                orders.append(Order("PETR3", -1, 0))
                orders.append(Order("USDBRL", 1, 0))

            #vender pbr -> compra petr3, vende dolar (no preço que tiver)
            elif quantity == -1:
                orders.append(Order("PETR3", 1, 0))
                orders.append(Order("USDBRL", -1, 0))

        #submit a mercado
        return orders


print(evaluateHist(EMA(), {'IBOV':'^BVSP.csv'}))
print(evaluateHist(TheOneChoice(), {'IBOV':'^BVSP.csv'}))
print(evaluateIntr(MarketMaker(), {'USDBRL':'USDBRL.csv', 'PETR3':'PETR3.csv'}))
