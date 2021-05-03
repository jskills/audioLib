#!/usr/bin/env python

import ast
import os
import sys
import json
from utils import *

# Library file comes from a full dump of all of your Youtube Music songs
# use this to produce :
# https://github.com/jskills/M3U-to-Youtube-Music/blob/master/dumpLibrary.py

debug = False
libraryFile = None

if sys.argv[1:]:
    libraryFile = sys.argv[1]
else:
    print("Usage : populateYTMdata.py [libraryfile.json]")
    sys.exit()

songList = list()
try:
    f = open(libraryFile) 
    songList = f.readlines()
    f.close()
except:
    print("Cannot open library file : " + str(libraryFile))
    sys.exit()



i = 0

for l in songList:
    conn = connect()
    sl = ast.literal_eval(l)

    sql = "select count(*) from ytm_song where video_id = '" + str(sl['videoId']) + "'"
    songFound = int(getResults(conn, sql, 'scalar'))

    sqlList = list()
    # these fields should always be present
    sqlList.append(sl['videoId'])
    sqlList.append(sl['entityId']) 
    sqlList.append(sl['title'])
    if sl['artist']:
        sqlList.append(sl['artist'][0]['name'])
        sqlList.append(sl['artist'][0]['id'])
    else:
        sqlList.append('')
        sqlList.append('')
    if sl['album']:
        sqlList.append(sl['album']['name'])
        sqlList.append(sl['album']['id'])
    else:
        sqlList.append('')
        sqlList.append('')
    sqlList.append(str(sl['duration']))
    sqlList.append('jskills')

    i += 1

    print("Processing record " + str(i))

    if not songFound:
        # insert new playlist
        sql1 = "insert into ytm_song (video_id, entity_id, title, artist_name, artist_id,"
        sql1 += "album_name, album_id, duration, last_updated_by"
        sql2 = " ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s"
        sql2 += ") RETURNING id"
        sql = sql1 + sql2

        if debug:
            print(sql)
            print(sqlList)
        else:
            try:
                cur = conn.cursor()
                cur.execute(sql, sqlList)
                ytm_id = cur.fetchone()[0]
                conn.commit()
                print("Added : " + str(ytm_id) + " | " + str(sl['title']))
            except:
                print("Insert failed for : ")
                print(sql)
                print(sqlList)
                continue
    conn.close()

