import os
import re
import functools

import Qt

def convert( fileName ) :

	with open( fileName ) as f :
		text = "".join( f.readlines() )
		#print text

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
		text
	)

	with open( fileName, "w" ) as f :
		f.write( newText )

for root, dirs, files in os.walk( "./python" ) :
	for file in files :
		if os.path.splitext( file )[1] == ".py" :
			convert( os.path.join( root, file ) )
