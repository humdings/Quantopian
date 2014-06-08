'''
This algorithm manages a bear market portfolio and a bull market portfolio.

It allocates a percentage of the account to each portfolio based on a confidence
level obtained from several tailing windows of returns.

The allocation within each portfolio is evenly weighted.
'''


import pandas as pd
import numpy as np

import datetime
from pytz import timezone
from zipline.utils import tradingcalendar as calendar


###################
# Time Management #
###################

class EventManager(object):
    '''
    Manager for periodic events.

    parameters

    period: integer
        number of business days between events
        default: 1

    max_daily_hits: integer
        upper limit on the number of times per day the event is triggered.
        (trading controls could work for this too)
        default: 1

    rule_func: function (returns a boolean)
        decision function for timimng an intraday entry point
    '''

    def __init__(self,
                 period=1,
                 max_daily_hits=1,
                 rule_func=None):

        self.period = period
        self.max_daily_hits = max_daily_hits
        self.remaining_hits = max_daily_hits
        self._rule_func = rule_func
        self.next_event_date = None
        self.market_open = None
        self.market_close = None

    @property
    def todays_index(self):
        dt = calendar.canonicalize_datetime(get_datetime())
        return calendar.trading_days.searchsorted(dt)

    def open_and_close(self, dt):
        return calendar.open_and_closes.T[dt]

    def signal(self, *args, **kwargs):
        '''
        Entry point for the rule_func
        All arguments are passed to rule_func
        '''
        now = get_datetime()
        dt = calendar.canonicalize_datetime(now)
        if self.next_event_date is None:
            self.next_event_date = dt
            times = self.open_and_close(dt)
            self.market_open = times['market_open']
            self.market_close = times['market_close']
        if now < self.market_open:
            return False
        if now == self.market_close:
            self.set_next_event_date()
        decision = self._rule_func(*args, **kwargs)
        if decision:
            self.remaining_hits -= 1
            if self.remaining_hits <= 0:
                self.set_next_event_date()
        return decision

    def set_next_event_date(self):
        self.remaining_hits = self.max_daily_hits
        tdays = calendar.trading_days
        idx = self.todays_index + self.period
        self.next_event_date = tdays[idx]
        times = self.open_and_close(self.next_event_date)
        self.market_open = times['market_open']
        self.market_close = times['market_close']



def entry_func(dt):
    '''
    rule_func passed to EventManager for
    an intraday entry decision.
    '''
    dt = dt.astimezone(timezone('US/Eastern'))
    return dt.hour == 11 and dt.minute <= 30



###############################
# Accounting/Order Management #
###############################

def get_leverage(P):
    longs, shorts = 0, 0
    positions = P.positions
    for pos in positions:
        value = positions[pos].amount * positions[pos].last_sale_price
        if value > 0:
            longs += value
        elif value < 0:
            shorts += abs(value)
    return (longs + shorts) / P.portfolio_value

####################
# Helper functions #
####################

def returns_confidence(R):
    '''
    Calculates the sum of the returns over each trailing
    window in the returns series R. It gains confidence
    for each positive return and loses some for each negative
    window.

    Param:
        R: array/series
            Series of porfolio or benchmark returns

    Returns: float
        -1.0 =< Confidence level =< 1.0

    '''
    x = 1.0 / len(R)
    signal = 0
    for i in range(1, len(R)):
        r = R.tail(i).sum()
        if r > 0:
            signal += x
        elif r < 0:
            signal -= x
    return signal


# Global instance of the EventManager
trade_manager = EventManager(period=20, rule_func=entry_func)

########################
# Qunatopian Functions #
########################

def initialize(context):
    '''
    Called once at the very beginning of a backtest (and live trading).
    Use this method to set up any bookkeeping variables.

    The context object is passed to all the other methods in your algorithm.

    Parameters

    context: An initialized and empty Python dictionary that has been
             augmented so that properties can be accessed using dot
             notation as well as the traditional bracket notation.

    Returns None
    '''
    set_commission(commission.PerShare(cost=0.01, min_trade_cost=1.0))

    # Calculation parameters
    context.leverage= 1.0

    # If True, this will allow up to 1.0x leverage beyond context.leverage
    context.allow_additional_leverage = True

    #setup the identifiers and data storage
    context.bulls = [sid(19656), sid(19655),
                     sid(19660), sid(19658),
                     sid(19654), sid(19659),
                     sid(19662), sid(19657),
                     sid(19661)]

    context.bears = [sid(23911), sid(25801)]




def handle_data(context, data):
    '''
    Called when a market event occurs for any of the algorithm's
    securities.

    Parameters

    data: A dictionary keyed by security id containing the current
          state of the securities in the algo's universe.

    context: The same context object from the initialize function.
             Stores the up to date portfolio as well as any state
             variables defined.

    Returns None
    '''

    leverage = get_leverage(context.portfolio)

    record(leverage=leverage)
    # Check for the entry signal from the event manager
    if trade_manager.signal(get_datetime()):

        # Pull trailing daily close prices of the bull portfolio
        historical_prices = history(500,'1d','price')[context.bulls]

        # convert prices into day over day returns:
        historical_returns = historical_prices.pct_change().dropna()

        # Average daily returns of the bull portfolio
        R = historical_returns.T.mean()

        # get the current confidence level and add it to the bulls weight
        confidence = returns_confidence(R)
        wbulls = context.leverage + confidence

        # Correct to maximum allowed leverage
        if not context.allow_additional_leverage:
            wbulls = min(wbulls, context.leverage)

        # dont let bears get shorted if using leverage
        wbears = max(0, context.leverage - wbulls)

        record(bear_pct=wbears,
               bull_pct=wbulls)

        wbulls /= len(context.bulls)
        wbears /= len(context.bears)

        for sec in context.bulls:
            order_target_percent(sec, wbulls)
        for sec in context.bears:
            order_target_percent(sec, wbears)
