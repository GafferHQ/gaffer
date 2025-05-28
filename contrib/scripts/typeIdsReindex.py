#! /usr/bin/env python

import re

# In theory, this could be a glob? With some way of deciding an order?
# But currently, this script assumes that you manually set the first and last id of every file,
# and manually order them in this file in a matching way - it reindexes all the ids within each file,
# and throws an exception if you screw up the first/last ids matching between files.

typeIdFiles = [
'include/Gaffer/TypeIds.h',
'include/GafferDispatch/TypeIds.h',
'include/GafferTest/TypeIds.h',
'include/GafferUSD/TypeIds.h',
'include/GafferUI/TypeIds.h',
'include/GafferScene/TypeIds.h',
'include/GafferSceneUI/TypeIds.h',
'include/GafferSceneTest/TypeIds.h',
'include/GafferImage/TypeIds.h',
'include/GafferImageUI/TypeIds.h',
'include/GafferOSL/TypeIds.h',
'include/GafferArnold/TypeIds.h',
'include/GafferCycles/TypeIds.h',
'include/GafferDelight/TypeIds.h',
'include/GafferRenderMan/TypeIds.h',
'include/GafferVDB/TypeIds.h',
'include/GafferML/TypeIds.h',
'include/GafferScene/Private/IECoreScenePreview/TypeIds.h',
'include/GafferCortex/TypeIds.h'
]

prevFileLastId = None
prevId = None

findId = re.compile( r'(\w*) = *([0-9]*)' )

for fileName in typeIdFiles:
	prevId = None
	inText = open( fileName ).read()

	def processId( g ):

		global prevId
		global prevFileLastId

		curId = int( g.group( 2 ) )
		if g.group( 1 ) == "LastTypeId":
			if prevId > curId:
				raise Exception( "Id runs past last in %s" % fileName )

			prevFileLastId = curId
		elif prevId is None:
			if prevFileLastId and curId != prevFileLastId + 1:
				raise Exception( "First id of %s doesn't match last id of previous file" % fileName )
			prevId = curId
		else:
			curId = prevId + 1
			prevId += 1

		return "%s = %i" % ( g.group(1), curId )

	outText = re.sub( findId, processId, inText )

	open( fileName, "w" ).write( outText )
