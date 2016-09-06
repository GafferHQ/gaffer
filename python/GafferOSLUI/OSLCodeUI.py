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
	"layout:customWidget:error:section", "Settings",
	"layout:customWidget:error:index", -1,

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

				GafferUI.MenuButton(
					image = "plus.png",
					hasFrame = False,
					menu = GafferUI.Menu(
						Gaffer.WeakMethod( self.__menuDefinition ),
						title = "Add " + ( "Input" if plug.direction() == plug.Direction.In else "Output" )
					),
					toolTip = "Add " + ( "Input" if plug.direction() == plug.Direction.In else "Output" )
				)

				GafferUI.Spacer( IECore.V2i( 1 ), IECore.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def _updateFromPlug( self ) :

		self.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		labelsAndConstructors = [
			( "Int", Gaffer.IntPlug ),
			( "Float", Gaffer.FloatPlug ),
			( "Vector", Gaffer.V3fPlug ),
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

	if plug.parent() not in ( node["parameters"], node["out"] ) :
		return

	menuDefinition.append( "/DeleteDivider", { "divider" : True } )
	menuDefinition.append( "/Delete", { "command" : IECore.curry( __deletePlug, plug ), "active" : not plugValueWidget.getReadOnly() } )

__plugPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )
