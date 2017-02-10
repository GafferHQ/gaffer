##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import os
import functools

import IECore

import Gaffer
import GafferUI
import GafferOSL

Gaffer.Metadata.registerNode(

	GafferOSL.OSLCode,

	"description",
	"""
	Allows arbitrary OSL shaders to be written directly within
	Gaffer.
	""",

	"layout:customWidget:error:widgetType", "GafferOSLUI.OSLCodeUI._ErrorWidget",
	"layout:customWidget:error:section", "Settings.Code",
	"layout:customWidget:error:index", -1,

	"layout:section:Settings.Inputs:collapsed", False,
	"layout:section:Settings.Outputs:collapsed", False,
	"layout:section:Settings.Code:collapsed", False,

	plugs = {

		"name" : [

			"description", "Generated automatically - do not edit.",
			"plugValueWidget:type", "",

		],

		"type" : [

			"description", "Generated automatically - do not edit.",
			"plugValueWidget:type", "",

		],

		"parameters" : [

			"description",
			"""
			The inputs to the shader. Any number of inputs may be created
			by adding child plugs. Supported plug types and the corresponding
			OSL types are :

			- FloatPlug (`float`)
			- IntPlug (`int`)
			- ColorPlug (`color`)
			- V3fPlug (`vector`)
			- M44fPlug (`matrix`)
			- StringPlug (`string`)
			- Plug (`closure color`)
			- SplinefColor3f ( triplet of `float [], color [], string` )
			""",

			"layout:customWidget:footer:widgetType", "GafferOSLUI.OSLCodeUI._ParametersFooter",
			"layout:customWidget:footer:index", -1,
			"layout:section", "Settings.Inputs",

		],

		"parameters.*" : [

			"labelPlugValueWidget:renameable", True,

		],

		"out" : [

			"description",
			"""
			The outputs from the shader. Any number of outputs may be created
			by adding child plugs. Supported plug types are as for the input
			parameters, with the exception of SplinefColor3f, which cannot be
			used as an output.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

			"layout:customWidget:footer:widgetType", "GafferOSLUI.OSLCodeUI._ParametersFooter",
			"layout:customWidget:footer:index", -1,
			"layout:section", "Settings.Outputs",

		],

		"out.*" : [

			"labelPlugValueWidget:renameable", True,

		],

		"code" : [

			"description",
			"""
			The code for the body of the OSL shader. This should read from the
			input parameters and write to the output parameters.
			""",

			"nodule:type", "",
			"plugValueWidget:type", "GafferOSLUI.OSLCodeUI._CodePlugValueWidget",
			"multiLineStringPlugValueWidget:role", "code",
			"layout:label", "",
			"layout:section", "Settings.Code",

		],

	}

)

##########################################################################
# _ParametersFooter
##########################################################################

class _ParametersFooter( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :

				GafferUI.Spacer( IECore.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

				menuButton = GafferUI.MenuButton(
					image = "plus.png",
					hasFrame = False,
					menu = GafferUI.Menu(
						Gaffer.WeakMethod( self.__menuDefinition ),
						title = "Add " + ( "Input" if plug.direction() == plug.Direction.In else "Output" )
					),
					toolTip = "Add " + ( "Input" if plug.direction() == plug.Direction.In else "Output" ),
				)
				menuButton.setEnabled( not Gaffer.MetadataAlgo.readOnly( plug ) )

				GafferUI.Spacer( IECore.V2i( 1 ), IECore.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def _updateFromPlug( self ) :

		self.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		labelsAndConstructors = [
			( "Int", Gaffer.IntPlug ),
			( "Float", Gaffer.FloatPlug ),
			( "Vector", functools.partial( Gaffer.V3fPlug, interpretation = IECore.GeometricData.Interpretation.Vector ) ),
			( "Normal", functools.partial( Gaffer.V3fPlug, interpretation = IECore.GeometricData.Interpretation.Normal ) ),
			( "Point", functools.partial( Gaffer.V3fPlug, interpretation = IECore.GeometricData.Interpretation.Point ) ),
			( "Color", Gaffer.Color3fPlug ),
			( "Matrix", Gaffer.M44fPlug ),
			( "String", Gaffer.StringPlug ),
			( "Closure", Gaffer.Plug )
		]

		if self.getPlug().direction() == Gaffer.Plug.Direction.In :

			labelsAndConstructors.insert(
				-1,
				( "Color Spline",
					functools.partial(
						Gaffer.SplinefColor3fPlug,
						defaultValue = IECore.SplinefColor3f(
							IECore.CubicBasisf.catmullRom(),
							(
								( 0, IECore.Color3f( 0 ) ),
								( 0, IECore.Color3f( 0 ) ),
								( 1, IECore.Color3f( 1 ) ),
								( 1, IECore.Color3f( 1 ) ),
							)
						)
					)
				)
			)

		for label, constructor in labelsAndConstructors :

			result.append(
				"/" + label,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), constructor ),
				}
			)

		return result

	def __addPlug( self, plugConstructor ) :

		direction = self.getPlug().direction()
		plug = plugConstructor(
			name = "input1" if direction == Gaffer.Plug.Direction.In else "output1",
			direction = self.getPlug().direction(),
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)

		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild( plug )

##########################################################################
# _CodePlugValueWidget
##########################################################################

class _CodePlugValueWidget( GafferUI.MultiLineStringPlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		GafferUI.MultiLineStringPlugValueWidget.__init__( self, plug, **kw )

		self.textWidget().setRole( GafferUI.MultiLineTextWidget.Role.Code )

		self.__dropTextConnection = self.textWidget().dropTextSignal().connect( Gaffer.WeakMethod( self.__dropText ) )

	def __dropText( self, widget, dragData ) :

		if not isinstance( dragData, Gaffer.Plug ) :
			return None

		plug = dragData
		node = plug.node()
		if plug.parent() not in ( node["parameters"], node["out"] ) :
			return None

		if isinstance( plug, Gaffer.SplinefColor3fPlug ) :
			return "colorSpline( {0}Positions, {0}Values, {0}Basis, u )".format( plug.getName() )

		return plug.getName()

##########################################################################
# _ErrorWidget
##########################################################################

class _ErrorWidget( GafferUI.Widget ) :

	def __init__( self, node, **kw ) :

		self.__messageWidget = GafferUI.MessageWidget()
		GafferUI.Widget.__init__( self, self.__messageWidget, **kw )

		self.__errorConnection = node.errorSignal().connect( Gaffer.WeakMethod( self.__error ) )
		self.__shaderCompiledConnection = node.shaderCompiledSignal().connect( Gaffer.WeakMethod( self.__shaderCompiled ) )

		self.__messageWidget.setVisible( False )

	def __error( self, plug, source, error ) :

		self.__messageWidget.clear()
		self.__messageWidget.messageHandler().handle( IECore.Msg.Level.Error, "Compilation error", error )
		self.__messageWidget.setVisible( True )

	def __shaderCompiled( self ) :

		self.__messageWidget.setVisible( False )

##########################################################################
# Plug menu
##########################################################################

## \todo This functionality is duplicated in several places (NodeUI,
#  BoxUI, CompoundDataPlugValueWidget). It would be better if we could
#  just control it in one place with a "plugValueWidget:removeable"
#  metadata value. This main reason we can't do that right now is that
#  we'd want to register the metadata with "parameters.*", but that would
#  match "parameters.vector.x" as well as "parameters.vector". This is
#  a general problem we have with the metadata matching - we should make
#  '.' unmatchable by '*'.
def __deletePlug( plug ) :

	with Gaffer.UndoContext( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.parent().removeChild( plug )

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	node = plug.node()
	if not isinstance( node, GafferOSL.OSLCode ) :
		return

	if plug.parent() in ( node["parameters"], node["out"] ) :

		menuDefinition.append( "/DeleteDivider", { "divider" : True } )
		menuDefinition.append(
			"/Delete",
			{
				"command" : IECore.curry( __deletePlug, plug ),
				"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( plug )
			}
		)

	elif plug.isSame( node["code"] ) :

		for label, text in reversed( [

			( "/Math/Constants/Pi", "M_PI" ),
			( "/Math/Angles/Radians", "radians( angleInDegrees )" ),
			( "/Math/Angles/Degrees", "degrees( angleInRadians )" ),
			( "/Math/Trigonometry/Sin", "sin( angleInRadians )" ),
			( "/Math/Trigonometry/Cosine", "cos( angleInRadians )" ),
			( "/Math/Trigonometry/Tangent", "tan( angleInRadians )" ),
			( "/Math/Trigonometry/Arc Sin", "asin( y )" ),
			( "/Math/Trigonometry/Arc Cosine", "acos( x )" ),
			( "/Math/Trigonometry/Arc Tangent", "atan( yOverX )" ),
			( "/Math/Trigonometry/Arc Tangent 2", "atan2( y, x )" ),
			( "/Math/Exponents/Pow", "pow( x, y )" ),
			( "/Math/Exponents/Exp", "exp( x )" ),
			( "/Math/Exponents/Log", "log( x )" ),
			( "/Math/Exponents/Square Root", "sqrt( x )" ),
			( "/Math/Utility/Abs", "abs( x )" ),
			( "/Math/Utility/Sign", "sign( x )" ),
			( "/Math/Utility/Floor", "floor( x )" ),
			( "/Math/Utility/Ceil", "ceil( x )" ),
			( "/Math/Utility/Round", "round( x )" ),
			( "/Math/Utility/Trunc", "trunc( x )" ),
			( "/Math/Utility/Mod", "mod( x )" ),
			( "/Math/Utility/Min", "min( a, b )" ),
			( "/Math/Utility/Max", "max( a, b )" ),
			( "/Math/Utility/Clamp", "clamp( x, minValue, maxValue )" ),
			( "/Math/Utility/Mix", "mix( a, b, alpha )" ),
			( "/Math/Geometry/Dot", "dot( a, b )" ),

			( "/Geometry/Cross", "cross( a, b )" ),
			( "/Geometry/Length", "length( V )" ),
			( "/Geometry/Length", "distance( p0, p1 )" ),
			( "/Geometry/Normalize", "normalize( V )" ),
			( "/Geometry/Face Forward", "faceforward( N, I )" ),
			( "/Geometry/Reflect", "reflect( I, N )" ),
			( "/Geometry/Refract", "refract( I, N, eta )" ),
			( "/Geometry/Rotate", "rotate( p, angle, p0, p1 )" ),
			( "/Geometry/Transform", "transform( toSpace, p )" ),
			( "/Geometry/Transform", "transform( fromSpace, toSpace, p )" ),

			( "/Color/Luminance", "luminance( c )" ),
			( "/Color/BlackBody", "blackbody( degreesKelvin )" ),
			( "/Color/Wavelength Color", "wavelength_color( wavelengthNm )" ),
			( "/Color/Transform", "transformc( fromSpace, toSpace, c )" ),

			( "/Pattern/Step", "step( edge, x )" ),
			( "/Pattern/Linear Step", "linearstep( edge0, edge1, x )" ),
			( "/Pattern/Smooth Step", "smoothstep( edge0, edge1, x )" ),
			( "/Pattern/Noise", "noise( \"perlin\", p )" ),
			( "/Pattern/Periodic Noise", "noise( \"perlin\", p, period )" ),
			( "/Pattern/Cell Noise", "cellnoise( p )" ),

			( "/String/Length", "length( str )" ),
			( "/String/Format", "format( \"\", ... )" ),
			( "/String/Join", "concat( str0, str1 )" ),
			( "/String/Split", "split( str, results )" ),
			( "/String/Starts With", "startswith( str, prefix )" ),
			( "/String/Ends With", "endswith( str, suffix )" ),
			( "/String/Substring", "substr( str, start, length )" ),
			( "/String/Get Char", "getchar( str, n )" ),
			( "/String/Hash", "hash( str )" ),

			( "/Texture/Texture", "texture( filename, s, t )" ),
			( "/Texture/Environment", "environment( filename, R )" ),

			( "/Parameter/Is Connected", "isconnected( parameter )" ),
			( "/Parameter/Is Constant", "isconstant( parameter )" ),

		] ) :

			menuDefinition.prepend( "/InsertDivider", { "divider" : True } )

			menuDefinition.prepend(
				"/Insert" + label,
				{
					"command" : functools.partial( plugValueWidget.textWidget().insertText, text ),
					"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( plug ),
				},
			)

__plugPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )

##########################################################################
# NodeEditor tool menu
##########################################################################

def __toolMenu( nodeEditor, node, menuDefinition ) :

	if not isinstance( node, GafferOSL.OSLCode ) :
		return

	menuDefinition.append( "/ExportDivider", { "divider" : True } )
	menuDefinition.append( "/Export OSL Shader...", { "command" : functools.partial( __exportOSLShader, nodeEditor, node ) } )

def __exportOSLShader( nodeEditor, node ) :

	bookmarks = GafferUI.Bookmarks.acquire( node, category="shader" )

	path = Gaffer.FileSystemPath( bookmarks.getDefault( nodeEditor ) )
	path.setFilter( Gaffer.FileSystemPath.createStandardFilter( [ "osl" ] ) )

	dialogue = GafferUI.PathChooserDialogue( path, title="Export OSL Shader", confirmLabel="Export", leaf=True, bookmarks=bookmarks )
	path = dialogue.waitForPath( parentWindow = nodeEditor.ancestor( GafferUI.Window ) )

	if not path :
		return

	path = str( path )
	if not path.endswith( ".osl" ) :
		path += ".osl"

	with GafferUI.ErrorDialogue.ErrorHandler( title = "Error Exporting Shader", parentWindow = nodeEditor.ancestor( GafferUI.Window ) ) :
		with open( path, "w" ) as f :
			with nodeEditor.getContext() :
				f.write( node.source( os.path.splitext( os.path.basename( path ) )[0] ) )

__nodeEditorToolMenuConnection = GafferUI.NodeEditor.toolMenuSignal().connect( __toolMenu )
