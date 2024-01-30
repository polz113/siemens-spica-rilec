#!/usr/bin/python3
import sys
import datetime
import csv

import glob
import os

import argparse
from collections import defaultdict

from urllib import parse, request
DATEFORMAT = "%d. %m. %Y"
# DATEFORMAT = "%d/%m/%Y"

FILENAMEFORMAT = "garage-access(%Y-%m-%d *).csv"

OUT_FUNCTIONS = dict()

def fri_calculation(days):
    return min(days * 0.5, 8.0)

def is_employee(ks):
    return ks.startswith('023')

# register output
try:
    import csv
    def write_csv(l, outfname):
        with open(outfname, 'w') as outfile:
            writer = csv.writer(outfile)
            writer.writerows(l)
    OUT_FUNCTIONS['csv'] = write_csv
except:
    pass

try:
    import openpyxl
    def write_xlsx(l, outfname):
        wb = openpyxl.workbook.Workbook()
        ws = wb.active
        for i in l:
            ws.append(i)
        wb.save(outfname)
    OUT_FUNCTIONS['xlsx'] = write_xlsx
except Exception as e:
    print(e)
    pass

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
    parser.add_argument('-c', '--calculation', dest='fri_calculation', action='store_true',
                    help='V .xlsx dodaj izracun parkirnine po pravilih FRI')
    parser.add_argument('-m', '--employees', dest='employees_only', action='store_true',
                    help='Filtriraj - samo veljavne kadrovske')
    parser.add_argument('-f', '--format', dest='out_format', action='store',
                    default="csv",
                    help='Format izhodne datoteke; podprti: ' + ",".join(OUT_FUNCTIONS.keys()))
    parser.add_argument('dirname', action='store',
                    help='Imenik z log datotekami')
    parser.add_argument('outfile', action='store',
                    help='Izhodna datoteka; {start} se nadomesti z zacetnim, {end} s koncnim datumom')
    args = parser.parse_args()
    dirname = args.dirname
    start_date = datetime.date.fromisoformat(args.start)
    end_date = datetime.date.fromisoformat(args.end)
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
    l = []
    l.append(('Kadrovska številka', 
              'Priimek in ime', 
              'Davčna številka', 
              'Zač. velj.', 
              'Znesek', 
              'Št. Obr.', 
              'Saldo', 
              'Model', 
              'Sklic'))
    for kadrovska, v in visits.items():
        if args.show_dates:
            visit_dates = "; ".join([i.isoformat() for i in sorted(list(v))])
        else:
            visit_dates = ""
        if args.fri_calculation:
            calc_result = fri_calculation(len(v))
        else:
            calc_result = ""
        if args.employees_only and not is_employee(kadrovska):
            continue
        # TULE NAPOLNIMO TABELO
        row = (kadrovska, 
               '', # priimek in ime 
               '', # davcna
               start_date.strftime("%m/%d/%Y"),
               calc_result, # znesek
               str(len(v)), # st. obr.
               0.0, # saldo
               99, # model
               '',
               visit_dates) # sklic
        l.append(row)
    outfname = args.outfile.format(**{'start': start_date.isoformat(), 
                'end': end_date.isoformat()})
    OUT_FUNCTIONS[args.out_format](l, outfname)
