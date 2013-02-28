##########################################################################
#  
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
#  
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#  
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#  
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#  
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#  
##########################################################################

import Gaffer
import GafferUI
import GafferRenderMan

def __qualitySummary( plug ) :

	info = []
	
	if plug["pixelSamples"]["enabled"].getValue() :
		ps = plug["pixelSamples"]["value"].getValue()
		info.append( "Pixel Samples %dx%d" % ( ps[0], ps[1] ) )
		
	return ", ".join( info )

def __statisticsSummary( plug ) :

	info = []
	if plug["statisticsLevel"]["enabled"].getValue() :
		info.append( "Level %d" % plug["statisticsLevel"]["value"].getValue() )
	if plug["statisticsFileName"]["enabled"].getValue() :
		info.append( "File name" )
	if plug["statisticsProgress"]["enabled"].getValue() :
		info.append( "Progress " + ( "On" if plug["statisticsProgress"]["value"].getValue() else "Off" ) )

	return ", ".join( info )
		
def __searchPathsSummary( plug ) :

	info = []
	
	for childName, label in (
		( "shaderSearchPath", "Shaders" ),
		( "textureSearchPath", "Textures" ),
		( "displaySearchPath", "Displays" ),
		( "archiveSearchPath", "Archives" ),
		( "proceduralSearchPath", "Procedurals" ),
	) :
		if plug[childName]["enabled"].getValue() :
			info.append( label )
		
	return ", ".join( info )

GafferUI.PlugValueWidget.registerCreator(
	
	GafferRenderMan.RenderManOptions.staticTypeId(),
	"options",
	GafferUI.SectionedCompoundDataPlugValueWidget,
	sections = (
		
		{
			"label" : "Quality",
			"summary" : __qualitySummary,
			"namesAndLabels" : (
				( "ri:pixelSamples", "Pixel Samples" ),
			),
		},
		
		{
			"label" : "Statistics",
			"summary" : __statisticsSummary,
			"namesAndLabels" : (
				( "ri:statistics:endofframe", "Level" ),
				( "ri:statistics:filename", "File Name" ),
				( "ri:statistics:progress", "Progress" ),
			),
		},
		
		{
			"label" : "Search Paths",
			"summary" : __searchPathsSummary,
			"namesAndLabels" : (
				( "ri:searchpath:shader", "Shaders" ),
				( "ri:searchpath:texture", "Textures" ),
				( "ri:searchpath:display", "Displays" ),
				( "ri:searchpath:archive", "Archives" ),
				( "ri:searchpath:procedural", "Procedurals" ),
			),
		},
		
	),	
	
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManOptions.staticTypeId(),
	"options.statisticsLevel.value",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "0 (Off)", 0 ),
		( "1", 1 ),
		( "2", 2 ),
		( "3 (Most Verbose)", 3 ),
	),
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManOptions.staticTypeId(),
	"options.statisticsFileName.value",
	lambda plug : GafferUI.PathPlugValueWidget( plug,
		path = Gaffer.FileSystemPath( "/", filter = Gaffer.FileSystemPath.createStandardFilter( extensions = ( "htm", "html", "txt", "stats" ) ) )
	)
)
