# Naive Bayes Classifier test with nltk
#
# ISEN - 2016
#
# Python 2.7.6

from collections import OrderedDict
from tabulate import tabulate

class Request(OrderedDict):
    LABELS = ['remote_host', 'remote_logname', 'remote_user',
        'time_received_utc_datetimeobj', 'request_method', 'request_url',
        'status', 'response_bytes', 'request_header_referer',
        'request_header_user_agent']

    def __init__(self, data):
        """Constructor to create a Request instance.
        Parameters
        ----------
        data : list(str)
            The data to store in the Request instance.

        """
        processed_data = zip(Request.LABELS, data)
        super(Request, self).__init__(processed_data)

    def __str__(self):
        """Return a string corresponding the request.

        """
        return tabulate([self.keys(), self.values()], headers='firstrow')
