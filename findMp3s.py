import sys
import os
import eyed3
import psycopg2
import re
import string
from configparser import ConfigParser
from unidecode import unidecode
import warnings

warnings.simplefilter("ignore")
eyed3.log.setLevel("ERROR")

debug = False
runLimit = 0

# if you need to debug
#import pdb
# then add this to where you want to set a break
# pdb.set_trace()


#######################

def search_files(directory='.', extension=''):
	fileCount = 0
	returnList = list()
	extension = extension.lower()
	for dirpath, dirnames, files in os.walk(directory):
		# skip this directory for now
		dirnames[:] = [d for d in dirnames if d != "Kenans Treasure Chest"]
		for name in files:
			if extension and name.lower().endswith(extension):
				songFile = os.path.join(dirpath, name)
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
		songDict['secs'] = audiofile.info.time_secs
		if songDict['secs']:
			songDict['secs'] = int(float(songDict['secs']))	
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
		songDict['album'] = normalizeUnicode(songDict['album'])
	songDict['filename'] = normalizeUnicode(songFile)

	return songDict

###

def writeCover(sDict):

	sysCallText = 'eyeD3 --write-images=' + coverImageDir + ' "' + str(songDict['filename']) + '"'
	os.system(sysCallText)
	outFile = coverImageDir + "FRONT_COVER.jpg"
	coverFile = str(songDict['song_id']) + ".jpg"
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
	try:
		cur.execute(sql, (artistName,) )
		returnId = cur.fetchone()[0]
	except:
		returnId = None

	return returnId
###

def config(filename='db.ini', section='postgresql'):
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


#######################

musicDir = "/media/jskills/Toshiba-2TB/"
coverImageDir = musicDir + "cover_art/"

conn = connect()

genres = populateGenres(conn)


songList = search_files(musicDir, '.mp3')

# look up song ID based on file name
# look up artist in artist table in DB
# if found use artist_id, if not insert new artist and use that ID
# lookup song/artist combo in song table in DB


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
		print("Had to skip this one for now : " + normalizeUnicode(songDict['file_path']))
		continue

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
		sql2 += ")"
		sql = sql1 + sql2 + " RETURNIND id"

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
				continue

	writeCover(songDict)

	totalProcessed += 1

print("Completed processing " + str(totalProcessed) + " files.")



# now that we have ensured all existing songs and new songs are in the database, we should scan all songs and ensure the files are still on disk
# if not, we should delete the record in the song table

# also we need to cleanup all files in the cover images directory that do not start with a number (hence not the cover image for the song_id



