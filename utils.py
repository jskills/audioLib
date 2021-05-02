import sys
import os
import eyed3
import psycopg2
import re
import string
import glob
from configparser import ConfigParser
from unidecode import unidecode
import warnings
warnings.simplefilter("ignore")

eyed3.log.setLevel("ERROR")


#######################

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

	songDict['filename'] = songFile.encode('utf-8', errors='surrogatepass')

	return songDict

###

def writeCover(sDict, coverImageDir):

	sysCallText = 'eyeD3 --write-images=' + coverImageDir + ' "' + sDict['filename'].decode() + '"'
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
		returnSet = cur.fetchone()[0]

	return returnSet
###
