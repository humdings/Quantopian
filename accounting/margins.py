import pandas as pd


class Margins(object):
    '''
    Calculates portfolio minimum margin requirement and
    keeps a dict of the requirement for each position.

    Also tracks the current leverage and remaining margin.
    '''

    def __init__(self, context, data, day_trader=False):
        self.initial_margin = 25000.0 if day_trader else 2000.0
        P = context.portfolio
        L, S = self.long_short_values(P)
        equity = P.portfolio_value
        self.position_margins = {}
        for stock in data.keys():
            self.position_margins[stock] = \
                self.position_requirement(context.portfolio.positions[stock])
        self.requirement = sum(self.position_margins.values())
        self.remaining_margin = equity - self.requirement
        self.leverage = (L + S) / equity

    def position_requirement(self, position):
        amount = position.amount
        last_sale_price = position.last_sale_price
        if amount >= 0:
            req = .25 * amount * last_sale_price
        else:
            if last_sale_price < 5:
                req = max(2.5 * amount, abs(amount * last_sale_price))
            else:
                req = max(5 * amount, abs(0.3 * amount * last_sale_price))
        return req

    def long_short_values(self, P):
        longs, shorts = 0, 0
        pos = P.positions
        for p in pos:
            value = pos[p].amount * pos[p].last_sale_price
            if value > 0:
                longs += value
            elif value < 0:
                shorts += abs(value)
        return longs, shorts

    def __repr__(self):
        template = \
"\nSymbol  Requirement\n{position_margins}\nMargin Requirement: {req}"
        return template.format(
            position_margins=pd.Series(
                {i.symbol : self.position_margins[i]
                 for i in self.position_margins}),
            req=self.requirement)

    def __getitem__(self, item):
        return self.position_margins[item]
