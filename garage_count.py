#!/usr/bin/python3
import sys
import datetime
import csv

from collections import defaultdict

from urllib import parse, request
DATEFORMAT = "%m/%d/%Y"


def count_days(fnames):
    res = defaultdict(set)
    for fname in fnames:
        with open(fname, newline='', encoding='utf-16-le') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            try:
                header = reader.__next__()
                for row in reader:
                    d = datetime.datetime.strptime(row[1], DATEFORMAT).date()
                    res[row[0]].add(d)
            except:
                pass
    return res

if __name__ == '__main__':
    fnames = sys.argv[1:]
    visits = count_days(fnames)
    for kadrovska, v in visits.items():
        row = (kadrovska, str(len(v)), "; ".join([i.isoformat() for i in sorted(list(v))]))
        print(",".join(row))
