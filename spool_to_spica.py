#!/usr/bin/python3

import urllib
import json
import datetime
import csv
import glob
import os
import itertools
import argparse

from collections import defaultdict

from urllib import parse, request

from spica_api_settings import APIURL, SPICA_USER, SPICA_PASSWD, SPICA_KEY

# Ker je testno okolje povsem drugacno od produkcijskega,
# je ID dogodka kar zapecaten.

SPOOL_DIR = "/home/polz/projekti/siemens_log_examples/spool"


SPOOL_FNAME = "new_events.csv"
OLDEVENTS_FNAME = "old_events.csv"
FAKEEVENTS_FNAME = "fake_events.csv"

EVENT_TRANSLATIONS = {
    '2': 43,
    "odhod": 44,
    "malica": 45,
    "sluzbeni": 47,
    "zasebni": 48,
    "zdravnik": 70,
}


def get_employees(api_url, api_key):
    url = api_url + "/employee"
    req = request.Request(url, headers={"Authorization": "SpicaToken " + api_key})
    resp = request.urlopen(req)
    ret = json.loads(resp.read())
    return ret


def get_event_definitions():
    params = urllib.parse.urlencode({'Type': 0})
    url = APIURL + "/EventDefinition?" + params
    # url = "{apiurl}/Session/GetSession/".format(apiurl=APIURL)
    # data = parse.urlencode({"username": SPICA_USER, "password": SPICA_PASSWD, sid:''})
    req = request.Request(url, headers={"Authorization": "SpicaToken " + SPICA_KEY})
    resp = request.urlopen(req)
    ret = json.loads(resp.read())
    return ret


def put_time_event(api_url, api_key, timestamp, person_id, event_id, fake = True):
    print(timestamp, name_trans.get(person_id, person_id), event_id)
    if fake:
        # print(timestamp, person_id, event_id)
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
            headers={"Authorization": "SpicaToken " + api_key},
            data=urllib.parse.urlencode(data).encode())
    resp = request.urlopen(req)
    ret = json.loads(resp.read())
    return ret


def read_table(fileglob, trans, min_t = None, max_t = None):
    events = defaultdict(list)
    date0 = datetime.datetime.combine(datetime.date.today(), datetime.time.min) 
    t0 = datetime.timedelta(hours = 10)
    for filename in glob.glob(fileglob):
        with open(filename, newline='', encoding='utf-16-le') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            header = reader.__next__()
            # print(header)
            for row in reader:
                if row[0] not in trans: continue 
                if len(row[1]) > 0:
                    t = datetime.datetime.strptime(row[1], DATEFORMAT)
                else:
                    t = date0
                # print(t)
                if len(row[2]) > 0:
                    t += datetime.datetime.strptime(row[2], TIMEFORMAT) - \
                         datetime.datetime.strptime("00:00:00", TIMEFORMAT)
                else:
                    t += t0
                if (min_t is not None and t < min_t) or \
                   (max_t is not None and t > max_t):
                    # print(t, min_t, max_t)
                    t = None
                if t is not None:
                    # print(t, min_t, max_t)
                    events[trans[row[0]]].append([t] + row[3:])
    return events

def get_spicaids(employees):
    kadrovska_to_spica = dict()
    spica_to_name = dict()
    for kadrovska, employee in employees.items():
        spica_id = employee["Id"]
        kadrovska_to_spica[kadrovska] = spica_id
        spica_to_name[spica_id] = employee["FirstName"] + " " + employee["LastName"]
    return kadrovska_to_spica, spica_to_name

def handle_events(spooldir, api_url, api_key, 
        spica_ids, spica_names, event_translations,
        skip_last, fake):
    for kadrovska in os.listdir(spooldir):
        spoolname = os.path.join(spooldir, kadrovska, SPOOL_FNAME)
        if commit:
            eventsname = os.path.join(spooldir, kadrovska, OLDEVENTS_FNAME)
        else:
            eventsname = os.path.join(spooldir, kadrovska, FAKEEVENTS_FNAME)
        if isfile(spoolname):
            with open(spoolname, "r+") as spoolfile,\
                    open(eventsname, "a") as eventsfile:
                fcntl.lockf(spoolfile, fcntl.LOCK_EX)
                fcntl.lockf(eventsfile, fcntl.LOCK_EX)
                #TODO lock files
                something_failed = False
                try:
                    spica_id = spica_ids[kadrovska]
                    reader = csv.reader(spoolfile, delimiter=',', quotechar='"')
                    writer = csv.writer(eventsfile)
                    if skip_last:
                        reader = list(reader)[:-1]
                    for row in reader[:endpos]:
                        timestamp = datetime.datetime.fromisoformat(row[0])
                        event_type = event_translations[row[1]]
                        put_time_event(api_url, api_key, timestamp, 
                                spica_id, event_type, fake=fake)
                        writer.write(row)
                    spoolfile.truncate()
                except Exception as e:
                    print(e)
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
                    default=SPOOL_DIR, nargs=1,
                    help='Imenik s podatki')
    parser.add_argument('--url', dest='api_url', action='store',
                    default=APIURL, nargs=1,
                    help='Naslov Spice')
    parser.add_argument('--apikey', dest='api_key', action='store',
                    default=SPICA_KEY, nargs=1, type=str,
                    help='Skrivnost za dostop do Spice')
    args = parser.parse_args()
    employees = get_employees(args.api_url, args.api_key)
    spica_ids, spica_names = get_spicaids(employees)
    handle_events(spooldir=args.spooldir, api_url=args.api_url, api_key=args.api_key, 
                  spica_ids=spica_ids, spica_names=spica_names,
                  event_translations=EVENT_TRANSLATIONS,
                  skip_last=args.skip_last, fake=not args.commit)
    # set_last_to = None
    # upload_events(min_t, max_t, set_last_to, skip_last=False, fake=True)
    # set_last_to = None
# ret = put_time_event(datetime.datetime.now(), person_id=256, event_id=19)
#    ret = register_event(datetime.datetime.now(), "6200271", employees = employees,
#
#        events=event_definitions)
#    print(json.dumps(ret))
    # print(json.dumps([employees, event_definitions]))

