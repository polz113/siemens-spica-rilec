#!/usr/bin/python3
import sys
import datetime
import csv

import glob

import argparse
from collections import defaultdict

from urllib import parse, request
DATEFORMAT = "%m/%d/%Y"

FILENAMEFORMAT = "room-access(%Y-%m-%d .*).csv"

def count_days(fnames, start_date = None, end_date = None):
    res = defaultdict(set)
    for fname in fnames:
        with open(fname, newline='', encoding='utf-16-le') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            try:
                header = reader.__next__()
                for row in reader:
                    d = datetime.datetime.strptime(row[1], DATEFORMAT).date()
                    if (start_date is not None and d < start_date) or \
                            (end_date is not None and d > end_date):
                        continue
                    res[row[0]].add(d)
            except:
                pass
    return res

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Izvozi podatke za garazo')
    today = datetime.datetime.now().date()
    end_of_prev_month = today - datetime.timedelta(days = today.day)
    start_of_prev_month = end_of_prev_month - datetime.timedelta(days = end_of_prev_month.day - 1)
    parser.add_argument('--start', dest='start', action='store',
                    default=start_of_prev_month.isoformat(),
                    help='Zacetni datum; privzeto zacetek preteklega meseca; oblike 2000-03-25')
    default_end = today
    parser.add_argument('--end', dest='end', action='store',
                    default=end_of_prev_month.isoformat(),
                    help='Koncni datum; privzeto konec preteklega meseca; oblike 2010-01-22')
    parser.add_argument('dirname', action='store',
                    help='Imenik z log datotekami')
    args = parser.parse_args()
    dirname = args.dirname
    start_date = datetime.date.fromisoformat(args.start)
    end_date = datetime.date.fromisoformat(args.end)
    globs = []
    i = start_date
    while i <= end_date:
        globs.append(i.strftime(FILENAMEFORMAT))
        i += datetime.timedelta(days=1)
    print(dirname, start_date, end_date)
    print(globs)
    fnames = []
    for g in globs:
        fnames += glob.glob(g)
    print(fnames)
    visits = count_days(fnames, start_date, end_date)
    for kadrovska, v in visits.items():
        row = (kadrovska, str(len(v)), "; ".join([i.isoformat() for i in sorted(list(v))]))
        print(",".join(row))
