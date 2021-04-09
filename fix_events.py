#!/usr/bin/env python3

import argparse
import csv
import datetime
import os

from collections import defaultdict

from siemens_spica_settings import SPOOL_DIR, ULID_SPOOL_DIR, SPOOL_FNAME

TIMEFORMAT = "%H:%M:%S"
DATEFORMAT = "%m/%d/%Y"

FIXED_FNAME = "fixed_events.csv"
FIXES_FNAME = "fixes.csv"
OLDFIXES_FNAME = "old_fixes.csv"

OLD_TRANSLATION_FNAME = "preslikava_kadrovskih.csv"


def create_new_fixes(fixfname, spooldir):
    events = defaultdict(list)
    with open(fixfname, encoding='utf-16-le') as fixfile:
        reader = csv.reader(fixfile, delimiter=',', quotechar='"')
        header = reader.__next__()
        for row in reader:
            t = datetime.datetime.strptime(row[1], DATEFORMAT)
            t += datetime.datetime.strptime(row[2], TIMEFORMAT) - \
                 datetime.datetime.strptime("00:00:00", TIMEFORMAT)
            events[row[0]].append([t, row[3]])
    for k, v in events.items():
        fixdirname = os.path.join(spooldir, k)
        newfixname = os.path.join(fixdirname, FIXES_FNAME)
        if not os.path.isdir(fixdirname):
            os.mkdir(fixdirname)
        with open(newfixname, "a") as newfixfile:
            writer = csv.writer(newfixfile, delimiter=',', quotechar='"')
            writer.writerows(sorted([[i[0].isoformat(), i[1]] for i in v]))


def __read_eventfile(f):
    reader = csv.reader(f, delimiter=',', quotechar='"')
    return sorted(
        [
            [datetime.datetime.fromisoformat(i[0]), i[1]
        ] for i in reader])


def fix_events(spooldir):
    for kadrovska in os.listdir(spooldir):
        spoolname = os.path.join(spooldir, kadrovska, SPOOL_FNAME)
        fixedname = os.path.join(spooldir, kadrovska, FIXED_FNAME)
        fixname = os.path.join(spooldir, kadrovska, FIXES_FNAME)
        oldfixname = os.path.join(spooldir, kadrovska, OLDFIXES_FNAME)
        if not os.path.isfile(spoolname) or not os.path.isfile(fixname):
            continue
        with open(spoolname, "r") as spoolfile,\
                open(fixname, "r") as fixfile,\
                open(fixedname, "w") as fixedfile:
            events = __read_eventfile(spoolfile)
            fixes = __read_eventfile(fixfile)
            fixed = csv.writer(fixedfile, delimiter=',', quotechar='"')
            if len(fixes) == 0:
                continue
            fix_i = 0
            event_i = 0
            target_i = None
            while fix_i < len(fixes) and event_i < len(events):
                fix_t, fixed_type = fixes[fix_i]
                # print(fix_t, fixed_type)
                event_t = events[event_i][0]
                while event_t is not None and event_t < fix_t:
                    target_t = event_t
                    target_i = event_i
                    event_i += 1
                    if event_i < len(events):
                        event_t = events[event_i][0]
                    else:
                        event_t = None
                # print("  ", target_t, target_i, fixed_type)
                while fix_i < len(fixes) and (event_t is None or event_t >= fixes[fix_i][0]):
                    fixed_type = fixes[fix_i][1]
                    fix_i += 1
                # print("  ", target_t, target_i, fix_t, fixed_type)
                if (target_i is not None) and (fixed_type is not None):
                    events[target_i][1] = fixed_type
            fixed.writerows(events)
        os.rename(fixedname, spoolname)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Popravi tip podatkov')
    parser.add_argument('--spooldir', dest='spooldir', action='store', type=str,
                    default=SPOOL_DIR,
                    help='Imenik s podatki')
    parser.add_argument('--oldfixes', dest='oldfixes', action='store',
                    default=None, type=str,
                    help='Beri popravke iz starinske datoteke')
    args = parser.parse_args()
    if not args.oldfixes is None:
        create_new_fixes(args.oldfixes, ULID_SPOOL_DIR)
    fix_events(spooldir=args.spooldir)
