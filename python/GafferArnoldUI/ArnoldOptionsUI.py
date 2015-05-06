##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import GafferArnold

def __samplingSummary( plug ) :

	info = []
	if plug["aaSamples"]["enabled"].getValue() :
		info.append( "AA %d" % plug["aaSamples"]["value"].getValue() )
	if plug["giDiffuseSamples"]["enabled"].getValue() :
		info.append( "Diffuse %d" % plug["giDiffuseSamples"]["value"].getValue() )
	if plug["giGlossySamples"]["enabled"].getValue() :
		info.append( "Glossy %d" % plug["giGlossySamples"]["value"].getValue() )
	if plug["giRefractionSamples"]["enabled"].getValue() :
		info.append( "Refraction %d" % plug["giRefractionSamples"]["value"].getValue() )

	return ", ".join( info )

def __featuresSummary( plug ) :

	info = []
	for childName, label in (
		( "ignoreTextures", "Textures" ),
		( "ignoreShaders", "Shaders" ),
		( "ignoreAtmosphere", "Atmos" ),
		( "ignoreLights", "Lights" ),
		( "ignoreShadows", "Shadows" ),
		( "ignoreSubdivision", "Subdivs" ),
		( "ignoreDisplacement", "Disp" ),
		( "ignoreBump", "Bump" ),
		( "ignoreMotionBlur", "MBlur" ),
		( "ignoreSSS", "SSS" ),
	) :
		if plug[childName]["enabled"].getValue() :
			info.append( label + ( " Off " if plug[childName]["value"].getValue() else " On" ) )

	return ", ".join( info )

def __searchPathsSummary( plug ) :

	info = []
	for prefix in ( "texture", "procedural", "shader" ) :
		if plug[prefix+"SearchPath"]["enabled"].getValue() :
			info.append( prefix.capitalize() )

	return ", ".join( info )

def __errorColorsSummary( plug ) :

	info = []
	for suffix in ( "Texture", "Mesh", "Pixel", "Shader" ) :
		if plug["errorColorBad"+suffix]["enabled"].getValue() :
			info.append( suffix )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldOptions,

	plugs = {

		# Sections

		"options" : [

			"layout:section:Sampling:summary", __samplingSummary,
			"layout:section:Features:summary", __featuresSummary,
			"layout:section:Search Paths:summary", __searchPathsSummary,
			"layout:section:Error Colors:summary", __errorColorsSummary,

		],

		# Sampling

		"options.aaSamples" : [

			"layout:section", "Sampling",
			"label", "AA Samples",

		],

		"options.giDiffuseSamples" : [

			"layout:section", "Sampling",
			"label", "Diffuse Samples",

		],

		"options.giGlossySamples" : [

			"layout:section", "Sampling",
			"label", "Glossy Samples",

		],

		"options.giRefractionSamples" : [

			"layout:section", "Sampling",
			"label", "Refraction Samples",

		],

		# Features

		"options.ignoreTextures" : [

			"layout:section", "Features",

		],

		"options.ignoreShaders" : [

			"layout:section", "Features",

		],

		"options.ignoreAtmosphere" : [

			"layout:section", "Features",

		],

		"options.ignoreLights" : [

			"layout:section", "Features",

		],

		"options.ignoreShadows" : [

			"layout:section", "Features",

		],

		"options.ignoreSubdivision" : [

			"layout:section", "Features",

		],

		"options.ignoreDisplacement" : [

			"layout:section", "Features",

		],

		"options.ignoreBump" : [

			"layout:section", "Features",

		],

		"options.ignoreMotionBlur" : [

			"layout:section", "Features",

		],

		"options.ignoreSSS" : [

			"layout:section", "Features",

		],

		# Search Paths

		"options.textureSearchPath" : [

			"layout:section", "Search Paths",
			"label", "Textures",

		],

		"options.proceduralSearchPath" : [

			"layout:section", "Search Paths",
			"label", "Procedurals",

		],

		"options.shaderSearchPath" : [

			"layout:section", "Search Paths",
			"label", "Shaders",

		],

		# Error Colors

		"options.errorColorBadTexture" : [

			"layout:section", "Error Colors",
			"label", "Bad Texture",

		],

		"options.errorColorBadMesh" : [

			"layout:section", "Error Colors",
			"label", "Bad Mesh",

		],

		"options.errorColorBadPixel" : [

			"layout:section", "Error Colors",
			"label", "Bad Pixel",

		],

		"options.errorColorBadShader" : [

			"layout:section", "Error Colors",
			"label", "Bad Shader",

		],

	}

)
