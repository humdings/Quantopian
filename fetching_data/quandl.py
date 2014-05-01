
import datetime

import pandas as pd


class QuandlFetcher(object):
    """
    Modified version of the Quandl Python API that builds the
    url query string given a dataset code or list of dataset codes.

    url is retrieved via the attribute self.url

    parameters

    dataset: string or list
        A single dataset code or list of codes
        Dataset codes are available on the Quandl website

    Optional keyword args

    auth_token: string
        quandl api auth token, calls will be limited without a token

    trim_start: string
        first date in dataset

    trim_end: string
        last date in dataset

    collapse: string
        Options are daily, weekly, monthly, quarterly, annual

    transformation: string
        options are diff, rdiff, cumul, and normalize

    rows: string
        Number of rows which will be returned

    sort_order: string
        options are asc, desc. Default: `asc`

    Other `kwargs` are added to the url string with no interference.

    """

    API_URL = 'http://www.quandl.com/api/v1/'

    def __init__(self, dataset, **kwargs):
        self.url = self.build_url(dataset, **kwargs)

    def _append_query_fields(self, url, **kwargs):
        field_values = ['{0}={1}'.format(key, val)
                        for key, val in kwargs.items() if val]
        return url + 'request_source=python&request_version=2&' +'&'.join(field_values)

    def _parse_dates(self, date):
        if date is None:
            return date
        if isinstance(date, datetime.datetime):
            return date.date().isoformat()
        if isinstance(date, datetime.date):
            return date.isoformat()
        try:
            date = pd.to_datetime(date)
        except ValueError:
            raise ValueError("{} is not recognised a date.".format(date))
        return date.date().isoformat()

    def build_url(self, dataset, **kwargs):

        kwargs.setdefault('sort_order', 'asc')
        auth_token = kwargs.pop('auth_token', None)
        trim_start = self._parse_dates(kwargs.pop('trim_start', None))
        trim_end = self._parse_dates(kwargs.pop('trim_end', None))

        # Check whether dataset is given as a string (for a single dataset) or
        # an array (for a multiset call)

        #Unicode String
        if type(dataset) == unicode or type(dataset) == str:
            url = self.API_URL + 'datasets/{}.csv?'.format(dataset)

        #Array
        elif type(dataset) == list:
            url = self.API_URL + 'multisets.csv?columns='
            #Format for multisets call
            dataset = [d.replace('/', '.') for d in dataset]
            for i in dataset:
                url += i + ','
            #remove trailing ,
            url = url[:-1] + '&'

        #If wrong format
        else:
            error = "Your dataset must either be specified as a string (containing a Quandl code) or an array (of Quandl codes) for multisets"
            raise Exception(error)

        url = self._append_query_fields(
            url,
            auth_token=auth_token,
            trim_start=trim_start,
            trim_end=trim_end,
            **kwargs
        )
        return url
