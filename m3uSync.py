from utils import *
import glob

#######################

def search_files(directory='.', extension=''):

	plList = glob.glob(musicDir + "/*"+ extension)
	plList.sort(key=os.path.getmtime, reverse=True)

	return plList

###

def syncDB(plList, debug=False, runLimit=0):

	conn = connect()

	i = 0

	while i < len(plList):
		pl_id = None

		plList[i] = re.sub(musicDir,'', plList[i])
		sql = "select id from playlist where file_path = %s"
		if debug:
			print(sql + " : " + plList[i])
		cur = conn.cursor()
		cur.execute(sql, (plList[i],))
		pl_id = cur.fetchone()

		# get filename - everything after the trailing slash
		plTitle =  plList[i].rsplit('/', 1)[-1]
		plTitle = re.sub('.m3u', '', plTitle)
		plTitle = re.sub('_', ' ', plTitle)
		plTitle = plTitle.title()
		
		sqlList = list()
		# these fields should always be present
		sqlList.append(plTitle)
		sqlList.append(plList[i])
		sqlList.append('jskills')

		if not pl_id:
			# insert new playlist
			sql1 = "insert into playlist (title, file_path, last_updated_by"
			sql2 = " ) values (%s,%s,%s"
			sql2 += ") RETURNING id"
			sql = sql1 + sql2

			if debug:
				print(sql)
				print(sqlList)
			else:
				try:
					cur = conn.cursor()
					cur.execute(sql, sqlList)
					pl_id = cur.fetchone()[0]
					conn.commit()
				except:
					print("Insert failed for " + str(plList[i]))
					print(sql)
					print(sqlList)
					continue

		i += 1

	conn.close()

	return i

#######################



# set locally 
musicDir = "/media/jskills/Toshiba-2TB/"

# debug flag will result in printing SQL rather than doing any inserts / updates
debug = False

# set to halt after processing a certain number of records in dbSync, leave 0 to process all 
runLimit = 0

# locate all m3u files
plList = search_files(musicDir, '.m3u')

# synchronize database to reflect playlists on disk
plProcessed = syncDB(plList, debug, runLimit)
print("Completed processing " + str(plProcessed) + " files.")
