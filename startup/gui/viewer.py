##########################################################################
#
#  Copyright (c) 2014, John Haddon. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

# add plugs to the preferences node

preferences = application.root()["preferences"]
preferences["viewer"] = Gaffer.Plug()
preferences["viewer"]["gridDimensions"] = Gaffer.V2fPlug( defaultValue = IECore.V2f( 10 ), minValue = IECore.V2f( 0 ) )

Gaffer.Metadata.registerValue( preferences["viewer"], "plugValueWidget:type", "GafferUI.LayoutPlugValueWidget", persistent = False )
Gaffer.Metadata.registerValue( preferences["viewer"], "layout:section", "Viewer", persistent = False )

# register a customised view for viewing scenes

def __sceneView( plug ) :

	view = GafferSceneUI.SceneView()
	view["in"].setInput( plug )
	view["grid"]["dimensions"].setInput( preferences["viewer"]["gridDimensions"] )

	return view

GafferUI.View.registerView( GafferScene.ScenePlug.staticTypeId(), __sceneView )

# register shading modes

def __createNode( nodeType, plugValues ) :

	node = nodeType()
	for name, value in plugValues.items() :
		node.descendant( name ).setValue( value )

	return node

def __registerShadingModes( modes ) :

	for name, nodeType, plugValues in modes :
		GafferSceneUI.SceneView.registerShadingMode(
			name,
			functools.partial(
				__createNode,
				nodeType,
				plugValues,
			)
		)

with IECore.IgnoredExceptions( ImportError ) :

	import GafferArnold

	__registerShadingModes( [

		( "Diagnostic/Arnold/Shader Assignment", GafferScene.AttributeVisualiser, { "attributeName" : "ai:surface", "mode" : GafferScene.AttributeVisualiser.Mode.ShaderNodeColor } ),
		( "Diagnostic/Arnold/Camera Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "ai:visibility:camera" } ),
		( "Diagnostic/Arnold/Shadow Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "ai:visibility:shadow" } ),
		( "Diagnostic/Arnold/Reflection Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "ai:visibility:reflected" } ),
		( "Diagnostic/Arnold/Refraction Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "ai:visibility:refracted" } ),
		( "Diagnostic/Arnold/Diffuse Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "ai:visibility:diffuse" } ),
		( "Diagnostic/Arnold/Glossy Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "ai:visibility:glossy" } ),

	] )

with IECore.IgnoredExceptions( ImportError ) :

	import GafferAppleseed

	__registerShadingModes( [

		( "Diagnostic/Appleseed/Shader Assignment", GafferScene.AttributeVisualiser, { "attributeName" : "osl:surface", "mode" : GafferScene.AttributeVisualiser.Mode.ShaderNodeColor } ),
		( "Diagnostic/Appleseed/Camera Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "as:visibility:camera" } ),
		( "Diagnostic/Appleseed/Shadow Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "as:visibility:shadow" } ),
		( "Diagnostic/Appleseed/Diffuse Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "as:visibility:diffuse" } ),
		( "Diagnostic/Appleseed/Specular Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "as:visibility:specular" } ),
		( "Diagnostic/Appleseed/Glossy Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "as:visibility:glossy" } ),
		( "Diagnostic/Appleseed/Photon Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "as:visibility:light" } ),

	] )
