##########################################################################
#
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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
import GafferScene

##########################################################################
# Metadata
##########################################################################

def __drawingSummary( plug ) :

	info = []
	for name, label in (

		( "solid", "Shaded" ),
		( "wireframe", "Wireframe" ),
		( "outline", "Outline" ),
		( "points", "Point" ),
		( "bound", "Bound" ),

	) :

		values = []
		if plug["gl:primitive:"+name]["enabled"].getValue() :
			values.append( "On" if plug["gl:primitive:" + name]["value"].getValue() else "Off" )
		name = { "points" : "point" }.get( name, name )
		if name != "solid" and plug["gl:primitive:" + name + "Color"]["enabled"].getValue() :
			values.append( "Color" )
		if name not in ( "solid", "bound" ) and plug["gl:primitive:" + name + "Width"]["enabled"].getValue() :
			values.append( "%0gpx" % plug["gl:primitive:" + name + "Width"]["value"].getValue() )

		if values :
			info.append( label + " : " + "/".join( values ) )

	return ", ".join( info )

def __pointsPrimitivesSummary( plug ) :

	info = []
	if plug["gl:pointsPrimitive:useGLPoints"]["enabled"].getValue() :
		info.append( "Points On" if plug["gl:pointsPrimitive:useGLPoints"]["value"].getValue() else "Points Off" )
	if plug["gl:pointsPrimitive:glPointWidth"]["enabled"].getValue() :
		info.append( "Width %0gpx" % plug["gl:pointsPrimitive:glPointWidth"]["value"].getValue() )

	return ", ".join( info )

def __curvesPrimitivesSummary( plug ) :

	info = []
	if plug["gl:curvesPrimitive:useGLLines"]["enabled"].getValue() :
		info.append( "Lines On" if plug["gl:curvesPrimitive:useGLLines"]["value"].getValue() else "Lines Off" )
	if plug["gl:curvesPrimitive:glLineWidth"]["enabled"].getValue() :
		info.append( "Width %0gpx" % plug["gl:curvesPrimitive:glLineWidth"]["value"].getValue() )
	if plug["gl:curvesPrimitive:ignoreBasis"]["enabled"].getValue() :
		info.append( "Basis Ignored" if plug["gl:curvesPrimitive:ignoreBasis"]["value"].getValue() else "Basis On" )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferScene.OpenGLAttributes,

	"description",
	"""
	Applies attributes to modify the appearance of objects in
	the viewport and in renders done by the OpenGLRender node.
	""",

	plugs = {

		# Section summaries

		"attributes" : {

			"layout:section:Drawing:summary" : __drawingSummary,
			"layout:section:Points Primitives:summary" : __pointsPrimitivesSummary,
			"layout:section:Curves Primitives:summary" : __curvesPrimitivesSummary,

		},

	}

)
