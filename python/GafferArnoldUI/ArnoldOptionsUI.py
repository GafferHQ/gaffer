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

	"description",
	"""
	Sets global scene options applicable to the Arnold
	renderer. Use the StandardOptions node to set
	global options applicable to all renderers.
	""",

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

			"description",
			"""
			Controls the number of rays per pixel
			traced from the camera. The more samples,
			the better the quality of antialiasing,
			motion blur and depth of field. The actual
			number of rays per pixel is the square of
			the AA samples value - so a value of 3
			means 9 rays are traced, 4 means 16 rays are
			traced and so on.
			""",

			"layout:section", "Sampling",
			"label", "AA Samples",

		],

		"options.giDiffuseSamples" : [

			"description",
			"""
			Controls the number of rays traced when
			computing indirect illumination ("bounce light").
			The number of actual diffuse rays traced is the
			square of this number.
			""",

			"layout:section", "Sampling",
			"label", "Diffuse Samples",

		],

		"options.giGlossySamples" : [

			"description",
			"""
			Controls the number of rays traced when
			computing glossy specular reflections.
			The number of actual specular rays traced
			is the square of this number.
			""",

			"layout:section", "Sampling",
			"label", "Glossy Samples",

		],

		"options.giRefractionSamples" : [

			"description",
			"""
			Controls the number of rays traced when
			computing refractions. The number of actual
			specular rays traced is the square of this number.
			""",

			"layout:section", "Sampling",
			"label", "Refraction Samples",

		],

		# Features

		"options.ignoreTextures" : [

			"description",
			"""
			Ignores all file textures, rendering as
			if they were all white.
			""",

			"layout:section", "Features",

		],

		"options.ignoreShaders" : [

			"description",
			"""
			Ignores all shaders, rendering as a
			simple facing ratio shader instead.
			""",

			"layout:section", "Features",

		],

		"options.ignoreAtmosphere" : [

			"description",
			"""
			Ignores all atmosphere shaders.
			""",

			"layout:section", "Features",

		],

		"options.ignoreLights" : [

			"description",
			"""
			Ignores all lights.
			""",

			"layout:section", "Features",

		],

		"options.ignoreShadows" : [

			"description",
			"""
			Skips all shadow calculations.
			""",

			"layout:section", "Features",

		],

		"options.ignoreSubdivision" : [

			"description",
			"""
			Treats all subdivision surfaces
			as simple polygon meshes instead.
			""",

			"layout:section", "Features",

		],

		"options.ignoreDisplacement" : [

			"description",
			"""
			Ignores all displacement shaders.
			""",

			"layout:section", "Features",

		],

		"options.ignoreBump" : [

			"description",
			"""
			Ignores all bump mapping.
			""",

			"layout:section", "Features",

		],

		"options.ignoreMotionBlur" : [

			"description",
			"""
			Ignores motion blur. Note that the turn
			off motion blur completely, it is more
			efficient to use the motion blur controls
			in the StandardOptions node.
			""",

			"layout:section", "Features",

		],

		"options.ignoreSSS" : [

			"description",
			"""
			Disables all subsurface scattering.
			""",

			"layout:section", "Features",

		],

		# Search Paths

		"options.textureSearchPath" : [

			"description",
			"""
			The locations used to search for texture
			files.
			""",

			"layout:section", "Search Paths",
			"label", "Textures",

		],

		"options.proceduralSearchPath" : [

			"description",
			"""
			The locations used to search for procedural
			DSOs.
			""",

			"layout:section", "Search Paths",
			"label", "Procedurals",

		],

		"options.shaderSearchPath" : [

			"description",
			"""
			The locations used to search for shader plugins.
			""",

			"layout:section", "Search Paths",
			"label", "Shaders",

		],

		# Error Colors

		"options.errorColorBadTexture" : [

			"description",
			"""
			The colour to display if an attempt is
			made to use a bad or non-existent texture.
			""",

			"layout:section", "Error Colors",
			"label", "Bad Texture",

		],

		"options.errorColorBadMesh" : [

			"description",
			"""
			The colour to display if bad geometry
			is encountered.
			""",

			"layout:section", "Error Colors",
			"label", "Bad Mesh",

		],

		"options.errorColorBadPixel" : [

			"description",
			"""
			The colour to display for a pixel where
			a NaN is encountered.
			""",

			"layout:section", "Error Colors",
			"label", "Bad Pixel",

		],

		"options.errorColorBadShader" : [

			"description",
			"""
			The colour to display if a problem occurs
			in a shader.
			""",

			"layout:section", "Error Colors",
			"label", "Bad Shader",

		],

	}

)
