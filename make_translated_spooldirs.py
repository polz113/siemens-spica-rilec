#!/usr/bin/env python3

import argparse
import csv
import os

from siemens_spica_settings import SPOOL_DIR, ULID_SPOOL_DIR, FIX_FNAME, NOCOMMIT_FNAME
FIX_OWNER=1001
FIX_GROUP=33


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prenesi podatke na spico')
    parser.add_argument('--spooldir', dest='spooldir', action='store',
                    default=SPOOL_DIR,
                    help='Glavni imenik s podatki')
    parser.add_argument('--ulidspooldir', dest='ulidspooldir', action='store',
                    default=ULID_SPOOL_DIR, type=str,
                    help='Imenik za web server')
    parser.add_argument('file', metavar='file',
                    type=str,
                    help='.csv ULID,kadrovska,stara kadrovska')
    args = parser.parse_args()
    ulidspooldir = args.ulidspooldir
    spooldir = args.spooldir
    with open(args.file) as f:
        reader = csv.reader(f)
        for ulid, nova, stara in reader:
            if len(nova) == 0 or len(ulid) == 0:
                continue
            ulid_f = os.path.join(ulidspooldir, ulid)
            if spooldir == ulidspooldir:
                nova_f = nova
            else:
                nova_f = os.path.join(spooldir, nova)
            if not os.path.exists(nova_f):
                os.mkdir(nova_f)
            if os.path.islink(ulid_f):
                os.unlink(ulid_f)
            os.symlink(nova_f, ulid_f)
            fix_f = os.path.join(ulid_f, FIX_FNAME)
            if not os.path.exists(fix_f):
                with open(fix_f, "a"):
                    pass
                os.chown(fix_f, FIX_OWNER, FIX_GROUP)
                os.chmod(fix_f, 0o660,)
            nocommit_f = os.path.join(ulid_f, NOCOMMIT_FNAME)
            if not os.path.exists(nocommit_f):
                with open(nocommit_f, "a"):
                    pass
                os.chown(nocommit_f, FIX_OWNER, FIX_GROUP)
                os.chmod(nocommit_f, 0o660,)
            if len(stara) > 0:
                stara_f = os.path.join(spooldir, stara[-6:])
                if os.path.islink(stara_f):
                    os.unlink(stara_f)
                os.symlink(nova, stara_f)
