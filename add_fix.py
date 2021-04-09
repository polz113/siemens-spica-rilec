#!/usr/bin/env python3

import datetime
import argparse
import csv
import os

from siemens_spica_settings import SPOOL_DIR, ULID_SPOOL_DIR, FIX_FNAME

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prenesi podatke na spico')
    parser.add_argument('--time', dest='time', action='store',
                    default=datetime.datetime.now().isoformat(),
                    help='Timestamp')
    parser.add_argument('--type', dest='type', action='store', type=str,
                    default='2',
                    help='Tip dogodka')
    parser.add_argument('files', metavar='files',
                    type=str, nargs="+",
                    help='datoteke s popravki')
    args = parser.parse_args()
    t = datetime.datetime.fromisoformat(args.time)
    for fname in args.files:
        with open(fname, "a") as f:
            writer = csv.writer(f, delimiter=',', quotechar='"')
            writer.writerow([t.isoformat(), args.type])
