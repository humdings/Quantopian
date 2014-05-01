



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
