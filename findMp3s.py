import pdb
import sys
import os
from os import path
import eyed3
import psycopg2
import re
import string
import glob
from datetime import datetime, timedelta
from configparser import ConfigParser
from unidecode import unidecode
import warnings

warnings.simplefilter("ignore")
eyed3.log.setLevel("ERROR")


#######################

def isOldFile(fileCheck):
    dateCheck = datetime.now() - timedelta(days=8)
    filetime = datetime.fromtimestamp(path.getctime(fileCheck))
    if filetime < dateCheck:
        return 1
    else:
        return 0

###

def search_files(directory='.', extension='', skip=None):
    fileCount = 0
    returnList = list()
    extension = extension.lower()
    for dirpath, dirnames, files in os.walk(directory):
        if skip:
            dirnames[:] = [d for d in dirnames if d != skip]
        for name in files:
            if extension and name.lower().endswith(extension):
                songFile = os.path.join(dirpath, name)
                if isOldFile(songFile):
                    continue
                else:
                    # get all MP3 tags for this file
                    songDict = mp3tags(songFile)
                    # add to dictionary of all files read with MP3 tag info
                    if songDict:
                        returnList.append(songDict)
                        fileCount += 1
            if runLimit and fileCount > runLimit:
                break
    return returnList

###

def normalizeUnicode(s):
    s = unidecode(s)
    printable = set(string.printable)
    s = ''.join(filter(lambda x: x in printable, s))
    return s

###

def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default

###

def mp3tags(songFile):
    audiofile = eyed3.load(songFile)
    songDict = dict()
    # get all MP3 tags for this file
    audiofile = eyed3.load(songFile)
    if not audiofile:
        return None
    songDict['title'] = audiofile.tag.title
    if not songDict['title']:
        return None
    else:
        songDict['title'] = normalizeUnicode(songDict['title'])
    songDict['artist'] = audiofile.tag.artist
    if not songDict['artist']:
        return None
    else:
        songDict['artist'] = normalizeUnicode(songDict['artist'])

    songDict['genre'] = str(audiofile.tag.genre)
    
    if audiofile.tag.track_num and str(audiofile.tag.track_num[0]) != 'None':
        songDict['track_number'] = int(str(audiofile.tag.track_num[0]))
    if audiofile.info:
        songDict['duration'] = audiofile.info.time_secs
        if songDict['duration']:
            songDict['duration'] = int(float(songDict['duration'])) 
        if str(audiofile.info.bit_rate[1]) != 'None':
            songDict['bit_rate'] = str(audiofile.info.bit_rate[1])
    if audiofile.tag.comments:
        try:
            songDict['comment'] = str(audiofile.tag.comments[1].text)
        except IndexError:
            songDict['comment'] = str(audiofile.tag.comments[0].text)
        songDict['comment'] = normalizeUnicode(songDict['comment'])
    year = str(audiofile.tag.getBestDate())
    songDict['year'] = year[0:4]
    songDict['year'] = safe_cast(songDict['year'], int, '') 
    if audiofile.tag.album:
        songDict['album'] = str(audiofile.tag.album)
        songDict['album'] = songDict['album'].replace(",", "")
        songDict['album'] = songDict['album'].replace("/", "-")
        songDict['album'] = songDict['album'].replace("!", "")
        songDict['album'] = songDict['album'].replace("\?", "")
        songDict['album'] = normalizeUnicode(songDict['album'])
    songDict['filename'] = normalizeUnicode(songFile)

    return songDict

###

def writeCover(sDict):

    sysCallText = 'eyeD3 --write-images=' + coverImageDir + ' "' + str(sDict['filename']) + '"'
    os.system(sysCallText)
    outFile = coverImageDir + "FRONT_COVER.jpg"
    coverFile = str(sDict['song_id']) + ".jpg"
    if os.path.exists(outFile):
        sysCallText = 'mv ' + outFile + ' '  + coverImageDir + coverFile
        print(sysCallText)
        os.system(sysCallText)


###

def populateGenres(conn):
    sql = "select * from genre"
    return getResults(conn, sql)


###

def populateArtists(conn):
    sql = "select * from artist"
    return getResults(conn, sql)

###

def returnGenreID(genreList, genreName):

    returnId = 99

    i = 0
    while i < len(genreList):
        gDict = genreList[i] 
        if gDict['genre_name'] == genreName:
            returnId = gDict['id']
            break
        i += 1

    return returnId

###

def returnArtistID(conn, artistName):

    returnId = None

    cur = conn.cursor()
    sql = "select id from artist where full_name = %s"
    #pdb.set_trace()
    try:
        cur.execute(sql, (artistName,) )
        curReturn = cur.fetchone()
        returnId = curReturn[0]
    except:
        returnId = None

    return returnId
###

def config(filename='/home/jskills/src/audioLib/db.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)

    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
    return db

###

def connect():
    conn = None

    try:
        params = config()
        conn = psycopg2.connect(**params)
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    return conn

###

def getResults(conn, sql, type='list'):
    # type parameter refers to the desired data structure for return data
    # 'list' : list of dictionaries, each dictionary using column names as key values
    # 'scalar' : single value

    returnSet = None    

    cur = conn.cursor()
    cur.execute(sql)
    desc = cur.description
    column_names = [col[0] for col in desc]

    if type == 'list':
        returnSet = [dict(zip(column_names, row)) for row in cur.fetchall()]
    elif type == 'scalar':
        returnSet = cur.fetchone()

    return returnSet
###


def syncDB(songList, debug=False, runLimit=0):

    conn = connect()

    genres = populateGenres(conn)

    i = 0
    totalProcessed = 0
    while i < len(songList):
        songDict = songList[i]
        i += 1

        #eyed3 genre : looks like (42)Soul
        if songDict['genre']:
            songDict['genre'] = re.sub('\([^()]*\)', '', songDict['genre'])
        # lookup genreId
        songDict['genre_id'] = returnGenreID(genres, songDict['genre'])

        if songDict['artist']:
            songDict['artist_id'] = returnArtistID(conn, songDict['artist'])
            if not songDict['artist_id']:
                sql = "insert into artist (full_name, last_updated_by) values (%s, %s) returning id"
                try:
                    cur = conn.cursor()
                    cur.execute(sql, (songDict['artist'], 'jskills'))
                    songDict['artist_id'] = cur.fetchone()[0]
                except:
                    print("Cannot find or insert artist :" + normalizeUnicode(songDict['artist']))
                    continue
        else:
            print("No MP3 tag for artist for " + str(songDict['filename']))
            continue
        if not songDict['artist_id']:
            print("No artist ID for " + str(songDict['filename']))
            continue

        # we have artist and genre so let's decide whether to insert a new song or update an existing one
        # remove musicDir from file_path prior to putting into the DB

        songDict['file_path'] = re.sub(musicDir,'', songDict['filename'])

        sql = "select id from song where file_path = (%s)"

        if debug:
            print(sql + normalizeUnicode(songDict['file_path']))

        cur = conn.cursor()
        try:
            cur.execute(sql, (normalizeUnicode(songDict['file_path']),))
            songDict['song_id'] = cur.fetchone()[0]
        except:
            #print("Could not find this song : " + normalizeUnicode(songDict['file_path']))
            songDict['song_id'] = None

        sqlList = list()
        # these fields should always be present
        sqlList.append(songDict['artist_id'])
        sqlList.append(songDict['title'])
        sqlList.append(songDict['file_path'])
        sqlList.append(songDict['genre_id'])
        sqlList.append(songDict['year'])
        sqlList.append('jskills')

        if songDict['song_id']:
            # update song meta data
            sql = "update song set artist_id = %s, song_name = %s, file_path = %s, genre_id = %s, year = %s, last_updated_by = %s"
            if 'comment' in songDict.keys():
                if songDict['comment'] and songDict['comment'] != 'None':
                    sql += ", comment = %s"
                    sqlList.append(songDict['comment'])
            if 'album' in songDict.keys():
                if songDict['album'] and songDict['album'] != 'None':
                    sql += ", album = %s"
                    sqlList.append(songDict['album'])
            if 'track_number' in songDict.keys():
                if songDict['track_number'] > 0 and songDict['track_number'] != 'None':
                    sql += ", track_number = %s"
                    sqlList.append(songDict['track_number'])
            if 'bit_rate' in songDict.keys():
                if int(songDict['bit_rate']) > 0 and songDict['bit_rate'] != 'None':
                    sql += ", bit_rate = %s"
                    sqlList.append(songDict['bit_rate'])
            if 'duration' in songDict.keys():
                if int(songDict['duration']) > 0 and songDict['duration'] != 'None':
                    sql += ", duration = %s"
                    sqlList.append(songDict['duration'])

    
            sql += ", last_updated_date = now() "   
            sql += " where id = %s"
            sqlList.append(songDict['song_id'])

            if debug:
                print(sql)
                print(sqlList)
            else:
                try:
                    cur = conn.cursor()
                    cur.execute(sql, sqlList)
                    conn.commit()
                except:
                    print("Update failed for " + str(songDict['filename']))
                    print(sql)
                    print(sqlList)
                    conn.rollback()
                    continue
            
        else:
            # insert new song
            sql1 = "insert into song (artist_id, song_name, file_path, genre_id, year, last_updated_by"
            sql2 = " ) values (%s,%s,%s,%s,%s,%s"

            if 'comment' in songDict.keys():
                if songDict['comment'] and songDict['comment'] != 'None':
                    sql1 += ", comment"
                    sql2 += ",%s"
                    sqlList.append(songDict['comment'])
            if 'album' in songDict.keys():
                if songDict['album'] and songDict['album'] != 'None':
                    sql1 += ", album"
                    sql2 += ",%s"
                    sqlList.append(songDict['album'])
            if 'track_number' in songDict.keys():
                if songDict['track_number'] > 0 and songDict['track_number'] != 'None':
                    sql1 += ",track_number"
                    sql2 += ",%s"
                    sqlList.append(songDict['track_number'])
            if 'bit_rate' in songDict.keys():
                if int(songDict['bit_rate']) > 0 and songDict['bit_rate'] != 'None':
                    sql1 += ",bit_rate"
                    sql2 += ",%s"
                    sqlList.append(songDict['bit_rate'])
            if 'duration' in songDict.keys():
                if int(songDict['duration']) > 0 and songDict['duration'] != 'None':
                    sql1 += ",duration"
                    sql2 += ",%s"
                    sqlList.append(songDict['duration'])

            sql2 += ")"
            sql = sql1 + sql2 + " RETURNING id"

            if debug:
                print(sql)
                print(sqlList)
            else:
                try:
                    cur = conn.cursor()
                    cur.execute(sql, sqlList)
                    songDict['song_id'] = cur.fetchone()[0]
                    conn.commit()
                except:
                    print("Insert failed for " + str(songDict['filename']))
                    print(sql)
                    print(sqlList)
                    conn.rollback()
                    continue

        writeCover(songDict)

        totalProcessed += 1

    conn.close()

    return totalProcessed

###

def purgeOrphans(songList, debug=False):

    conn = connect()
    sql = "select id, song_name, file_path from song"
    allSongs = getResults(conn, sql)
    
    removed = 0 
    for s in allSongs:
        checkPath = musicDir + str(s['file_path'])
        if not os.path.exists(checkPath):
            print("Deleting record for song - id : " + str(s['id']) + " name " + str(s['id']))
            print(str(checkPath) + " does not exist.")
            sql = "delete from songs where id = %s"
            if debug:
                print(sql)
            else:
                print(sql)
                # need to address DB lookup of filenames before we can be sure to delete
                #cur.execute(sql, sqlList)
                #conn.commit()
                
            removed += 1
    conn.close()

    return removed
    
#######################



# set locally 
musicDir = "/media/jskills/Toshiba-2TB/"
coverImageDir = musicDir + "cover_art/"

# debug flag will result in printing SQL rather than doing any inserts / updates
debug = False

# set to halt after processing a certain number of records in dbSync, leave 0 to process all 
runLimit = 0

# locate all mp3 files and exclude ones you're not ready to process into the database yet
excludeDir = "Kenans Treasure Chest"
songList = search_files(musicDir, '.mp3', excludeDir)

# synchronize database to reflect songs on disk
songsProcessed = syncDB(songList, debug, runLimit)
print("Completed processing " + str(songsProcessed) + " files.")


# now that we have ensured all existing songs and new songs are in the database,
# we should scan all songs and ensure the files are still on disk
# if not, we should delete the record in the song table
#orphansProcessed = purgeOrphans(songList, debug)
#print("Removed " + str(orphansProcessed) + " orphaned DB records")

# also we need to cleanup all files in the cover images directory that do not start with a number
# (hence not the cover image for the song_id)
deleteList = glob.glob(coverImageDir + "/[A-Z]*")
for dl in deleteList:
    if debug:
        print(str(dl))
    else:
        os.remove(dl)


