#!/usr/bin/env python3

import os
import fcntl
import glob
import csv
import datetime
import sys
from collections import defaultdict

from siemens_spica_settings import LOG_GLOB, OLD_LOG_LIST, SPOOL_DIR, SPOOL_FNAME,\
        OLDEVENTS_FNAME

TIMEFORMAT = "%H:%M:%S"
DATEFORMAT = "%m/%d/%Y"


def read_log_events(events_by_id, logfname):
    row_n = 0
    try:
        with open(logfname, newline='', encoding='utf-16-le') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            header = reader.__next__()
            for row in reader:
                row_n += 1
                if len(row[0]) == 0:
                    continue
                t = datetime.datetime.strptime(row[1], DATEFORMAT)
                t += datetime.datetime.strptime(row[2], TIMEFORMAT) - \
                     datetime.datetime.strptime("00:00:00", TIMEFORMAT)
                events_by_id[row[0]].append([t, row[3]])
        return True
    except Exception as e:
        print(logfname, file=sys.stderr)
        print("  ", row_n, file=sys.stderr)
        print(e, file=sys.stderr)
        return False
    # print(events_by_id)


def read_spool_events(spoolfile):
    spoolfile.seek(0)
    events = dict()
    reader = csv.reader(spoolfile, delimiter=',', quotechar='"')
    for row in reader:
        t = datetime.datetime.fromisoformat(row[0])
        events[t] = row[1]
    return events


def siemens_to_spool(log_glob, spool_dir, old_log_list):
    logs = set(glob.glob(log_glob))
    with open(old_log_list, "a+") as oldlogs_file:
        fcntl.lockf(oldlogs_file, fcntl.LOCK_EX)
        oldlogs_file.seek(0)
        old_logs = set(oldlogs_file.read().splitlines())
        events_by_id = defaultdict(list)
        done_logs = set()
        error_logs = set()
        for logfname in logs - old_logs:
            if (read_log_events(events_by_id, logfname)):
                done_logs.add(logfname)
        for employee_id, log_events in events_by_id.items():
            # print(employee_id)
            spool_dirname = os.path.join(spool_dir, employee_id)
            spool_fname = os.path.join(spool_dirname, SPOOL_FNAME)
            oldevents_fname = os.path.join(spool_dirname, OLDEVENTS_FNAME)
            if not os.path.isdir(spool_dirname):
                os.mkdir(spool_dirname)
            with open(spool_fname, "a+") as spoolfile, open(oldevents_fname, "a+") as oldfile:
                fcntl.lockf(spoolfile, fcntl.LOCK_EX)
                fcntl.lockf(oldfile, fcntl.LOCK_EX)
                events = read_spool_events(spoolfile)
                old_events = read_spool_events(oldfile)
                # TODO: read older events from spica log files
                new_events = dict()
                for ev in log_events:
                    ev_t = ev[0]
                    if not (ev_t in events) and not (ev_t in old_events):
                        new_events[ev[0]] = ev[1]
                new_events.update(events)
                new_events = sorted([[k, v] for k, v in new_events.items()])
                spoolfile.seek(0)
                spoolfile.truncate(0)
                writer = csv.writer(spoolfile, delimiter=',', quotechar='"')
                writer.writerows(new_events)
                fcntl.lockf(spoolfile, fcntl.LOCK_UN)
                fcntl.lockf(oldfile, fcntl.LOCK_UN)
        oldlogs_file.seek(0, 2) # seek to end of file
        oldlogs_file.writelines("%s\n" % i for i in done_logs)
        fcntl.lockf(oldlogs_file, fcntl.LOCK_UN)
        


if __name__ == '__main__':
    # read list of files
    siemens_to_spool(LOG_GLOB, SPOOL_DIR, OLD_LOG_LIST)
