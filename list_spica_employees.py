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

def get_auth_token(api_url, api_username, api_password, api_key):
    url = api_url + "/Session/GetSession"
    data = json.dumps({"Username": api_username, "Password": api_password, "Sid": ""})
    req = request.Request(url, data=data.encode(), headers={"Authorization": "SpicaToken {}".format(api_key), 'Content-Type': 'application/json'})
    try:
        resp = request.urlopen(req)
        token = api_key + ":" + json.loads(resp.read())['Token']
    except:
        token = api_key
    return "SpicaToken " + token

def get_employees(api_url, api_key, api_session):
    url = api_url + "/employee"
    req = request.Request(url, headers={"Authorization": auth_token})
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
    parser.add_argument('--username', dest='api_username', action='store',
                    default=SPICA_USER, type=str,
                    help='Uporabnik za dostop do Spice')
    parser.add_argument('--password', dest='api_password', action='store',
                    default=SPICA_PASSWD, type=str,
                    help='Geslo za dostop do Spice')
    args = parser.parse_args()
    auth_token = get_auth_token(args.api_url, args.api_username, args.api_password, args.api_key)
    employees = get_employees(args.api_url, args.api_key, auth_token)
    for employee in employees:
        print("{ReferenceId} {LastName} {FirstName}".format(**employee))
        print("  {}".format(employee))
