import datetime
from pytz import timezone


class EventManager(object):
    '''
    Manager for periodic events.

    parameters

    period: integer
        number of days between events
        default: 1

    max_daily_hits: integer
        upper limit on the number of times per day the event is triggered
        default: 1

    intraday_func: function (returns a boolean)
        decision function for timimng an intraday entry point

    start_date: datetime.date
        initial date the event can take place
        default: datetime.date(1900,1,1)

    open_time: datetime.time
        earliest time in the intraday window
        default: 9:31

    close_time: datetime.time
        latest time in the intraday window
        default: 15:29

    tz
        type: timezone obj
        All datetimes converted to this timezone
        default: US/Eastern
    '''

    def __init__(self,
                 period=1,
                 max_daily_hits=1,
                 intraday_func=None,
                 start_date=datetime.date(1900,1,1),
                 open_time=datetime.time(9,31,0),
                 close_time=datetime.time(15,29,0),
                 tz=timezone('US/Eastern')):

        self.delta_t = datetime.timedelta(days=period)
        self.max_daily_hits = max_daily_hits
        self.remaining_hits = max_daily_hits
        self.start_date = start_date
        self.open_time = open_time
        self.close_time = close_time
        self.next_trade_date = self.start_date
        self.tz = tz
        self._intraday_func = intraday_func

    def signal(self, *args, **kwargs):
        '''
        Entry point for the intraday_func
        All arguments are passed to intraday_func
        '''
        now = get_datetime().astimezone(self.tz)
        if now.date() < self.next_trade_date:
            return False
        if not self.open_for_biz(now):
            return False
        decision = self._intraday_func(*args, **kwargs)
        if decision:
            self.remaining_hits -= 1
            if self.remaining_hits <= 0:
                self.set_next_trade_date(now)
        return decision

    def set_next_trade_date(self, dt):
        self.remaining_hits = self.max_daily_hits
        today = dt.date()
        self.next_trade_date = today + self.delta_t

    def open_for_biz(self, dt):
        t = dt.astimezone(self.tz).time()
        closed_for_day = (t > self.close_time)
        open_for_day = (t >= self.open_time)
        return open_for_day and not closed_for_day



'''
This is a second version that uses the trading calendar in Zipline.

If it is between the open and close time on the event date,
the passed entry_func is called for the entry decision. The
maximum daily hits works correctly for this version.
'''

from zipline.utils import tradingcalendar as calendar


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
                 rule_func=None,
                 max_daily_hits=1):

        self.period = period
        self.max_daily_hits = max_daily_hits
        self.remaining_hits = max_daily_hits
        self.next_event_date = None
        self.market_open = None
        self.market_close = None
        self._rule_func = rule_func

    @property
    def todays_index(self):
        dt = calendar.canonicalize_datetime(get_datetime())
        return calendar.trading_days.searchsorted(dt)

    def open_and_close(self, dt):
        return calendar.open_and_closes.T[dt]

    def __call__(self, *args, **kwargs):
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
