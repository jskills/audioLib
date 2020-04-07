import sys
import os
import eyed3
import psycopg2
import re
from configparser import ConfigParser

eyed3.log.setLevel("ERROR")


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
				returnList.append(songDict)
				fileCount += 1
		if fileCount > 200:
			break
	return returnList

###

def mp3tags(songFile):
	audiofile = eyed3.load(songFile)
	songDict = dict()
	# get all MP3 tags for this file
	audiofile = eyed3.load(songFile)
	songDict['title'] = audiofile.tag.title
	songDict['artist'] = audiofile.tag.artist
	songDict['album'] = audiofile.tag.artist
	songDict['genre'] = str(audiofile.tag.genre)
	if audiofile.tag.track_num:
		songDict['track_number'] = str(audiofile.tag.track_num[0])
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

def populateGenres(conn, cur):
	sql = "select genre_id, genre_name from genres"
	cur.execute(sql)
	return cur.fetchall()


###

def returnGenreID(genreList, genreName):

	returnId = 99

	i = 0
	while i < len(genreList):
		gDict = genreList[i] 
		if gDict[1] == genreName:
			returnId = gDict[0]
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



#######################

musicDir = "/media/jskills/Toshiba-2TB/soul"

conn = connect()
cur = conn.cursor()

genres = populateGenres(conn, cur)

print(genres)

songList = search_files(musicDir, '.mp3')

# look up song ID based on file name
# look up artist in artists table in DB
# if found use artist_id, if not insert new artist and use that ID
# lookup song/artist combo in songs table in DB






i = 0
while i < len(songList):
	songDict = songList[i]

	#songDict[genre] looks like (42)Soul
	if songDict['genre']:
		songDict['genre'] = re.sub('\([^()]*\)', '', songDict['genre'])
		# lookup genreId
		songDict['genre_id'] = returnGenreID(genres, songDict['genre'])

	print(songDict)
	
	i += 1
