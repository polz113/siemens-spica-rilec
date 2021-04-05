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

EVENT_GLOB = "/home/apis/siemens_logs/room-access*.csv"
TYPE_FIX_GLOB = "/home/apis/registrator/logs/registratorLog.csv"

TIMEFORMAT = "%H:%M:%S"
DATEFORMAT = "%m/%d/%Y"

REGISTRATION_EVENT_ID = 43
LEAVE_EVENT_ID = 44

EVENT_TRANSLATIONS = {
    '2': 43,
    "odhod": 44,
    "malica": 45,
    "sluzbeni": 47,
    "zasebni": 48,
    "zdravnik": 70,
}

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
        if len(key) == 0: continue
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


def put_time_event(timestamp, person_id, event_id, name_trans = dict(), fake = True):
    print(timestamp, name_trans.get(person_id, person_id), event_id)
    if fake:
        # print(timestamp, person_id, event_id)
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

def read_type_fixes(trans, min_t, max_t):
    return read_table(TYPE_FIX_GLOB, trans, min_t, max_t)

def read_events(trans, min_t, max_t):
    return read_table(EVENT_GLOB, trans, min_t, max_t)

def fix_events(events, fixes, evt_dict, set_last_to=None, skip_last=False):
    res = dict()
    for spica_id, event_list in events.items():
        if len(event_list) < 1: continue
        print("ID", spica_id)
        # print("k2ul:", spica_id_to_ulid, kadrovska)
        fix_list = fixes.get(spica_id, [])
        fix_list = sorted(fix_list, key= lambda x: x[:1])
        event_list = sorted(event_list, key= lambda x: x[:1])
        if set_last_to != None and len(event_list) > 1:
            event_list[-1][1] = set_last_to
        if skip_last:
            i = len(event_list)-1
            last_t = event_list[i][0]
            while i > 1 and event_list[i][0] == last_t:
                i -= 1
            event_list = event_list[:i]
        fix_i = 0
        event_i = 0
        while fix_i < len(fix_list) and event_i < len(event_list):
            event_t = event_list[event_i][0]
            fix_t = fix_list[fix_i][0]
            target_i = None
            fixed_type = None
            # find last event before fix_t
            while event_i < len(event_list) and event_t < fix_t:
                target_t = event_t
                target_i = event_i
                event_i += 1
                event_t = event_list[event_i][0]
            # print(fix_i, target_i, fix_t, target_t)
            while target_i < len(event_list) and \
                    target_t == event_list[event_i][0]:
                target_t = event_t
                target_i = event_i
                event_i += 1
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
        # print("el:", json.dumps([(str(i[0]), i[1]) for i in event_list], indent=4))
        # print("    el:", [ (str(i[0]), i[1]) for i in event_list ])
        for i, (timestamp, event_type) in enumerate(event_list):
            if i+1 < len(event_list) and event_list[i+1][0] == timestamp: continue
            if old_type != event_type:
                latest_events.append([timestamp, evt_dict[event_type]])
            old_type = event_type
        res[spica_id] = latest_events
    return res

def get_spicaids(employees):
    kadrovska_to_spica = dict()
    spica_to_name = dict()
    for kadrovska, employee in employees.items():
        spica_id = employee["Id"]
        kadrovska_to_spica[kadrovska] = spica_id
        spica_to_name[spica_id] = employee["FirstName"] + " " + employee["LastName"]
    return kadrovska_to_spica, spica_to_name

def upload_events(min_t=None, max_t=None, set_last_to=None, skip_last=False, fake=True):
    ulid_to_kadrovska, new_to_old = get_trans_dicts()
    employees = get_employees_dict(new_to_old)
    # print(json.dumps(employees, indent=4))
    spica_ids, spica_names = get_spicaids(employees)
    ulid_to_spica = dict()
    for k, v in ulid_to_kadrovska.items():
        spica_id = spica_ids.get(v, None)
        if spica_id is not None:
            ulid_to_spica[k] = spica_id
    # print (spica_ids)
    # print(ulid_to_spica)
    events = read_events(spica_ids, min_t, max_t)
    fixes = read_type_fixes(ulid_to_spica, min_t, max_t)
    events = fix_events(events, fixes, evt_dict=EVENT_TRANSLATIONS, 
        set_last_to=set_last_to, skip_last=skip_last)
    # print(employees)
    event_definitions = get_event_definitions()
    # print(json.dumps(event_definitions, indent=4))
    for spica_id, event_list in events.items():
        try:
            for timestamp, event_type in event_list:
                # print("    ", timestamp, event_type)
                put_time_event(timestamp, spica_id, event_type, name_trans = spica_names, fake=fake)
        except KeyError:
            print("Neznan uporabnik:", employee_id)
            # print(employees)
            continue


if __name__ == '__main__':
    set_last_to = "odhod"
    # set_last_to = None
    min_t = datetime.datetime.now()
    min_t = min_t.combine(min_t.date(), datetime.time(0))
    max_t = datetime.datetime.now() - datetime.timedelta(minutes=30)
    upload_events(min_t, max_t, set_last_to, skip_last=False, fake=False)
    # set_last_to = None
# ret = put_time_event(datetime.datetime.now(), person_id=256, event_id=19)
#    ret = register_event(datetime.datetime.now(), "6200271", employees = employees,
#
#        events=event_definitions)
#    print(json.dumps(ret))
    # print(json.dumps([employees, event_definitions]))

