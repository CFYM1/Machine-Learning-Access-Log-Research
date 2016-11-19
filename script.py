# Naive Bayes Classifier test with nltk
#
# ISEN - 2016
#
# Python 2.7.6

#!/usr/bin/python

import argparse
import numpy
import pytz
import request
import requestclassifier
import scalper

from datetime import datetime

def test_requests(request_classifier):
    """A range of tests to try with our classifier.
    Parameters
    ----------
    request_classifier : object
        Our request classifier to work with.

    """
    requests = []

    requests.append((request.Request(['195.154.169.9', '-', '-',
         datetime(2016, 4, 10, 4, 46, 40, tzinfo=pytz.utc), 'GET', '/', '200',
         '42751', '-',
         'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0']),
         'OK'))

    print('')
    request_number = 0

    for request_item in requests:
        print('REQUEST #' + str(request_number) + ' ~')
        request_classifier.try_classify_request(request_item)
        request_number += 1
        print('')

def create_argument_parser():
    """Create the argument parser.

    """
    parser = argparse.ArgumentParser(description='Create a Naive Bayes \
        classifier.')

    parser.add_argument('-l', '--log-file', dest='log_file',
        default='./log.csv',
        help='the .csv file to train the classifier with')
    parser.add_argument('-a', '--access-log', dest='access_log', nargs=3,
        default=None, metavar=('access.log', 'filter.xml', 'blacklist.txt'),
        help='the files needed to use an Apache access log with Scalp')
    parser.add_argument('-v', '--verbose', help="increase output verbosity",
        action="store_true")

    return parser.parse_args()

args = create_argument_parser()

if (args.access_log == None):
    request_classifier = requestclassifier.RequestClassifier(
        args.log_file, 'csv', args.verbose)
else:
    log_file = scalper.scalper(args.access_log[0], args.access_log[1],
        args.access_log[2], False)
    request_classifier = requestclassifier.RequestClassifier(
        log_file, 'access_log', args.verbose)

request_classifier.train()
test_requests(request_classifier)
