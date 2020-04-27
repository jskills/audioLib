import sys
import os

# 2 file names as args
# will take 2 playlist files (1) the crate of songs (2) the songs already played
# and return a new crate file with played songs removed

crateFile = None
playedFile = None

# read file from command line argument
try:
	crateFile = sys.argv[1]
except:
	print("Usage : plDiff.py [crate_file] [played_file]")
	sys.exit()
if not os.path.exists(crateFile):
        print(crateFile + " does not exist", file=sys.stderr)
        sys.exit()
try:
	playedFile = sys.argv[2]
except:
	print("Usage : plDiff.py [crate_file] [played_file]", file=sys.stderr)
	sys.exit()
if not os.path.exists(playedFile):
        print(playedFile + " does not exist", file=sys.stderr)
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

i = crateCount = 0

playedCount = len(playedText)

while i < len(crateText):
	if crateText[i][0] == "#":
		i += 1
		continue
	else:
		crateCount += 1
	crateText[i] = crateText[i].replace('\\', '/')
	j = 0
	okFlag = 1
	while j < len(playedText):
		if playedText[j][0] == "#":
			j += 1
			continue	
		playedText[j] = playedText[j].replace('\\', '\/')
		if crateText[i] == playedText[j]:
			#print("I should be booting this song : " + crateText[i], , file=sys.stderr)
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

print("Just wrote " + str(i) + " records.", file=sys.stderr)
print("Processed " + str(crateCount) + " songs in the crate file." , file=sys.stderr)
print("Processed " + str(playedCount) + " songs in the played file." , file=sys.stderr)
