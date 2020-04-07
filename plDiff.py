import sys
import os

# 2 file names as args
# will take 2 playlist files (1) the crate of songs (2) the songs already played
# and return a new crate file with played songs removed


# read file from command line argument
crateFile = sys.argv[1]
if not os.path.exists(crateFile):
        print(crateFile + " does not exist")
        sys.exit()
playedFile = sys.argv[2]
if not os.path.exists(playedFile):
        print(playedFile + " does not exist")
        sys.exit()


f = open(crateFile)
crateText = f.readlines()
f.close()        

f = open(playedFile)
playedText = f.readlines()
f.close()


keepers = list()

# loop over the crate list
#      loop over the played list
#      if a line from crate list is not in played list, put into keep list
i = 0
while i < len(crateText):
	if crateText[i][0] == "#":
		i += 1
		continue	
	crateText[i] = crateText[i].replace('\\', '/')
	#print ("ct : " + crateText[i])
	j = 0
	okFlag = 1
	while j < len(playedText):
		if playedText[j][0] == "#":
			j += 1
			continue	
		playedText[j] = playedText[j].replace('\\', '\/')
		#print ("pt : " + playedText[j])
		if crateText[i] == playedText[j]:
			#print("I should be booting this song : " + crateText[i])
			okFlag = 0
			j = len(playedText)
			break
		j += 1
	if okFlag:
		#print("keeping : " + crateText[i])
		keepers.append(crateText[i])
	i += 1

# print keep list as output

i = 0
while i < len(keepers):
	print(keepers[i])
	i += 1
