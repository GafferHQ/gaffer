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

import copy
import functools
import imath

import IECore

import PyOpenColorIO as OCIO

import Gaffer
import GafferUI
import GafferImage
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
Gaffer.Metadata.registerValue( preferences["displayColorSpace"]["context"], "layout:customWidget:addButton:widgetType", "GafferImageUI.OpenColorIOTransformUI._ContextFooter", persistent = False )
Gaffer.Metadata.registerValue( preferences["displayColorSpace"]["context"], "layout:customWidget:addButton:index", -1, persistent = False )

# Register with `GafferUI.DisplayTransform` for use by Widgets.

def __processor( view ) :

	d = OCIO.DisplayViewTransform()
	d.setSrc( OCIO.ROLE_SCENE_LINEAR )
	d.setDisplay( defaultDisplay )
	d.setView( view )

	context = copy.deepcopy( config.getCurrentContext() )
	gafferContext = Gaffer.Context.current()
	for variable in preferences["displayColorSpace"]["context"] :
		if variable["enabled"].getValue() :
			context[ variable["name"].getValue() ] = gafferContext.substitute( variable["value"].getValue() )

	return config.getProcessor( transform = d, context = context, direction = OCIO.TRANSFORM_DIR_FORWARD )

def __setDisplayTransform() :

	cpuProcessor = __processor( preferences["displayColorSpace"]["view"].getValue() ).getDefaultCPUProcessor()

	def f( c ) :

		cc = cpuProcessor.applyRGB( [ c.r, c.g, c.b ] )
		return imath.Color3f( *cc )

	GafferUI.DisplayTransform.set( f )

__setDisplayTransform()

# Register with `GafferUI.View.DisplayTransform` for use in the Viewer.

def __displayTransformCreator( view ) :

	processor = __processor( view )
	return GafferImageUI.OpenColorIOAlgo.displayTransformToFramebufferShader( processor )

def __registerViewerDisplayTransforms() :

	for name in config.getViews( defaultDisplay ) :
		GafferUI.View.DisplayTransform.registerDisplayTransform(
			name,
			functools.partial( __displayTransformCreator, name )
		)

	GafferUI.View.DisplayTransform.registerDisplayTransform(
		"Default",
		functools.partial( __displayTransformCreator, preferences["displayColorSpace"]["view"].getValue() )
	)

__registerViewerDisplayTransforms()

# And connect to `plugSet()` to update everything again when the user modifies something.

def __plugSet( plug ) :

	if plug.relativeName( plug.node() ) != "displayColorSpace" :
		return

	__registerViewerDisplayTransforms()
	__setDisplayTransform()

preferences.plugSetSignal().connect( __plugSet, scoped = False )

Gaffer.Metadata.registerValue( GafferUI.View, "displayTransform.name", "userDefault", "Default" )

# Add "Roles" submenus to various colorspace plugs. The OCIO UX guidelines suggest we
# shouldn't do this, but they do seem like they might be useful, and historically they
# have been available in Gaffer. They can be disabled by overwriting the metadata in
# a custom config file.

for node, plug in [
	( GafferImage.ColorSpace, "inputSpace" ),
	( GafferImage.ColorSpace, "outputSpace" ),
	( GafferImage.DisplayTransform, "inputColorSpace" ),
	( GafferImage.ImageReader, "colorSpace" ),
	( GafferImage.ImageWriter, "colorSpace" ),
] :
	Gaffer.Metadata.registerValue( node, plug, "openColorIO:includeRoles", True )
