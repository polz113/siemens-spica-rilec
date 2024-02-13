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
    trashdir = os.path.join(spooldir, "conflicts")
    for ulid, kadrovske in uids.items():
        ulid_f = os.path.join(ulidspooldir, ulid)
        others = set()
        kadrovske_l = list(sorted(kadrovske))
        dests = []
        for kadrovska in kadrovske_l:
            kadrovska_f = os.path.join(spooldir, kadrovska)
            dests.append(kadrovska_f)
        dests.append(ulid_f)
        # print(f"dests: {dests}")
        kadrovska_fdir = None
        if not(os.path.islink(dests[0])) and os.path.isdir(dests[0]):
            kadrovska_fdir = dests[0]
        for dest in dests:
            while os.path.islink(dest):
                others.add(dest)
                dest = os.path.realpath(os.readlink(dest))
            others.add(dest)
        olddir = None
        others.discard(kadrovska_fdir)
        already_ok = set()
        # print(f" others:{others}")
        for i in others:
            if kadrovska_fdir is None:
                if not os.path.islink(i) and os.path.isdir(i):
                    olddir = i
                    # print(f"olddir: {i}")
                    continue
            trash_fname = os.path.join(trashdir, os.path.basename(i))
            if os.path.exists(i):
                rl = None
                islink = os.path.islink(i)
                if islink:
                    rl = os.readlink(i)
                if kadrovska_fdir is not None and islink and rl == kadrovska_fdir:
                    already_ok.add(i)
                else:
                    # print(f" fdir: {kadrovska_fdir}, {i} -> {rl} islink: {islink}")
                    #if os.path.exists(trash_fname):
                    #    os.path.unlink(trash_fname)
                    print(f"mv {i} {trash_fname}")
                    os.rename(i, trash_fname)
        if kadrovska_fdir is None:
            kadrovska_fdir = os.path.join(spooldir, kadrovske_l[0])
            if olddir is None:
                print(f"mkdir {kadrovska_fdir}")
                os.mkdir(kadrovska_fdir)
            else:
                print(f"mv {olddir} {kadrovska_fdir}")
                os.rename(olddir, kadrovska_fdir)
        already_ok.add(kadrovska_fdir)
        for dest in dests:
            if dest not in already_ok:
                print(f"ln {kadrovska_fdir} {dest}")
                os.symlink(kadrovska_fdir, dest)
                already_ok.add(dest)
        # print("kadrovska_fdir:", kadrovska_fdir, nove_kadrovske + [ulid_f])
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
