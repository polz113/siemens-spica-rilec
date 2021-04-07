#!/usr/bin/env python3

import argparse
import csv
import datetime
import os

from collections import defaultdict

from siemens_spica_settings import SPOOL_DIR, SPOOL_FNAME

TIMEFORMAT = "%H:%M:%S"
DATEFORMAT = "%m/%d/%Y"

FIXED_FNAME = "fixed_events.csv"
FIXES_FNAME = "fixes.csv"
OLDFIXES_FNAME = "old_fixes.csv"

OLD_TRANSLATION_FNAME = "preslikava_kadrovskih.csv"

def create_new_fixes(fixfname, spooldir):
    events = defaultdict(list)
    with open(fixfname) as fixfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        header = reader.__next__()
        for row in reader:
            t = datetime.datetime.strptime(row[1], DATEFORMAT)
            t += datetime.datetime.strptime(row[2], TIMEFORMAT) - \
                 datetime.datetime.strptime("00:00:00", TIMEFORMAT)
            events[row[0]].append([t, row[3]])
    for k, v in events.items():
        fixdirname = os.path.join(spooldir, k)
        newfixname = os.path.join(fixdirname, FIXES_FNAME)
        if not os.isdir(fixdirname):
            os.mkdir(fixdirname)
        with open(newfixname, "a") as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"')
            for i in v:
                writer.write(i[0].isoformat(), i[1])


def fix_events(spooldir, set_last_to=None):
    for kadrovska in os.listdir(spooldir):
        spoolname = os.path.join(spooldir, kadrovska, SPOOL_FNAME)
        fixedname = spoolname = os.path.join(spooldir, kadrovska, FIXED_FNAME)
        fixname = spoolname = os.path.join(spooldir, kadrovska, FIXES_FNAME)
        oldfixname = os.path.join(spooldir, kadrovska, OLDFIXES_FNAME)
        if not os.path.isfile(spoolname) or not os.path.isfile(fixname):
            continue
        with open(spoolname, "r") as spoolfile,\
                open(fixname, "r") as fixfile,\
                open(fixedname, "w") as fixedfile:
            events = list(csv.reader(spoolfile, delimiter=',', quotechar='"'))
            fixes = list(csv.reader(fixfile, delimiter=',', quotechar='"'))
            fixed = csv.writer(fixedfile, delimiter=',', quotechar='"')
            if set_last_to is not None:
                events[-1][1] = set_last_to
            fix_i = 0
            event_i = 0
            while fix_i < len(fixes) and event_i < len(events):
                fix_t = datetime.datetime.fromisoformat(fixes[fix_i][0])
                event_t = datetime.datetime.fromisoformat(events[event_i][0])
                while event_i < len(events) and event_t < fix_t:
                    target_t = event_t
                    target_i = event_i
                    event_i += 1
                    event_t = datetime.datetime.fromisoformat(events[event_i][0])
                while fix_i < len(fixes) and (event_i >= len(event_list) or event_t >= fix_t):
                    fixed_type = fixes[fix_i][1]
                    fix_t = datetime.datetime.fromisoformat(fixes[fix_i][0])
                    fix_i += 1
                if (target_i is not None) and (fixed_type is not None):
                    events[target_i][1] = fixed_type
            fixed.write(events)
        os.rename(fixedname, spoolname)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Popravi tip podatkov')
    parser.add_argument('--spooldir', dest='spooldir', action='store',
                    default=SPOOL_DIR, nargs=1,
                    help='Imenik s podatki')
    parser.add_argument('--setlast', dest='set_last_to', action='store',
                    default=None, nargs=1, type=str,
                    help='Nastavi zadnji dogodek na')
    parser.add_argument('--oldfixes', dest='oldfixes', action='store',
                    default=None, nargs=1, type=str,
                    help='Beri popravke iz starinske datoteke')
    args = parser.parse_args()
    if not args.oldfixes is None:
        create_new_fixes(args.oldfixes, args.spooldir)
    fix_events(spooldir=args.spooldir,
                set_last_to=args.set_last_to)
