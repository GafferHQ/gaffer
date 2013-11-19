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
preferences["displayColorSpace"] = Gaffer.CompoundPlug()
preferences["displayColorSpace"]["view"] = Gaffer.StringPlug( defaultValue = config.getDefaultView( defaultDisplay ) )

# configure ui for preferences plugs

GafferUI.PlugValueWidget.registerCreator(
	Gaffer.Preferences.staticTypeId(),
	"displayColorSpace.view",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = zip( config.getViews( defaultDisplay ), config.getViews( defaultDisplay ) ),
)

# update the display transform from the plugs

def __setDisplayTransform() :

	view = preferences["displayColorSpace"]["view"].getValue()
	colorSpace = config.getDisplayColorSpaceName( defaultDisplay, view )
	processor = config.getProcessor( OCIO.Constants.ROLE_SCENE_LINEAR, colorSpace )
	
	def f( c ) :
	
		cc = processor.applyRGB( [ c.r, c.g, c.b ] )
		return IECore.Color3f( *cc )
		
	GafferUI.DisplayTransform.set( f )

__setDisplayTransform()
	
# and connect to plug changed to update things again when the user asks

def __plugSet( plug ) :
	
	if plug.relativeName( plug.node() ) != "displayColorSpace" :
		return
	
	__setDisplayTransform()
	__updateDefaultDisplayTransforms()
	
application.__ocioPlugSetConnection = preferences.plugSetSignal().connect( __plugSet )

# register display transforms with the image viewer

def __displayTransformCreator( name ) :

	result = GafferImage.OpenColorIO()
	result["inputSpace"].setValue( "linear" )
	result["outputSpace"].setValue( config.getDisplayColorSpaceName( defaultDisplay, name ) )
	
	return result

for name in config.getViews( defaultDisplay ) :
	GafferImageUI.ImageView.registerDisplayTransform( name, IECore.curry( __displayTransformCreator, name ) )

# and register a special "Default" display transform which tracks the
# global settings from the preferences

__defaultDisplayTransforms = []

def __updateDefaultDisplayTransforms() :

	view = preferences["displayColorSpace"]["view"].getValue()
	colorSpace = config.getDisplayColorSpaceName( defaultDisplay, view )
	for node in __defaultDisplayTransforms :
		node["outputSpace"].setValue( colorSpace )

def __defaultDisplayTransformCreator() :

	result = GafferImage.OpenColorIO()
	result["inputSpace"].setValue( "linear" )
	
	__defaultDisplayTransforms.append( result )
	__updateDefaultDisplayTransforms()
		
	return result

GafferImageUI.ImageView.registerDisplayTransform( "Default", __defaultDisplayTransformCreator )
