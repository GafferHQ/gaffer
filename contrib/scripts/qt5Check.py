#! /usr/bin/env python

import os
import re
import inspect
import argparse
import pydoc

import Qt

parser = argparse.ArgumentParser(
	description = inspect.cleandoc(
	"""
	Attempts to search Python source files to assist
	in the detection of Qt constructs that are not
	supported directly by Qt.py. It finds some false
	positives (for example QtGui.QApplication.instance)
	but is generally fairly useful.
	"""
	)
)

parser.add_argument(
	"source-directory",
	help = "A directory containing python files. This will be searched recursively.",
	nargs = "?",
	default = "./",
)

def detect( fileName ) :

	with open( fileName ) as f :
		text = "".join( f.readlines() )

	matches = re.findall( r"Qt[A-Za-z_]+\.[A-Za-z0-9\._]+", text )
	if matches is None :
		return

	for match in matches :
		if pydoc.locate( "Qt." + match ) is None :
			print fileName + " : " + match

args = parser.parse_args()
directory = vars( args )["source-directory"]
for root, dirs, files in os.walk( directory ) :
	for file in files :
		if os.path.splitext( file )[1] == ".py" :
			detect( os.path.join( root, file ) )
