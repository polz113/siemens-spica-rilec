#!/usr/bin/python3
import sys
import datetime
import csv

import glob
import os

import argparse
from collections import defaultdict

from urllib import parse, request
DATEFORMAT = "%m/%d/%Y"

FILENAMEFORMAT = "garage-access(%Y-%m-%d *).csv"

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
    parser.add_argument('-s', '--start', dest='start', action='store',
                    default=start_of_prev_month.isoformat(),
                    help='Zacetni datum; privzeto zacetek preteklega meseca; oblike 2000-03-25')
    default_end = today
    parser.add_argument('-e', '--end', dest='end', action='store',
                    default=end_of_prev_month.isoformat(),
                    help='Koncni datum; privzeto konec preteklega meseca; oblike 2010-01-22')
    parser.add_argument('-d', '--dates', dest='show_dates', action='store_true',
                    help='Izpisi tudi datume, ko je bil zaposleni na FRI')
    parser.add_argument('dirname', action='store',
                    help='Imenik z log datotekami')
    args = parser.parse_args()
    dirname = args.dirname
    start_date = datetime.date.fromisoformat(args.start)
    end_date = datetime.date.fromisoformat(args.end)
    show_dates = args.show_dates
    globs = []
    i = start_date
    while i <= end_date:
        globs.append(os.path.join(dirname, i.strftime(FILENAMEFORMAT)))
        i += datetime.timedelta(days=1)
#    print(dirname, start_date, end_date)
#    print(globs)
    fnames = []
    for g in globs:
        fnames += glob.glob(g)
#    print(fnames)
    visits = count_days(fnames, start_date, end_date)
    for kadrovska, v in visits.items():
        if show_dates:
            visit_dates = "; ".join([i.isoformat() for i in sorted(list(v))])
        else:
            visit_dates = ""
        row = (kadrovska, str(len(v)), visit_dates)
        print(",".join(row))
