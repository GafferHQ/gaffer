#! /usr/bin/env python

import argparse
import inspect
import subprocess
import os
import json
import matplotlib.pyplot as plt
import matplotlib.ticker

parser = argparse.ArgumentParser(
	description = inspect.cleandoc(
	"""
	Graph the performance results for a folder of json files.
	""" )
)

parser.add_argument(
	'jsonFolder',
	help='Folder containing json files'
)

args = parser.parse_args()

jsonFolder = vars( args )["jsonFolder"]

jsonFileNames = [ i for i in os.listdir( jsonFolder ) if i.endswith( ".json" ) ]

results = []
for n in jsonFileNames:
	f = open( "%s/%s" % ( jsonFolder, n ) )
	d = json.load( f )
	f.close()

	r = {}
	for key, value in d.items():
		if "timings" in value:
			r[ key.split()[1].split('.')[-1][:-1] + "." + key.split()[0]] = ( min( value["timings"] ), max( value["timings"] ) )

	resultName = n[:-5]
	resultOrder = resultName

	try:
		resultOrder = int( subprocess.check_output( [ "git", "rev-list", "--count", resultName ] ) )
		resultName = subprocess.check_output( [ "git", "log", "--format=%B", "-n 1", resultName ] ).splitlines()[0].decode( "UTF-8" )
	except:
		pass

	results.append( [resultOrder, resultName, r] )

results.sort()
results = [r[1:] for r in results ]

ax = plt.subplot(111)

curveNames = results[0][1].keys()
curveNames = sorted( curveNames, key = lambda k : -results[-1][1][k][0] )
for k in curveNames:
	ax.plot( [ j[1][k][0] for j in results ], label = k )
	# Use this line instead if you want to see variability
	#ax.fill_between( range( len( results ) ), [ j[1][k][0] for j in results ], [ j[1][k][1] for j in results ], label = k )

plt.yscale( "log", base = 2 )

# Force labelling of every power of two
plt.yticks( [2**i for i in range( -4, 4 )] )

ax.xaxis.set_major_formatter( matplotlib.ticker.FuncFormatter( lambda i, pos : results[int(i)][0] ) )
plt.xticks( rotation = 45, ha = "right" )

box = ax.get_position()

# Create margin
ax.set_position([box.x0, box.y0 + box.height * 0.2, box.width * 0.8, box.height * 0.8])

# Put a legend to the right of the current axis
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

# Currently hacking things up to work with very old matplotlib
#plt.show_all()
plt.show()
