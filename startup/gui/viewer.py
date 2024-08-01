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
import imath
import inspect
import os

import IECore
import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI
import GafferImageUI

# add plugs to the preferences node

preferences = application.root()["preferences"]
preferences["viewer"] = Gaffer.Plug()
preferences["viewer"]["gridDimensions"] = Gaffer.V2fPlug( defaultValue = imath.V2f( 10 ), minValue = imath.V2f( 0 ) )

Gaffer.Metadata.registerValue( preferences["viewer"], "plugValueWidget:type", "GafferUI.LayoutPlugValueWidget", persistent = False )
Gaffer.Metadata.registerValue( preferences["viewer"], "layout:section", "Viewer", persistent = False )

# register a customised view for viewing scenes

def __sceneView( plug ) :

	view = GafferSceneUI.SceneView()
	view["in"].setInput( plug )
	view["grid"]["dimensions"].setInput( preferences["viewer"]["gridDimensions"] )

	return view

GafferUI.View.registerView( GafferScene.ScenePlug.staticTypeId(), __sceneView )

Gaffer.Metadata.registerValue( GafferSceneUI.SceneView, "drawingMode.includedPurposes.value", "userDefault", IECore.StringVectorData( [ "default", "proxy" ] ) )

# Add items to the viewer's right click menu

def __viewContextMenu( viewer, view, menuDefinition ) :

	GafferSceneUI.LightUI.appendViewContextMenuItems( viewer, view, menuDefinition )
	GafferSceneUI.SceneHistoryUI.appendViewContextMenuItems( viewer, view, menuDefinition )

GafferUI.Viewer.viewContextMenuSignal().connect( __viewContextMenu, scoped = False )

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

def __createXRayShader() :

	# ideally this could be any type of node (eg Box), but
	# SceneView seems to require a SceneProcessor.
	xray = GafferScene.SceneProcessor( "XRay" )
	xray["attributes"] = GafferScene.CustomAttributes()
	xray["attributes"]["attributes"].addChild( Gaffer.NameValuePlug( "gl:depthTest", Gaffer.BoolPlug( "value", defaultValue = False ), True, "depthTest" ) )
	xray["attributes"]["in"].setInput( xray["in"] )
	xray["assignment"] = GafferScene.ShaderAssignment()
	xray["assignment"]["in"].setInput( xray["attributes"]["out"] )
	xray["shader"] = GafferScene.OpenGLShader( "XRay" )
	xray["shader"]["name"].setValue( "xray" )
	xray["shader"]["type"].setValue( "gl:surface" )
	xray["shader"]["parameters"].addChild( Gaffer.StringPlug( "glFragmentSource", defaultValue = inspect.cleandoc(
		'''
		\\#if __VERSION__ <= 120
		\\#define in varying
		\\#endif

		in vec3 fragmentN;
		in vec3 fragmentI;

		void main()
		{
			float f = abs( dot( normalize( fragmentI ), normalize( fragmentN ) ) );
			gl_FragColor = vec4( mix( vec3( 0.7 ), vec3( 0.5 ), f ), 0.5 );
		}
		'''
	) ) )
	xray["shader"]["out"] = Gaffer.Plug()
	xray["assignment"]["shader"].setInput( xray["shader"]["out"] )
	xray["out"].setInput( xray["assignment"]["out"] )

	return xray

GafferSceneUI.SceneView.registerShadingMode( "X-Ray", __createXRayShader )

def __createPurposeShadingMode() :

	result = GafferScene.SceneProcessor( "PurposeVisualiser" )

	result["attributeQuery"] = GafferScene.AttributeQuery()
	result["attributeQuery"].setup( Gaffer.StringPlug() )
	result["attributeQuery"]["scene"].setInput( result["in"] )
	result["attributeQuery"]["location"].setValue( "${scene:path}" )
	result["attributeQuery"]["attribute"].setValue( "usd:purpose" )
	result["attributeQuery"]["default"].setValue( "default" )
	result["attributeQuery"]["inherit"].setValue( True )

	result["customAttributes"] = GafferScene.CustomAttributes()
	result["customAttributes"]["in"].setInput( result["in"] )

	result["spreadsheet"] = Gaffer.Spreadsheet()
	result["spreadsheet"]["selector"].setInput( result["attributeQuery"]["value"] )
	result["spreadsheet"]["rows"].addColumn( result["customAttributes"]["extraAttributes"] )

	result["customAttributes"]["extraAttributes"].setInput( result["spreadsheet"]["out"]["extraAttributes"] )

	for purpose, color in {
		"render" : imath.Color3f( 0, 1, 0 ),
		"proxy" : imath.Color3f( 0, 0, 1 ),
		"guide" : imath.Color3f( 1, 0, 0 ),
		"default" : imath.Color3f( 1, 1, 1 )
	}.items() :
		row = result["spreadsheet"]["rows"].addRow()
		row["name"].setValue( purpose )
		row["cells"]["extraAttributes"]["value"].setValue(
			IECore.CompoundObject( {
				"gl:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"surface" : IECoreScene.Shader(
							"FacingRatio", "gl:surface",
							{ "facingColor" : color },
						)
					},
					output = "surface",
				)
			} )
		)

	result["out"].setInput( result["customAttributes"]["out"] )

	return result

GafferSceneUI.SceneView.registerShadingMode( "Diagnostic/USD/Purpose", __createPurposeShadingMode )

def __loadRendererSettings( fileName ) :

	script = Gaffer.ScriptNode()
	script["fileName"].setValue( fileName )
	script.load()

	script["Processor"] = GafferScene.SceneProcessor()
	script.execute( script.serialise( parent = script["ViewerSettings"] ), parent = script["Processor"] )
	script["Processor"]["BoxIn"]["__in"].setInput( script["Processor"]["in"] )
	script["Processor"]["out"].setInput( script["Processor"]["BoxOut"]["__out"] )
	for plug in Gaffer.ValuePlug.InputRange( script["Processor"] ) :
		plug.setToDefault()

	return script["Processor"]

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
		( "Diagnostic/Arnold/Matte", GafferScene.AttributeVisualiser, { "attributeName" : "ai:matte" } ),
		( "Diagnostic/Arnold/Opaque", GafferScene.AttributeVisualiser, { "attributeName" : "ai:opaque" } ),
		( "Diagnostic/Arnold/Receive Shadows", GafferScene.AttributeVisualiser, { "attributeName" : "ai:receive_shadows" } ),
		( "Diagnostic/Arnold/Self Shadows", GafferScene.AttributeVisualiser, { "attributeName" : "ai:self_shadows" } ),

	] )

	GafferSceneUI.SceneView.registerRenderer(
		"Arnold",
		functools.partial( __loadRendererSettings, os.path.join( os.path.dirname( __file__ ), "arnoldViewerSettings.gfr" ) )
	)

with IECore.IgnoredExceptions( ImportError ) :

	import GafferDelight

	__registerShadingModes( [

		( "Diagnostic/3Delight/Shader Assignment", GafferScene.AttributeVisualiser, { "attributeName" : "osl:surface", "mode" : GafferScene.AttributeVisualiser.Mode.ShaderNodeColor } ),
		( "Diagnostic/3Delight/Camera Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "dl:visibility.camera" } ),
		( "Diagnostic/3Delight/Shadow Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "dl:visibility.shadow" } ),
		( "Diagnostic/3Delight/Reflection Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "dl:visibility.reflection" } ),
		( "Diagnostic/3Delight/Refraction Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "dl:visibility.refraction" } ),
		( "Diagnostic/3Delight/Diffuse Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "dl:visibility.diffuse" } ),
		( "Diagnostic/3Delight/Specular Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "dl:visibility.specular" } ),
		( "Diagnostic/3Delight/Hair Visibility", GafferScene.AttributeVisualiser, { "attributeName" : "dl:visibility.hair" } ),

	] )

	GafferSceneUI.SceneView.registerRenderer(
		"3Delight",
		functools.partial( __loadRendererSettings, os.path.join( os.path.dirname( __file__ ), "3delightViewerSettings.gfr" ) )
	)

if os.environ.get( "CYCLES_ROOT" ) and os.environ.get( "GAFFERCYCLES_HIDE_UI", "" ) != "1" :

	with IECore.IgnoredExceptions( ImportError ) :

		import GafferCycles

		GafferSceneUI.SceneView.registerRenderer(
			"Cycles",
			functools.partial( __loadRendererSettings, os.path.join( os.path.dirname( __file__ ), "cyclesViewerSettings.gfr" ) )
		)

# Add catalogue hotkeys to viewers, eg: up/down navigation
GafferUI.Editor.instanceCreatedSignal().connect( GafferImageUI.CatalogueUI.addCatalogueHotkeys, scoped = False )
GafferUI.Editor.instanceCreatedSignal().connect( GafferSceneUI.EditScopeUI.addPruningActions, scoped = False )
GafferUI.Editor.instanceCreatedSignal().connect( GafferSceneUI.EditScopeUI.addVisibilityActions, scoped = False )
