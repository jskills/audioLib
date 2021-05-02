#!/usr/bin/env python

from ytmusicapi.ytmusic import YTMusic
from utils import *

debug = False

songLimit = 10

ytm = YTMusic('headers_auth.json')

songList = ytm.get_library_upload_songs(limit=songLimit)

conn = connect()

for sl in songList:
    #print(str(sl))

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
            except psycopg2.OperationalError as e:
                print("Insert failed for : ")
                print(sql)
                print(sqlList)
                raise e
                continue

