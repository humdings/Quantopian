
import pandas as pd


def targets_from_weights(context, W):
    '''
    context: obj
        contains current portfolio state
    W: pandas Series
        target weights vector indexed by sid.

    returns: Series
        target position sizes required to achieve target weights.

    Note: Decimal sizes are allowed here, they will be rounded
          in zipline before they are placed.
    '''
    equity = context.portfolio.portfolio_value

    current_prices = history(1, '1d', 'price').iloc[-1]
    return (W * equity) / current_prices
    


# These ones are not Quantopian specific, but accomplish the same thing

def targets_from_weights(W, prices, funds):
    '''
    W: weight vector
    prices: Price vector
    funds: total $

    Assumes fractional shares are not allowed
    '''
    return (W * funds) // prices

def orders_from_targets(T, P):
    '''
    T: target position vector
    P: current position vector
    '''
    return T - P

def orders_from_weights(W, P, prices, funds):
    '''
    T: target position vector
    P: current position vector
    prices: Price vector
    funds: total $
    '''
    T = targets_from_weights(W, prices, funds)
    return orders_from_targets(T, P)
