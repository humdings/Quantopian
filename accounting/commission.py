

class CommissionTracker():
    '''
    Keeps track of the total commission and the last commission
    paid throughout a backtest.

    Orders are passed via the update function, e.g.
        ct = CommissionTracker()
        x = order(sid, amount)
        ct.update(x)
    '''
    def __init__(self, last_commission=0, total_commission=0):
        '''
        No required args, but last_commission and total_commission
        can be specified at initialization.
        '''
        self.total_commission = total_commission
        self.last_commission = last_commission
        self.orders = set()

    def calculate(self, orders):
        commission = 0
        if orders:
            filled = set()
            for x in orders:
                c = get_order(x).commission
                if c is not None:
                    commission += c
                    filled.add(x)
            self.orders = self.orders - filled
        return commission

    def update(self, orders):
        if orders is not None:
            if type(orders) in [str, unicode]:
                orders = [orders]
            self.orders.update(orders)
        com = self.calculate(self.orders)
        if com > 0:
            self.last_commission = com
        self.total_commission += com
