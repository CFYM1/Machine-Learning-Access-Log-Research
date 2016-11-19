#!/usr/bin/env python
"""
    Scalper is based on Scalp! Apache log based attack analyzer
    by Romain Gaucher <r@rgaucher.info> - http://rgaucher.info
                                          http://code.google.com/p/apache-scalp

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""
from __future__ import with_statement

import os
import sys
import time

import apache_log_parser as alp
import pandas as pd
import regex as re
from urlparse import urlparse

try:
    from lxml import etree
except ImportError:
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        try:
            import xml.etree.ElementTree as etree
        except ImportError:
            print "Cannot find the ElementTree in your python packages"


table = {}


class BreakLoop(Exception):
    pass


class object_dict(dict):
    def __init__(self, initd=None):
        if initd is None:
            initd = {}
        dict.__init__(self, initd)

    def __getattr__(self, item):
        d = self.__getitem__(item)
        # if value is the only key in object, you can omit it
        if isinstance(d, dict) and 'value' in d and len(d) == 1:
            return d['value']
        else:
            return d

    def __setattr__(self, item, value):
        self.__setitem__(item, value)


def __parse_node(node):
    tmp = object_dict()
    # save attrs and text, hope there will not be a child with same name
    if node.text:
        tmp['value'] = node.text
    for (k, v) in node.attrib.items():
        tmp[k] = v
    for ch in node.getchildren():
        cht = ch.tag
        chp = __parse_node(ch)
        if cht not in tmp:  # the first time, so store it in dict
            tmp[cht] = chp
            continue
        old = tmp[cht]
        if not isinstance(old, list):
            tmp.pop(cht)
            tmp[cht] = [old]  # multi times, so change old dict to a list
        tmp[cht].append(chp)  # add the new one
    return tmp


def parse(xml_file):
    try:
        xml_handler = open(xml_file, 'r')
        doc = etree.parse(xml_handler).getroot()
        xml_handler.close()
        return object_dict({doc.tag: __parse_node(doc)})
    except IOError:
        print("error: problem with the filter's file")
        return {}


def get_value(array, default):
    if 'value' in array:
        return array['value']
    return default



def analyzer(data):
    exp_line, regs, array, org_line = data[0], data[1], data[2], data[3]
    done = []
    # look for the detected attacks...
    # either stop at the first found or not

    for attack_type in regs.keys():
        if attack_type in regs:
            if attack_type not in array:
                array[attack_type] = {}
            for _hash in regs[attack_type]:
                if _hash not in done:
                    done.append(_hash)
                    attack = table[_hash]
                    if attack[0].search(exp_line):
                        if attack[1] not in array[attack_type]:
                            array[attack_type][attack[1]] = []
                        array[attack_type][attack[1]].append((exp_line, attack[3], attack[2], org_line))
                        return True


def scalper(access, filters, blacklistIPPath, outputCSV=True):
    global table
    if not os.path.isfile(access):
        print "error: the log file doesn't exist"
        return
    if not os.path.isfile(filters):
        print "error: the filters file (XML) doesn't exist"

    # load the XML file
    xml_filters = parse(filters)
    len_filters = len(xml_filters)
    if len_filters < 1:
        return
    # prepare to load the compiled regular expression
    regs = {}  # type => (reg.compiled, impact, description, rule)

    print "Loading XML file '%s'..." % filters
    for group in xml_filters:
        for f in xml_filters[group]:
            if f == 'filter':
                if type(xml_filters[group][f]) == type([]):
                    for elmt in xml_filters[group][f]:
                        rule, impact, description, tags = "", -1, "", []
                        if 'impact' in elmt:
                            impact = int(get_value(elmt['impact'], -1))
                        if 'rule' in elmt:
                            rule = get_value(elmt['rule'], "")
                        if 'description' in elmt:
                            description = get_value(elmt['description'], "")
                        if 'tags' in elmt and 'tag' in elmt['tags']:
                            if type(elmt['tags']['tag']) == type([]):
                                for tag in elmt['tags']['tag']:
                                    tags.append(get_value(tag, ""))
                            else:
                                tags.append(get_value(elmt['tags']['tag'], ""))
                        # register the entry in our array
                        for t in tags:
                            compiled = None
                            if t not in regs:
                                regs[t] = []
                            try:
                                compiled = re.compile(rule)
                            except Exception:
                                print "The rule '%s' cannot be compiled properly" % rule
                                return
                            _hash = hash(rule)
                            if impact > -1:
                                table[_hash] = (compiled, impact, description, rule, _hash)
                                regs[t].append(_hash)

    flag = {}  # {type => { impact => ({log_line dict}, rule, description, org_line) }}

    print "Processing the file '%s'..." % access

    methods = ["POST", "GET", "OPTIONS", "HEAD", "DELETE", "TRACE", "PUT", "CONNECT"]

    blacklistIPFile = open(blacklistIPPath, "r")
    blacklistIP = []
    print "Loading IP Blacklist File..."
    for line in blacklistIPFile:
        if line[0].isdigit():
            blacklistIP.append(line.split("\t", 1)[0])

    blacklistIPFile.close()
    if (outputCSV):
        columns = ["Host", "Log_Name", "Remote_User", "Date_Time", "Method", "URL", "Response_Code", "Bytes_Sent",
                   "Referer", "User Agent", "PASS"]
        data = pd.DataFrame(columns=columns)
    else:
        data = []

    count, lines, nb_lines = 0, 0, 0
    start = time.time()
    analyserKey = ['remote_host', 'remote_logname', 'remote_user', 'time_received', 'request_method', 'request_url',
                   'status', 'response_bytes', 'request_header_referer', 'request_header_user_agent', 'pass']
    parser = alp.make_parser("%h %l %u %t \"%r\" %>s %B \"%{Referer}i\" \"%{User-Agent}i\"")

    print "Searching for KO requests..."
    with open(access) as log_file:
        for line in log_file:
            lines += 1

            logline = parser(line)
            logline['pass'] = "OK"

            passval = 0

            if logline['remote_host'] in blacklistIP:
                passval += 1

            if logline['request_method'] not in methods:
                passval += 1

            path = urlparse(logline['request_header_referer']).path
            if len(logline['request_url']) > 1:
                if analyzer([(logline['request_url']), regs, flag, line]):
                    passval += 1
            if path != logline['request_url'] and len(path) > 1:
                if analyzer([(path), regs, flag, line]):
                    passval += 1

            if passval > 0:
                logline['pass'] = "KO"
                count += 1
            if (outputCSV):
                data.loc[len(data)] = list(logline[k] for k in analyserKey)
            else:
                data.append(dict((k, logline[k]) for k in analyserKey))

    if (outputCSV):
        print "Generating access_log_OKKO.csv File..."
        data.to_csv("access_log_OKKO.csv", index=False, error_bad_lines=False)

    tt = time.time() - start

    print("Scalper results:")
    print("\tProcessed %d lines " % (lines))
    print("\tFound %d attack patterns in %f s" % (count, tt))

    return data


def help():
    print("Scalper the apache log! by FCYM - https://github.com/FCYM")
    print("usage:  ./scalp.py [log_file] [filter_file] [blacklist_database.txt] ")


def main(argc, argv):
    if argc < 4 or argv[1] == "--help":
        help()
        sys.exit(0)
    else:
        for i in range(argc):
            filters = argv[2]
            access = argv[1]
            blacklistIPPath = argv[3]

    scalper(access, filters, blacklistIPPath, False)


if __name__ == "__main__":
    main(len(sys.argv), sys.argv)
