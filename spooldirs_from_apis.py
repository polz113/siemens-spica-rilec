#!/usr/bin/env python3

import argparse
import csv
import os
import shutils

import urllib.parse
import urllib.request
import json

from siemens_spica_settings import SPOOL_DIR, ULID_SPOOL_DIR, FIX_FNAME, NOCOMMIT_FNAME, FIX_OWNER, FIX_GROUP
from apis_preslikava_kadrovskih_settings import APIS_USERS_URL, APIS_API_KEY, APIS_WEB_SPOOL_FIELD, APIS_MAIN_SPOOL_FIELD

#FIX_OWNER=1001
#FIX_GROUP=33

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ustvari imenike za spool na osnovi apis')
    parser.add_argument('--spooldir', dest='spooldir', action='store',
                    default=SPOOL_DIR,
                    help='Glavni imenik s podatki')
    parser.add_argument('--webspooldir', dest='webspooldir', action='store',
                    default=ULID_SPOOL_DIR, type=str,
                    help='Imenik za web server')
    parser.add_argument('--apikey', dest='apikey', action='store',
                    default=APIS_API_KEY, type=str,
                    help='API key')
    parser.add_argument('--url', dest='url', action='store',
                    default=APIS_USERS_URL, type=str,
                    help='URL')
    args = parser.parse_args()
    webspooldir = args.webspooldir
    spooldir = args.spooldir
    params = urllib.parse.urlencode([("format", "json"), 
                                     ("fieldname", APIS_MAIN_SPOOL_FIELD),
                                     ("fieldname", APIS_WEB_SPOOL_FIELD) ])
    apikey = args.apikey
    headers = {
        "Authorization": "Api-Key " + apikey}
    req = urllib.request.Request(args.url + "?%s" % params, data=None, headers=headers)
    data = dict()
    try:
        response = urllib.request.urlopen(req)
        for obj in json.loads(response.read()):
            uid = obj["uid"]
            field = obj['field']
            dd = data.get(field, dict())
            ds = dd.get(uid, set())
            ds.add(obj['value'])
            dd[uid] = ds
            data[field] = dd
    except urllib.request.HTTPError as error:
        print("The request failed with status code: " + str(error.code))
        print(error.info())
        print(json.loads(error.read()))
    trashdir = os.path.join(spooldir, "conflicts")
    # determine main spool dirs
    spool_dirs = dict()
    main_by_ulid = dict()
    for ulid, vals in data[APIS_MAIN_SPOOL_FIELD].items():
        l = [ os.path.join(spooldir, i) for i in sorted(vals) ]
        if l[0] in spool_dirs:
            print("ERROR: same spool for multiple ULIDs")
            print("    dirs: ", spool_dirs[l[0]], l)
            print("    ulid: ", ulid)
            continue
        main_by_ulid[ulid] = l[0]
        spool_dirs[l[0]] = l[1:]
    # create / rename main spool dirs
    for main, others in spool_dirs.items():
        old_dirs = []
        for o in others:
            if not os.path.islink(o) and os.path.isdir(o):
                old_dirs.append(o)
        if len(old_dirs) > 0 and (os.path.islink(main) or not os.path.isdir(main)):
            if os.path.exists(main):
                trash_fname = os.path.join(trashdir, os.path.basename(main))
                print("mv1 ", main, trash_fname)
                os.rename(main, trash_fname)
            print("mv2 ", old_dirs[0], main)
            os.rename(old_dirs[0], main)
        if not os.path.exists(main):
            os.mkdir(main)
    # create symlinks in the general spool dir
    for main, others in spool_dirs.items():
        for o in others:
            if os.path.islink(o) and os.readlink(o) == main:
                continue
            if os.path.exists(o):
                trash_fname = os.path.join(trashdir, os.path.basename(o))
                print("mv3 ", o, trash_fname)
                os.rename(o, trash_fname)
            os.symlink(main, o)
    # create symlinks in the web spool dir
    for ulid, vals in data[APIS_WEB_SPOOL_FIELD].items():
        if ulid not in main_by_ulid:
            print("ERROR: missing main spool dir for ulid ", ulid)
            continue
        l = [ os.path.join(webspooldir, i) for i in sorted(vals) ]
        for path in l:
            if (os.path.islink(path)):
                os.unlink(path)
            os.symlink(main_by_ulid[ulid], path)
    # create missing files / fix permissions
    for ulid, main in main_by_ulid.items():
        fix_f = os.path.join(main, FIX_FNAME)
        if not os.path.exists(fix_f):
            with open(fix_f, "a"):
                pass
        shutil.chown(fix_f, FIX_OWNER, FIX_GROUP)
        os.chmod(fix_f, 0o660,)
        nocommit_f = os.path.join(main, NOCOMMIT_FNAME)
        if not os.path.exists(nocommit_f):
            with open(nocommit_f, "a"):
                pass
        shutil.chown(nocommit_f, FIX_OWNER, FIX_GROUP)
        os.chmod(nocommit_f, 0o660,)
