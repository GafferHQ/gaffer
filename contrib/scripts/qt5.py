#! /usr/bin/env python

import os
import re
import inspect
import argparse
import functools

import Qt

parser = argparse.ArgumentParser(
	description = inspect.cleandoc(
	"""
	Attempts to modify Python source files to assist
	in the migration from Qt4 to Qt5, via Qt.py :

	 - Replaces QtGui with QtWidgets where
	   necessary
	 - Replaces `GafferUI._qtImport( "X" )` calls with
	   `from Qt import X`

	This is a rough and (hopefully) ready script that does
	very little validation. It is recommended that you run
	it in a clean source repository and use `git diff` to
	manually verify the changes that have been made.
	""" ),
	formatter_class = argparse.RawTextHelpFormatter
)

parser.add_argument(
	"source-directory",
	help = "A directory containing python files. This will be searched recursively.",
	nargs = "?",
	default = "./",
)

def convert( fileName ) :

	with open( fileName ) as f :
		text = "".join( f.readlines() )

	# Substitute QtWidgets for QtGui where needed

	def replaceModule( match ) :

		s = match.group( 0 ).split( "." )
		if s[1] in Qt._common_members["QtWidgets"] :
			s[0] = "QtWidgets"

		return ".".join( s )

	for name in Qt._common_members["QtWidgets"] :
		newText = re.sub(
			r"QtGui\.[A-Za-z0-9]+",
			replaceModule,
			text,
		)

	if newText != text :

		# We'll need an import for QtWidgets,
		# and previously we must have had one
		# for QtGui, which we may or may not
		# need still.

		def replaceImport( match, needQtGui ) :

			qtGuiImport = match.group( 0 )
			qtWidgetsImport = qtGuiImport.replace( "QtGui", "QtWidgets" )
			if needQtGui :
				return qtGuiImport + "\n" + qtWidgetsImport
			else :
				return qtWidgetsImport

		newText = re.sub(
			r'QtGui\s*=\s*GafferUI\._qtImport(.*)',
			functools.partial( replaceImport, needQtGui = re.search( r"QtGui\.", newText ) ),
			newText
		)

	# Replace deprecated `_qtImport` calls with `from Qt import` calls

	newText = re.sub(
		r'(Qt\w*)\s*=\s*GafferUI._qtImport\(\s*["\'](Qt.*)["\']\s*\)',
		r'from Qt import \2',
		newText
	)

	with open( fileName, "w" ) as f :
		f.write( newText )

args = parser.parse_args()
directory = vars( args )["source-directory"]
for root, dirs, files in os.walk( directory ) :
	for file in files :
		if os.path.splitext( file )[1] == ".py" :
			convert( os.path.join( root, file ) )
