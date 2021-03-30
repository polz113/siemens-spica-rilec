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

REGISTRATION_EVENT_ID = 25

def get_employees():
    url = APIURL + "/employee"
    req = request.Request(url, headers={"Authorization": "SpicaToken " + SPICA_KEY})
    resp = request.urlopen(req)
    ret = json.loads(resp.read())
    return ret

def get_trans_dicts():
    ulid_to_kadrovska = dict()
    new_to_old_kadrovska = dict()
    try:
        with open(ID_REMAP_FILE) as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in reader:
                if len(row[2]):
                    new_to_old_kadrovska[row[1]] = row[2]
                if len(row[0]):
                    ulid_to_kadrovska[row[0]] = row[1]
    except:
        pass
    return ulid_to_kadrovska, new_to_old_kadrovska

def get_employees_dict(trans_dict):
    employee_list = get_employees()
    # print("TRANS:", new_to_old_kadrovska)
    d = dict()
    for e in employee_list:
        key = e['ReferenceId']
        # print(old_to_new_kadrovska.get(key, key), "->", key)
        d[key] = e
        if key in trans_dict:
            # print("d:", key, trans_dict[key])
            d[trans_dict[key]] = e
    # print(json.dumps(d, indent=4))
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


def put_time_event(timestamp, person_id, event_id, fake = False):
    if fake:
        print(timestamp, person_id, event_id)
        return
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


def read_table(fileglob, timeformat, timeoffset = None, trans=dict()):
    if timeoffset is None:
        timeoffset = datetime.timedelta()
    events = defaultdict(list)
    for filename in glob.glob(fileglob):
        with open(filename, newline='', encoding='utf-16-le') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            header = reader.__next__()
            # print(header)
            for row in reader:
                # print(row)
                t = datetime.datetime.strptime(row[1], timeformat) + timeoffset
                events[trans.get(row[0], row[0])].append([t] + row[2:])
    return events

def read_type_fixes(dirname, trans):
    typefixglob = os.path.join(dirname, "event-fix*.csv")
    t = datetime.datetime.combine(datetime.date.today(), datetime.time.min) 
    t = t - datetime.datetime.strptime("00:00:00", "%H:%M:%S")
    return read_table(typefixglob, "%H:%M:%S", t, trans)

def read_events(dirname, trans):
    srcglob = os.path.join(dirname, "room-access*.csv")
    t = datetime.timedelta(hours = 10)
    return read_table(srcglob, "%m/%d/%Y", t, trans)

def fix_events(events, fixes):
    res = dict()
    for spica_id, event_list in events.items():
        # print("list:", event_list)
        if len(event_list) < 1: continue
        # print("k2ul:", spica_id_to_ulid, kadrovska)
        fix_list = fixes.get(spica_id, [])
        # print("  fixes:", fix_list)
        fix_list = sorted(fix_list, key= lambda x: x[:0])
        event_list = sorted(event_list, key= lambda x: x[:0])
        fix_i = 0
        event_i = 0
        while fix_i < len(fix_list) and event_i < len(event_list):
            event_t = event_list[event_i][0]
            fix_t = fix_list[fix_i][0]
            target_i = None
            fixed_type = None
            # find last event before fix_t
            while event_i < len(event_list) and event_t < fix_t:
                event_t = event_list[event_i][0]
                target_t = event_t
                target_i = event_i
                event_i += 1
            # print(fix_i, target_i)
            # the last event timestamp and index are now in target_t/i
            # find last fix before the target event
            while fix_i < len(fix_list) and (event_i >= len(event_list) or event_t >= fix_t):
                fixed_type = fix_list[fix_i][1]
                fix_t = fix_list[fix_i][0]
                fix_i += 1
            # print("final:", target_i, fixed_type)
            # fixed_type now contains the last type before the next event
            if (target_i is not None) and (fixed_type is not None):
                event_list[target_i] = [target_t, fixed_type]
        latest_events = []
        old_type = None
        old_timestamp = event_list[0][0]
        # remove consecutive events if the type is the same.
        # print("el:", event_list)
        for i, (timestamp, event_type) in enumerate(event_list):
            if i+1 < len(event_list) and event_list[i+1][0] == timestamp: continue
            if old_type != event_type:
                latest_events.append([timestamp, event_type])
            old_type = event_type
        res[spica_id] = latest_events
    return res

def get_spicaids(employees):
    res = dict()
    for kadrovska, employee in employees.items():
        spica_id = employee["Id"]
        res[kadrovska] = spica_id
    return res

if __name__ == '__main__':
    ulid_to_kadrovska, new_to_old = get_trans_dicts()
    employees = get_employees_dict(new_to_old)
    spica_ids = get_spicaids(employees)
    ulid_to_spica = dict()
    for k, v in ulid_to_kadrovska.items():
        spica_id = spica_ids.get(v, None)
        if spica_id is not None:
            ulid_to_spica[k] = spica_id
    # print (spica_ids)
    events = read_events("samples", spica_ids)
    fixes = read_type_fixes("samples", ulid_to_spica)
    events = fix_events(events, fixes)
    # print(employees)
    event_definitions = get_event_definitions()
    # print(event_definitions)
    for spica_id, event_list in events.items():
        try:
            for timestamp, event_type in event_list:
                # print("    ", timestamp, event_type)
                put_time_event(timestamp, spica_id, event_type, fake=True)
        except KeyError:
            print("Neznan uporabnik:", employee_id)
            # print(employees)
            continue
# ret = put_time_event(datetime.datetime.now(), person_id=256, event_id=19)
#    ret = register_event(datetime.datetime.now(), "6200271", employees = employees,
#
#        events=event_definitions)
#    print(json.dumps(ret))
    # print(json.dumps([employees, event_definitions]))

