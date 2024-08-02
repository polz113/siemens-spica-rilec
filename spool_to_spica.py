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
FAKEEVENTS_FNAME = "fake_events.csv"

EVENT_TRANSLATIONS = {
    '2': 43,
    '7': 43,
    '8': 43,
    '69': 43,
    "odhod": 44,
    "malica": 45,
    "sluzbeni": 47,
    "zasebni": 48,
    "zdravnik": 70,
}

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

def get_employees(api_url, auth_token):
    url = api_url + "/employee"
    req = request.Request(url, headers={"Authorization": auth_token})
    resp = request.urlopen(req)
    ret = json.loads(resp.read())
    return ret

def get_event_definitions(api_url, auth_token):
    params = urllib.parse.urlencode({'Type': 0})
    url = APIURL + "/EventDefinition?" + params
    # url = "{apiurl}/Session/GetSession/".format(apiurl=APIURL)
    # data = parse.urlencode({"username": SPICA_USER, "password": SPICA_PASSWD, sid:''})
    req = request.Request(url, headers={"Authorization": auth_token})
    resp = request.urlopen(req)
    ret = json.loads(resp.read())
    return ret


def put_time_event(api_url, auth_token, timestamp, person_id, event_id,
                   kadrovska, commit=False, spica_names={}):
    print(timestamp, kadrovska, spica_names.get(person_id, person_id), event_id, commit)
    if not commit:
        return
    params = urllib.parse.urlencode({'SkipHolidays': False, 'numberOfDays': 1,
        'SkipWeekend1': False, "SkipWeekend2": False})
    url = api_url + "/TimeEvent?" + params
    data = {
        "UserId": person_id,
        "DateTime": timestamp.isoformat(),
        "Type": 4,
        "EventDefinitionId": event_id,
        "Authentic": True,
        # "AdditionalData": "numeric, end time of intervention which requires From - To parameters, as number of minutes since midnight",
        "TimeStamp": timestamp.isoformat(),
        "Comment": "Siemens FRI/FKKT",
        # "Origin": 7, # Always set to 7 (Time API)
        # "Location": "ID of a legacy reader. If the entry should not be indicated as originating from a HW point, leave it as null",
        # "CustomField1URL": "custom text",
        # "CustomField1Text": "custom text",
        # "Longitude": 42,
        # "Latitude": 42,
    }
    
    req = request.Request(url, method='PUT',
            headers={"Authorization": auth_token},
            data=urllib.parse.urlencode(data).encode())
    resp = request.urlopen(req)
    ret = json.loads(resp.read())
    return ret


def get_spicaids(employees):
    kadrovska_to_spica = dict()
    spica_to_name = dict()
    for employee in employees:
        spica_id = employee["Id"]
        kadrovska = employee["ReferenceId"]
        if employee.get('OrganizationalUnitId', '') is not None:
            kadrovska_to_spica[kadrovska] = spica_id
            spica_to_name[spica_id] = employee["FirstName"] + " " + employee["LastName"]
    return kadrovska_to_spica, spica_to_name


def __ends_with_1(fname):
    try:
        with open(fname, 'rb') as f:
            f.seek(-2, 2)
            d = f.read().decode("utf-8").strip()
            if d[-1] == "1":
                return True
    except Exception as e:
        # print(e)
        pass
    return False


def handle_events(spooldir, api_url, auth_token, 
        spica_ids, spica_names, event_translations,
        skip_last, no_skip_same=True, commit=False):
    for kadrovska in os.listdir(spooldir):
        spoolname = os.path.join(spooldir, kadrovska, SPOOL_FNAME)
        nocommitname = os.path.join(spooldir, kadrovska, NOCOMMIT_FNAME)
        if commit:
            eventsname = os.path.join(spooldir, kadrovska, OLDEVENTS_FNAME)
        else:
            eventsname = os.path.join(spooldir, kadrovska, FAKEEVENTS_FNAME)
        if os.path.isfile(spoolname):
            with open(spoolname, "r+") as spoolfile,\
                    open(eventsname, "a") as eventsfile:
                fcntl.lockf(spoolfile, fcntl.LOCK_EX)
                fcntl.lockf(eventsfile, fcntl.LOCK_EX)
                something_failed = False
                try:
                    spica_id = spica_ids[kadrovska]
                    reader = csv.reader(spoolfile, delimiter=',', quotechar='"')
                    writer = csv.writer(eventsfile)
                    rows = sorted(list(reader))
                    if skip_last:
                        rows = rows[:-1]
                    old_event_type = None
                    for row in rows:
                        timestamp = datetime.datetime.fromisoformat(row[0])
                        event_type = event_translations[row[1]]
                        if (event_type != old_event_type) or no_skip_same:
                            commit_this = commit and not __ends_with_1(nocommitname)
                            # print(commit_this, __ends_with_1(nocommitname))
                            put_time_event(api_url, auth_token, timestamp, 
                                    spica_id, event_type, kadrovska=kadrovska, 
                                    commit=commit_this,
                                    spica_names=spica_names)
                            old_event_type = event_type
                        writer.writerow(row)
                    spoolfile.truncate(0)
                except Exception as e:
                    print(e)
                    traceback.print_exc()
                    something_failed = True
                finally:
                    fcntl.lockf(spoolfile, fcntl.LOCK_UN)
                    fcntl.lockf(eventsfile, fcntl.LOCK_UN)
                    if something_failed: continue

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prenesi podatke na spico')
    parser.add_argument('--skiplast', dest='skiplast', action='store_const',
                    default=False, const=True,
                    help='Izpusti zadnji dogodek')
    parser.add_argument('--commit', dest='commit', action='store_const',
                    default=False, const=True,
                    help='Izvedi dejanski prenos podatkov')
    parser.add_argument('--spooldir', dest='spooldir', action='store',
                    default=SPOOL_DIR,
                    help='Imenik s podatki')
    parser.add_argument('--url', dest='api_url', action='store',
                    default=APIURL,
                    help='Naslov Spice')
    parser.add_argument('--noskipsame', dest='noskipsame', action='store_const',
                    default=False, const=True,
                    help='Ne preskoci zaporednih dogodkov istega tipa')
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
    auth_token = get_auth_token(args.api_url, args.api_username, args.api_password,
                                args.api_key)
    employees = get_employees(args.api_url, auth_token)
    spica_ids, spica_names = get_spicaids(employees)
    handle_events(spooldir=args.spooldir, api_url=args.api_url, auth_token=auth_token, 
                  spica_ids=spica_ids, spica_names=spica_names,
                  event_translations=EVENT_TRANSLATIONS,
                  skip_last=args.skiplast, no_skip_same=args.noskipsame,
                  commit=args.commit)
    # set_last_to = None
    # upload_events(min_t, max_t, set_last_to, skip_last=False, fake=True)
    # set_last_to = None
# ret = put_time_event(datetime.datetime.now(), person_id=256, event_id=19)
#    ret = register_event(datetime.datetime.now(), "6200271", employees = employees,
#
#        events=event_definitions)
#    print(json.dumps(ret))
    # print(json.dumps([employees, event_definitions]))

