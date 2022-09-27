#! /usr/bin/env python

import re

inText = open( "resources/graphics.svg" ).read()

constantGradients = set()
swatchSubstitutions = {}

findHref = re.compile( r'xlink:href="#(.*?)"' )
findUrl = re.compile( r':url\(#(.*?)\)' )
findGradient = re.compile( r" *<linearGradient[^>]*/> *\n?| *<linearGradient.*?/linearGradient> *\n?", flags=re.DOTALL )
matchId = re.compile( r'.*?id="(.*?)".*', flags=re.DOTALL )

usedRefs = set( re.findall( findHref, inText ) + re.findall( findUrl, inText ) )

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

def processGradient( g ):

	ident = re.match( matchId, g.group(0) ).group(1)
	if not ident in usedRefs:
		return ""
	hrefs = re.findall( findHref, g.group(0) )
	if len( hrefs ) == 1:
		if hrefs[0] in constantGradients:
			swatchSubstitutions[ident] = hrefs[0]
			return ""
	return g.group( 0 )

def processRef( r ):
	if r.group( 1 ) in swatchSubstitutions:
		return r.group( 0 )[:r.start(1)-r.start(0)] + swatchSubstitutions[ r.group( 1 ) ] + r.group( 0 )[r.end(1) - r.start( 0 ):]
	else:
		return r.group( 0 )


for m in re.findall( findGradient, inText ):
	if m.count( "<stop" ) == 1:
		constantGradients.add( re.match( matchId, m ).group(1) )

outText = re.sub( r"\n( *)<sodipodi:namedview([^>]*)>", processNamedView, inText, flags=re.DOTALL )

outText = re.sub( findGradient, processGradient, outText )

outText = re.sub( findHref, processRef, outText )
outText = re.sub( findUrl, processRef, outText )

open( "resources/graphics.svg", "w" ).write( outText )
