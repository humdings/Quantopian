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
