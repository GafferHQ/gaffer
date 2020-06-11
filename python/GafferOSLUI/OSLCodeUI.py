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
import imath

import IECore

import Gaffer
import GafferUI
import GafferOSL

from . import _CodeMenu

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
			- ClosurePlug (`closure color`)
			- SplinefColor3f ( triplet of `float [], color [], string` )
			""",

			"layout:customWidget:footer:widgetType", "GafferOSLUI.OSLCodeUI._ParametersFooter",
			"layout:customWidget:footer:index", -1,
			"layout:section", "Settings.Inputs",

		],

		"parameters.*" : [

			"renameable", True,
			"deletable", True,
			# Since the names are used directly as variable names in the code,
			# it's best to avoid any fancy label formatting for them.
			"label", lambda plug : plug.getName(),

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

			"renameable", True,
			"deletable", True,
			"label", lambda plug : plug.getName(),

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

				GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

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

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

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
			( "Closure", GafferOSL.ClosurePlug )
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
								( 0, imath.Color3f( 0 ) ),
								( 0, imath.Color3f( 0 ) ),
								( 1, imath.Color3f( 1 ) ),
								( 1, imath.Color3f( 1 ) ),
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

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild( plug )

##########################################################################
# _CodePlugValueWidget
##########################################################################

class _CodePlugValueWidget( GafferUI.MultiLineStringPlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		GafferUI.MultiLineStringPlugValueWidget.__init__( self, plug, **kw )

		self.textWidget().setRole( GafferUI.MultiLineTextWidget.Role.Code )

		self.textWidget().dropTextSignal().connect( Gaffer.WeakMethod( self.__dropText ), scoped = False )

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

		node.errorSignal().connect( Gaffer.WeakMethod( self.__error ), scoped = False )
		node.shaderCompiledSignal().connect( Gaffer.WeakMethod( self.__shaderCompiled ), scoped = False )

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

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	node = plug.node()
	if not isinstance( node, GafferOSL.OSLCode ) :
		return

	if plug.isSame( node["code"] ) :

		if len( menuDefinition.items() ) :
			menuDefinition.prepend( "/InsertDivider", { "divider" : True } )

		menuDefinition.prepend(
			"/Insert",
			{
				"subMenu" : functools.partial(
					_CodeMenu.commonFunctionMenu,
					command = plugValueWidget.textWidget().insertText,
					activator = lambda : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( plug ),
				),
			},
		)

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu, scoped = False )

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

GafferUI.NodeEditor.toolMenuSignal().connect( __toolMenu, scoped = False )
