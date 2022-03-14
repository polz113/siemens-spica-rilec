#!/usr/bin/python3

import urllib
import json
import datetime
import csv
import glob
import os
import fcntl
import itertools
import argparse
import traceback


from collections import defaultdict

from urllib import parse, request

from siemens_spica_settings import APIURL, SPICA_USER, SPICA_PASSWD, SPICA_KEY,\
    SPOOL_DIR, SPOOL_FNAME, OLDEVENTS_FNAME, NOCOMMIT_FNAME


# SPOOL_DIR = "/home/polz/projekti/siemens_log_examples/spool"


#SPOOL_FNAME = "new_events.csv"
#OLDEVENTS_FNAME = "old_events.csv"

def get_employees(api_url, api_key):
    url = api_url + "/employee"
    req = request.Request(url, headers={"Authorization": "SpicaToken " + api_key})
    resp = request.urlopen(req)
    ret = json.loads(resp.read())
    return ret


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ustvari imenike za SAP ID in kadrovsko na osnovi podatkov iz Spice')
    parser.add_argument('--spooldir', dest='spooldir', action='store',
                    default=SPOOL_DIR,
                    help='Imenik s podatki')
    parser.add_argument('--url', dest='api_url', action='store',
                    default=APIURL,
                    help='Naslov Spice')
    parser.add_argument('--apikey', dest='api_key', action='store',
                    default=SPICA_KEY, type=str,
                    help='Skrivnost za dostop do Spice')
    args = parser.parse_args()
    employees = get_employees(args.api_url, args.api_key)
    print(employees)
