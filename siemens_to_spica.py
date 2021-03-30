#!/usr/bin/python3

import urllib
import json
import datetime
import csv
import glob
import os
import itertools

from collections import defaultdict

from urllib import parse, request

from spica_api_settings import APIURL, SPICA_USER, SPICA_PASSWD, SPICA_KEY

# Ker je testno okolje povsem drugacno od produkcijskega,
# je ID dogodka kar zapecaten.
ID_REMAP_FILE = "preslikava_kadrovskih.csv"

REGISTRATION_EVENT_ID = 19

def get_employees():
    url = APIURL + "/employee"
    req = request.Request(url, headers={"Authorization": "SpicaToken " + SPICA_KEY})
    resp = request.urlopen(req)
    ret = json.loads(resp.read())
    return ret


def get_employees_dict():
    employee_list = get_employees()
    d = dict()
    trans_dict = dict()
    try:
        with open(ID_REMAP_FILE) as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in reader:
                trans_dict[row[1]] = row[0]
    except:
        pass
    print("TRANS:", trans_dict)
    for e in employee_list:
        key = e['ReferenceId']
        print(trans_dict.get(key, key), "->", key)
        d[trans_dict.get(key, key)] = e
    return d


def get_event_definitions():
    params = urllib.parse.urlencode({'Type': 0})
    url = APIURL + "/EventDefinition?" + params
    # url = "{apiurl}/Session/GetSession/".format(apiurl=APIURL)
    # data = parse.urlencode({"username": SPICA_USER, "password": SPICA_PASSWD, sid:''})
    req = request.Request(url, headers={"Authorization": "SpicaToken " + SPICA_KEY})
    resp = request.urlopen(req)
    ret = json.loads(resp.read())
    return ret


def put_time_event(timestamp, person_id, event_id): 
    params = urllib.parse.urlencode({'SkipHolidays': False, 'numberOfDays': 1,
        'SkipWeekend1': False, "SkipWeekend2": False})
    url = APIURL + "/TimeEvent?" + params
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
            headers={"Authorization": "SpicaToken " + SPICA_KEY},
            data=urllib.parse.urlencode(data).encode())
    resp = request.urlopen(req)
    ret = json.loads(resp.read())
    return ret


def register_event(timestamp, employee, events = None):
    """
    if events is None:
        events = get_event_definitions()
    event_id = 
    for e in events:
        if e["ShortName"] == "PRI":
            event_id = e["Id"]
            break"""
    event_id = REGISTRATION_EVENT_ID
    return put_time_event(timestamp, employee["Id"], event_id)


def read_events(dirname):
    events = defaultdict(list)
    srcglob = os.path.join(dirname, "room-access*.csv")
    typefixglob = os.path.join(dirname, "fix-event-type*.csv")
    for filename in glob.glob(srcglob):
        with open(filename, newline='', encoding='utf-16-le') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            header = reader.__next__()
            # print(header)
            for row in reader:
                # print(row)
                events[row[0]].append(datetime.datetime.strptime(row[1], "%m/%d/%Y"))
    for filename in glob.glob(srcglob):
    return events

    

if __name__ == '__main__':
    events = read_events("samples")
    employees = get_employees_dict()
    # print(employees)
    # event_definitions = get_event_definitions()
    for employee_id, timestamps in events.items():
        try:
            employee = employees[employee_id]
            print(employee_id, employee)
            for timestamp in set(timestamps):
                print("    ", timestamp)
                register_event(timestamp, employee)
        except KeyError:
            print("Neznan uporabnik:", employee)
            continue
# ret = put_time_event(datetime.datetime.now(), person_id=256, event_id=19)
#    ret = register_event(datetime.datetime.now(), "6200271", employees = employees,
#
#        events=event_definitions)
#    print(json.dumps(ret))
    # print(json.dumps([employees, event_definitions]))

