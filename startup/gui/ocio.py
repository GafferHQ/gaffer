##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

import functools
import imath

import IECore

import GafferImage # this sets the OCIO environment variable
import PyOpenColorIO as OCIO

import Gaffer
import GafferUI
import GafferImageUI

# get default display setup

config = OCIO.GetCurrentConfig()
defaultDisplay = config.getDefaultDisplay()

# add preferences plugs

preferences = application.root()["preferences"]
preferences["displayColorSpace"] = Gaffer.Plug()
preferences["displayColorSpace"]["view"] = Gaffer.StringPlug( defaultValue = config.getDefaultView( defaultDisplay ) )
preferences["displayColorSpace"]["context"] = Gaffer.CompoundDataPlug()

# configure ui for preferences plugs

Gaffer.Metadata.registerValue( preferences["displayColorSpace"], "plugValueWidget:type", "GafferUI.LayoutPlugValueWidget", persistent = False )
Gaffer.Metadata.registerValue( preferences["displayColorSpace"], "layout:section", "Display Color Space", persistent = False )

Gaffer.Metadata.registerValue( preferences["displayColorSpace"]["view"], "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget", persistent = False )
for view in config.getViews( defaultDisplay ) :
	Gaffer.Metadata.registerValue( preferences["displayColorSpace"]["view"], str( "preset:" + view ), view, persistent = False )

Gaffer.Metadata.registerValue( preferences["displayColorSpace"]["context"], "plugValueWidget:type", "GafferUI.LayoutPlugValueWidget", persistent = False )
Gaffer.Metadata.registerValue( preferences["displayColorSpace"]["context"], "layout:section", "OCIO Context", persistent = False )
Gaffer.Metadata.registerValue( preferences["displayColorSpace"], "layout:section:OCIO Context:collapsed", False, persistent = False )
Gaffer.Metadata.registerValue( preferences["displayColorSpace"]["context"], "layout:customWidget:addButton:widgetType", "GafferImageUI.OpenColorIOTransformUI._ContextFooter" )
Gaffer.Metadata.registerValue( preferences["displayColorSpace"]["context"], "layout:customWidget:addButton:index", -1 )

# update the display transform from the plugs

def __setDisplayTransform() :

	d = OCIO.DisplayViewTransform()
	d.setSrc( OCIO.ROLE_SCENE_LINEAR )
	d.setDisplay( defaultDisplay )
	d.setView( preferences["displayColorSpace"]["view"].getValue() )

	# \todo : Should be `context = copy.deepcopy( config.getCurrentContext() )`
	# once https://github.com/AcademySoftwareFoundation/OpenColorIO/pull/1575 gets merged into OCIO2.1.2
	context = OCIO.Context( searchPaths = list( config.getCurrentContext().getSearchPaths() ), workingDir = config.getCurrentContext().getWorkingDir(), environmentMode = config.getCurrentContext().getEnvironmentMode(), stringVars = dict( config.getCurrentContext().getStringVars() ) )
	for variable in preferences["displayColorSpace"]["context"] :
		if variable["enabled"].getValue() :
			context[ variable["name"].getValue() ] = variable["value"].getValue()

	processor = config.getProcessor( transform = d, context = context, direction = OCIO.TRANSFORM_DIR_FORWARD )
	cpuProcessor = processor.getDefaultCPUProcessor()

	def f( c ) :

		cc = cpuProcessor.applyRGB( [ c.r, c.g, c.b ] )
		return imath.Color3f( *cc )

	GafferUI.DisplayTransform.set( f )

__setDisplayTransform()

# and connect to plug changed to update things again when the user asks

def __plugSet( plug ) :

	if plug.relativeName( plug.node() ) != "displayColorSpace" :
		return

	__setDisplayTransform()

preferences.plugSetSignal().connect( __plugSet, scoped = False )

# register display transforms with the image viewer

def __displayTransformCreator( name ) :

	result = GafferImage.DisplayTransform()
	result["channels"].setValue( "[RGB] *.[RGB]" )
	result["inputColorSpace"].setValue( config.getColorSpace( OCIO.ROLE_SCENE_LINEAR ).getName() )
	result["display"].setValue( defaultDisplay )
	result["view"].setValue( name )

	for plug in preferences["displayColorSpace"]["context"] :
		result["context"].addChild( plug.createCounterpart( plug.getName(), plug.Direction.In ) )
	result["context"].setInput( preferences["displayColorSpace"]["context"] )

	return result

for name in config.getViews( defaultDisplay ) :
	GafferImageUI.ImageView.registerDisplayTransform( name, functools.partial( __displayTransformCreator, name ) )

# and register a special "Default" display transform which tracks the
# global settings from the preferences

def __defaultDisplayTransformCreator() :

	result = __displayTransformCreator( "" )
	result["view"].setInput( preferences["displayColorSpace"]["view"] )

	return result

GafferImageUI.ImageView.registerDisplayTransform( "Default", __defaultDisplayTransformCreator )
