# Naive Bayes Classifier test with nltk
#
# ISEN - 2016
#
# Python 2.7.6

import flatdict
import httpagentparser
import nltk
import pandas
import random
import re
import request
import sys
import time

from datetime import datetime
from nltk.classify import NaiveBayesClassifier
from pandas import DataFrame
from random import randint

class RequestClassifier:
    def __init__(self, log_file='./log.csv', file_type='csv', verbose=False):
        """Construtor to create a RequestClassifier instance.

        Parameters
        ----------
        log_file : str
            Optional parameter needed to locate our log file (in .csv format).
            If no log file is provided, './log.csv' will be considered.

        verbose : bool
            Optional. Will be used to configure the verbosity of the
            classifier. Currently not used.

        """
        self.__log_file = log_file
        self._type = file_type
        self.verbose = False

    def _log_prefix(self):
        """Return the prefix wanted for each message to print.

        """
        return  time.strftime('%m/%d/%Y | %I:%M:%S %p') + ' > '

    def _display_message(self, message):
        """Display a message. Convert it in string if needed. Add a prefix to
            it.

        Parameters
        ----------
        message : object
            The message to print.

        """
        print(self._log_prefix() + str(message))

    def _display_loader(self):
        """Display a loader when extracting features.

        """
        # Incrementing our counter to display our loader correctly.

        self.__request_processed += 1
        percentage = float(self.__request_processed) \
            / self.__request_number * 100
        to_print = '\r' + self._log_prefix()\
            + 'Request: {0} / {1} ({2}%)'\
            .format(unicode(str(self.__request_processed), 'utf-8'),
            unicode(str(self.__request_number), 'utf-8'),
            unicode('{0:.0f}'.format(percentage), 'utf-8'))

        sys.stdout.write(to_print)
        sys.stdout.flush()

    def train(self):
        """Train the classifier.

        """
        # Getting requests and features.

        self.set_requests()
        self.feature_sets = self.get_feature_sets()

        self._display_message('Splitting into a train and test sets...')

        # Creating a training set (to train our classifier) and a test set.

        feature_sets_size = len(self.__feature_sets)
        self.train_set = self.__feature_sets[:int(feature_sets_size/2)]
        self.test_set = self.__feature_sets[int(feature_sets_size/2)+1:]

        self._display_message('Training the Naive Bayes classifier...')

        # Training our classifier, and testing it.

        self.classifier = NaiveBayesClassifier.train(self.train_set)
        self.display_results()

    def display_results(self):
        """Print the results obtained with the classifier.

        """
        accuracy = nltk.classify.accuracy(self.classifier, self.test_set) * 100
        accuracy = unicode('{0:.2f}%'.format(accuracy), 'utf-8')

        self._display_message('Accuracy is ' + accuracy + '.')
        self._display_message('Most useful features:')
        self.classifier.show_most_informative_features(5)

    def _get_requests_from_csv(self):
        """Get the requests sorted from a CSV file.

        """
        columns = request.Request.LABELS
        columns.append('pass')

        self._display_message('Getting \'%s\'...' % self.__log_file)

        # Getting our .csv file, transforming it into a data frame instance.

        data = pandas.read_csv(self.__log_file, encoding='utf-8',
            error_bad_lines=False, warn_bad_lines=False, dtype=object)
        data_frame = DataFrame(data)
        data_frame.columns = columns

        self._display_message('Preparing a list of requests...')

        # Creating a list containing all pass values ('OK' or 'KO').

        pass_values = data_frame['pass'].values.tolist()

        # The 'pass' column is not needed anymore.

        data_frame = data_frame.drop('pass', 1)

        # Creating a list of tuples containing a request and its pass values
        # associated to it.

        self.__sorted_requests = zip(data_frame.T.to_dict().values(),
            pass_values)

    def _get_requests_from_access_log_object(self):
        """Get the requests sorted from an Apache access log object.

        """
        pass_values = [pass_value['pass'] for pass_value in self.__log_file]
        [request.pop('pass') for request in self.__log_file]
        request_list = [request for request in self.__log_file]
        self.__sorted_requests = zip(request_list, pass_values)

    def set_requests(self):
        """Get the requests from a given file, then shuffle the list and return
        it.

        """
        if self._type == 'csv':
            self._get_requests_from_csv()
        elif self._type == 'access_log':
            self._get_requests_from_access_log_object()

        self._display_message('Shuffling the list...')

        # We need to shuffle our requests to make them more 'real world'-like.

        random.shuffle(self.__sorted_requests)

    def get_feature_sets(self):
        """Get some feature sets extracted from the requests given.

        """
        self._display_message('Extracting features...')

        # '__request_number' and '__request_processed' are needed for our
        # loader.

        self.__request_number = len(self.__sorted_requests)
        self.__request_processed = 0

        # Getting our feature sets for each request of our list.

        self.__feature_sets = [(self.get_features(request), answer)
            for (request, answer) in self.__sorted_requests]
        self.__request_processed = 0

        print('')

    def get_features(self, request):
        """Call extract_features. Display a loader.
        Parameters
        ----------
        request : dict(object)
            The request for the features to be extracted.

        """
        features = self.extract_features(request)
        self._display_loader()

        return features

    def try_classify_request(self, request_sorted):
        """A range of tests to try with our classifier.
        Parameters
        ----------
        request_sorted : tuple(dict(object), str)
            The request to classify with the expected result ('OK' or 'KO').

        """
        request = request_sorted[0]
        expected_result = request_sorted[1]
        result = self.classifier.classify(request)
        is_correct = (expected_result == result)

        print(request)
        self._display_message('expected \'' + expected_result +
            '\' and got \'' + result + '\': ' + str(is_correct))

    def _process_url(self, features, url):
        """Process the url given and store it in the features.
        Parameters
        ----------
        features : dict(str)
            The features container to store our URL result(s).
        url : str
            The URL to process.

        """
        # '/' or '/' or ' ' or '\' or '?' or '&' or '=' or '_' or '.' or '-'.

        words = re.split('\/|%2F|%5C|%20|\?|\&|=|\_|\.|\-',
            url)

        for word in words:
            features['contains({})'.format(word)] = word

        return features

    def extract_features(self, request):
        """Extract features from a request given.
        Parameters
        ----------
        request : dict(object)
            The request for the features to be extracted.

        """
        # All features needed will be stored in a dictionary. Our machine
        # learning algorithm will be able to learn from it.

        features = {}
        features['remote_host'] = request['remote_host']
        features['remote_user'] = request['remote_user']

        date_time = request['time_received_utc_datetimeobj']
        features['time'] = date_time.strftime('%I:%M:%S')
        features['date'] = date_time.strftime('%Y-%m-%d')

        features['request_method'] = request['request_method']
        features['status'] = request['status']

        user_agent = flatdict.FlatDict(
            httpagentparser.detect(request['request_header_user_agent']))
        features.update(user_agent)

        features['url_len'] = str(len(request['request_url']))
        features['referer_len'] = str(len(request['request_header_referer']))

        features['response_bytes'] = request['response_bytes']

        features = \
            self._process_url(features, request['request_header_referer'])
        features = self._process_url(features, request['request_url'])

        return features
