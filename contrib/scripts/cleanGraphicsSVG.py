#! /usr/bin/env python

import re

inText = open( "resources/graphics.svg" ).read()

def processNamedView( t ):
	indent = t.group( 1 )
	items = t.group( 2 ).split()

	processedItems = []
	for i in items:
		name = i.split("=")[0]
		if sum( s in name for s in [ "inkscape:window", "inkscape:cx", "inkscape:cy", "inkscape:zoom", "inkscape:current-layer", "showgrid", "inkscape:current-layer", "inkscape:snap" ] ):
			continue
		processedItems.append( i )
	return "\n" + indent + "<sodipodi:namedview\n   " + indent + ("\n   " + indent ).join( processedItems ) + ">"

outText = re.sub( r"\n( *)<sodipodi:namedview([^>]*)>", processNamedView, inText, flags=re.DOTALL )

open( "resources/graphics.svg", "w" ).write( outText )
