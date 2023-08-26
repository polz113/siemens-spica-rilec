#!/usr/bin/env python3

import argparse
import csv
import os

import urllib.request
import json

from siemens_spica_settings import SPOOL_DIR, ULID_SPOOL_DIR, FIX_FNAME, NOCOMMIT_FNAME
from apis_preslikava_kadrovskih_settings import APIS_USERS_URL, APIS_API_KEY

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
    parser.add_argument('--apikey', dest='apikey', action='store',
                    default=APIS_API_KEY, type=str,
                    help='API key')
    parser.add_argument('--url', dest='url', action='store',
                    default=APIS_USERS_URL, type=str,
                    help='URL')
    args = parser.parse_args()
    ulidspooldir = args.ulidspooldir
    spooldir = args.spooldir
    url = args.url
    apikey = args.apikey
    headers = {
        "Authorization": "Api-Key " + apikey}
    req = urllib.request.Request(url, data=None, headers=headers)
    uids = dict()
    try:
        response = urllib.request.urlopen(req)
        for obj in json.loads(response.read()):
            kadrovska = obj["value"]
            uid = obj["uid"]
            s = uids.get(uid, set())
            s.add(kadrovska)
            uids[obj["uid"]] = s
    except urllib.request.HTTPError as error:
        print("The request failed with status code: " + str(error.code))
        print(error.info())
        print(json.loads(error.read()))
    for ulid, kadrovske in uids.items():
        ulid_f = os.path.join(ulidspooldir, ulid)
        nove_kadrovske = []
        kadrovska_fdir = None
        for kadrovska in kadrovske:
            kadrovska_f = os.path.join(spooldir, kadrovska)
            if not os.path.exists(kadrovska_f):
                nove_kadrovske.append(kadrovska_f)
            elif kadrovska_fdir is None:
                kadrovska_fdir = kadrovska_f
        if kadrovska_fdir is None:
            kadrovska_fdir = nove_kadrovske[0]
            nove_kadrovske = nove_kadrovske[1:]
            print("mkdir ", kadrovska_fdir)
            os.mkdir(kadrovska_fdir)
        print("kadrovska_fdir:", kadrovska_fdir, nove_kadrovske + [ulid_f])
        for fname in nove_kadrovske + [ulid_f]:     
            if os.path.islink(fname):
                print("unlink ", fname)
                os.unlink(fname)
            print("symlink ", kadrovska_fdir, fname)
            os.symlink(kadrovska_fdir, fname)
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
