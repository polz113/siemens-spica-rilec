#!/usr/bin/env python3

import argparse
import csv
import os

from siemens_spica_settings import SPOOL_DIR

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prenesi podatke na spico')
    parser.add_argument('--spooldir', dest='spooldir', action='store',
                    default=SPOOL_DIR, nargs=1,
                    help='Glavni imenik s podatki')
    parser.add_argument('--ulidspooldir', dest='ulidspooldir', action='store',
                    default=SPOOL_DIR, nargs=1, type=str,
                    help='Imenik za web server')
    parser.add_argument('--file', dest='file', action='store',
                    default=None, nargs=1, type=str,
                    help='Datoteka za prevod')
    args = parser.parse_args()
    with open(parser.file) as f:
        reader = csv.reader(f)
        for ulid, nova, stara in reader:
            if len(nova) == 0 or len(ulid) == 0:
                continue
            ulid_f = os.path.join(parser.ulidspooldir, ulid)
            if parser.spooldir == parser.ulspooldir:
                nova_f = nova
            else:
                nova_f = os.path.join(parser.spooldir, nova)
            os.symlink(nova_f, ulid_f)
            if len(stara) > 0:
                stara = os.path.join(parser.spooldir, stara[-6:])
                os.symlink(nova_f, stara_f)
