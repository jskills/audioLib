import sys
import os
import eyed3
import psycopg2
import re
from configparser import ConfigParser

eyed3.log.setLevel("ERROR")

debug = 1
runLimit = 1000


#######################

def search_files(directory='.', extension=''):
	fileCount = 0
	returnList = list()
	extension = extension.lower()
	for dirpath, dirnames, files in os.walk(directory):
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

def mp3tags(songFile):
	audiofile = eyed3.load(songFile)
	songDict = dict()
	# get all MP3 tags for this file
	audiofile = eyed3.load(songFile)
	if not audiofile:
		return None
	songDict['title'] = audiofile.tag.title
	songDict['artist'] = audiofile.tag.artist
	songDict['album'] = audiofile.tag.artist
	songDict['genre'] = str(audiofile.tag.genre)
	if audiofile.tag.track_num:
		songDict['track_number'] = str(audiofile.tag.track_num[0])
	if audiofile.info:
		songDict['secs'] =  str(audiofile.info.time_secs)
		if songDict['secs']:
			songDict['secs'] = int(float(songDict['secs']))	
		songDict['bit_rate'] = str(audiofile.info.bit_rate[1])
	if audiofile.tag.comments:
		songDict['comments'] = str(audiofile.tag.comments[0].text)
	songDict['year'] = str(audiofile.tag.getBestDate())
	songDict['album'] = str(audiofile.tag.album)
	songDict['filename'] = songFile
	
	return songDict

###

def populateGenres(conn):
	sql = "select * from genres"
	return getResults(conn, sql)


###

def populateArtists(conn):
	sql = "select * from artists"
	return getResults(conn, sql)

###

def returnGenreID(genreList, genreName):

	returnId = 99

	i = 0
	while i < len(genreList):
		gDict = genreList[i] 
		if gDict['genre_name'] == genreName:
			returnId = gDict['genre_id']
			break
		i += 1

	return returnId

###

def returnArtistID(artistList, artistName):

	returnId = None
	
	i = 0
	while i < len(artistList):
		aDict = artistList[i]
		if aDict['full_name'] == artistName:
			returnId = aDict['artist_id']
			break
		i += 1

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

musicDir = "/media/jskills/Toshiba-2TB/soul"

conn = connect()

genres = populateGenres(conn)
artists = populateArtists(conn)


songList = search_files(musicDir, '.mp3')

# look up song ID based on file name
# look up artist in artists table in DB
# if found use artist_id, if not insert new artist and use that ID
# lookup song/artist combo in songs table in DB


i = 0
while i < len(songList):
	songDict = songList[i]
	i += 1

	#eyed3 genre : looks like (42)Soul
	if songDict['genre']:
		songDict['genre'] = re.sub('\([^()]*\)', '', songDict['genre'])
	# lookup genreId
	songDict['genre_id'] = returnGenreID(genres, songDict['genre'])

	if songDict['artist']:
		songDict['artist_id'] = returnArtistID(artists, songDict['artist'])
		if not songDict['artist_id']:
			sql = "insert into artists (full_name, last_updated_by) values (%s, %s) returning artist_id"
			cur = conn.cursor()
			cur.execute(sql, (songDict['artist'], 'jskills'))
			songDict['artist_id'] = cur.fetchone()[0]
	else:
		print("No MP3 tag for artist for " + str(songDict['filename']))
		continue
	if not  songDict['artist_id']:
		print("No artist ID for " + str(songDict['filename']))
		continue

	# we have artist and genre so let's decide whether to insert a new song or update an existing one
	sql = "select song_id from songs where file_path = %s"
	cur = conn.cursor()
	songDict['song_id'] = cur.execute(sql, (songDict['filename'],))
	if songDict['song_id']:
		# update song meta data
		sql = "update songs set artist_id = %s, song_name = %s, file_path = %s, genre_id = %s, year = %s, "
		sql += "comment = %s, last_updated_by = %s, album = %s, track_number = %s, bit_rate = %s where song_id = %s"
		if debug:
			print(sql)
		else:
			cur = conn.cursor()
			cur.execute(sql, (songDict['artist_id'], songDict['song_name'], songDict['file_path'], songDict['genre_id'], songDict['year'], \
					songDict['comment'], 'jskills', songDict['album'], songDict['track_number'], songDict['bit_rate'], songDict['song_id']))
			
	else:
		# insert new song
		sql = "insert into songs (song_id, artist_id, song_name, file_path, genre_id, year, comment, last_updated_by, album, track_number, bit_rate)"
		sql += " values (DEFAULT, (%s,%s,%s,%s,%,s,%s,%s,%s,%s,%,s))"
		if debug:
			print(sql)
		else:
			cur = conn.cursor()
			cur.execute(sql, (songDict['artist_id'], songDict['song_name'], songDict['file_path'], songDict['genre_id'], songDict['year'], \
					songDict['comment'], 'jskills', songDict['album'], songDict['track_number'], songDict['bit_rate']))



# now that we have ensured all existing songs and new songs are in the database, we should scan all songs and ensure the files are still on disk
# if not, we should delete the record in the song table



