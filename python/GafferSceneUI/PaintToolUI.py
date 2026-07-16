##########################################################################
#
#  Copyright (c) 2026, Image Engine Design Inc. All rights reserved.
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

import imath
import functools

import IECore
import IECoreScene

import Gaffer
import GafferUI
import GafferSceneUI

from Qt import QtWidgets
from Qt import QtCore

from GafferUI.PlugValueWidget import sole

Gaffer.Metadata.registerNode(

	GafferSceneUI.PaintTool,

	"description",
	"""
	3D paint tool. Currently supports basic vertex paint.
	""",

	"viewer:shortCut", "Y",
	"viewer:shouldAutoActivate", False,
	"order", 9,
	"tool:exclusive", True,

	"nodeToolbar:top:type", "GafferUI.StandardNodeToolbar.top",
	"toolbarLayout:customWidget:StatusWidget:widgetType", "GafferSceneUI.PaintToolUI._StatusWidget",
	"toolbarLayout:customWidget:StatusWidget:section", "Top",

	"toolbarLayout:activator:colorValue", lambda node : node["variableType"].getValue() == IECore.Color3fVectorData.staticTypeId(),
	"toolbarLayout:activator:floatValue", lambda node : node["variableType"].getValue() == IECore.FloatVectorData.staticTypeId(),

	plugs = {

		"variableName" : {

			"description" :
			"""
			The name of the primitive variable to paint.
			""",

			"toolbarLayout:section" : "Bottom",
			"toolbarLayout:width" : 100,
			"plugValueWidget:type" : "GafferSceneUI.PaintToolUI._VariableSelect",

		},
		"mode" : {

			"description" :
			"""
			Use paint mode `Over` to overlay new values on a primvar. Use paint mode `Erase`
			to remove existing paint from the target EditScope.
			""",
			# \todo : Should we offer more modes? Add/subtract would be easy to add.

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:Over" : GafferSceneUI.PaintTool.PaintMode.Over,
			"preset:Erase" : GafferSceneUI.PaintTool.PaintMode.Erase,
			"toolbarLayout:width" : 70,
			"toolbarLayout:section" : "Bottom",

		},
		"size" : {

			"description" :
			"""
			The size of the brush.
			""",

			"toolbarLayout:section" : "Bottom",
			"toolbarLayout:width" : 45,

		},
		"colorValue" : {

			"description" :
			"""
			Specifies the color of the brush.
			""",

			"toolbarLayout:section" : "Bottom",
			"toolbarLayout:width" : 100,
			"toolbarLayout:visibilityActivator" : "colorValue",

		},
		"colorBackground" : {

			"description" :
			"""
			An alternate color. Press `G` to swap colors.
			""",

			"label" : "",
			"toolbarLayout:section" : "Bottom",
			"toolbarLayout:width" : 10,
			"plugValueWidget:type" : "GafferUI.ColorSwatchPlugValueWidget",
		},
		"floatValue" : {

			#TODO : After thinking about this, I think it might be clearer if this plug doesn't exist.
			# We could just use the average of colorValue when painting a float primvar?

			"description" :
			"""
			The value of the brush when painting a float primitive variable.
			""",

			"toolbarLayout:section" : "Bottom",
			"toolbarLayout:width" : 100,
			"toolbarLayout:visibilityActivator" : "floatValue",

		},
		"opacity" : {

			"description" :
			"""
			The opacity of the brush.
			""",

			"toolbarLayout:section" : "Bottom",
			"toolbarLayout:width" : 45,

		},
		"hardness" : {

			"description" :
			"""
			The hardness of the brush. 1 is completely hard, 0 means the whole brush is a smooth fade.
			""",

			"toolbarLayout:section" : "Bottom",
			"toolbarLayout:width" : 45,

		},
	}
)


class _VariableSelect( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		self.__menuButton = GafferUI.MenuButton( "Cs", menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plug )

	def _updateFromValues( self, values, exception ) :

			if len( values ) != 1:
				raise IECore.Exception( "Corrupt PaintTool UI" )
			self.__menuButton.setText( values[0] )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		for varName, varType in self.getPlug().node().targetVariableTypes().items():
			result.append(
				"/" + varName,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setVariable ), varName, varType.value ),
				}
			)

		result.append( "/CustomDivider", { "divider" : True } )
		result.append(
			"/Custom",
			{
				"command" : Gaffer.WeakMethod( self.__setCustomVariable )
			}
		)

		return result

	def __setVariable( self, varName, varType ) :
		if varType == 0:
			GafferUI.ErrorDialogue( "Inconsistent Primitive Variable Type", message = "Cannot paint variable across selection with mismatched types. Use \"custom\" variable selection if you want to overwrite the type." ).waitForButton()
			return

		self.getPlug().setValue( varName )
		self.getPlug().parent()["variableType"].setValue( varType )

	def __setCustomVariable( self ) :
		varName, varType =_CustomVariableDialogue().waitForClose( parentWindow = self.ancestor( GafferUI.Window ) )

		if varName:
			self.getPlug().setValue( varName )
			self.getPlug().parent()["variableType"].setValue( varType )



class _CustomVariableDialogue( GafferUI.Dialogue ) :

	def __init__( self ) :

		GafferUI.Dialogue.__init__( self, "Custom Variable", sizeMode=GafferUI.Window.SizeMode.Fixed )

		cont = GafferUI.ListContainer(
			GafferUI.ListContainer.Orientation.Vertical, spacing=4, borderWidth=0,
		)
		with cont:
			self.__textWidget = GafferUI.TextWidget( "custom" )
			self.__typeMenuButton = GafferUI.MenuButton( "Color3f", menu = GafferUI.Menu( Gaffer.WeakMethod( self.__typeMenuDefinition ) ) )


		self._setWidget( cont )

		self.__cancelButton = self._addButton( "Cancel" )
		self.__confirmButton = self._addButton( "OK" )

	def __typeMenuDefinition( self ) :
		result = IECore.MenuDefinition()
		result.append( "/Float", { "command" : functools.partial( Gaffer.WeakMethod( self.__setType ), "Float" ) } )
		result.append( "/Color3f", { "command" : functools.partial( Gaffer.WeakMethod( self.__setType ), "Color3f" ) } )
		return result

	def __setType( self, typeName ) :
		self.__typeMenuButton.setText( typeName )

	def waitForClose( self, **kw ) :

		button = self.waitForButton( **kw )
		if button is self.__confirmButton :
			typeId = IECore.Color3fVectorData.staticTypeId() if self.__typeMenuButton.getText() == "Color3f" else IECore.FloatVectorData.staticTypeId()
			return ( self.__textWidget.getText(), typeId )
		else :
			return ( "", 0 )

def _boldFormatter( graphComponents ) :

	with IECore.IgnoredExceptions( ValueError ) :
		## \todo Should the NameLabel ignore ScriptNodes and their ancestors automatically?
		scriptNodeIndex = [ isinstance( g, Gaffer.ScriptNode ) for g in graphComponents ].index( True )
		graphComponents = graphComponents[scriptNodeIndex+1:]

	return "<b>" + ".".join( g.getName() for g in graphComponents ) + "</b>"

def _distance( ancestor, descendant ) :

	result = 0
	while descendant is not None and descendant != ancestor :
		result += 1
		descendant = descendant.parent()

	return result

class _StatusWidget( GafferUI.Frame ) :

	def __init__( self, tool, **kw ) :

		GafferUI.Frame.__init__( self, borderWidth = 1, **kw )

		self.__tool = tool

		with self :
			with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal, spacing = 8 ) :

				with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal ) as self.__infoRow :
					GafferUI.Image( "infoSmall.png" )
					GafferUI.Spacer( size = imath.V2i( 4 ), maximumSize = imath.V2i( 4 ) )
					self.__infoLabel = GafferUI.Label( "" )
					self.__nameLabel = GafferUI.NameLabel( graphComponent = None, numComponents = 1000 )
					self.__nameLabel.setFormatter( _boldFormatter )

				with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) as self.__warningRow :
					GafferUI.Image( "warningSmall.png" )
					self.__warningLabel = GafferUI.Label( "" )

		self.__tool.statusChangedSignal().connect( Gaffer.WeakMethod( self.__update, fallbackResult = None ) )

		self.__update()

	def scriptNode( self ) : # For LazyMethod's `deferUntilPlaybackStops`

		return self.__tool.ancestor( GafferUI.View ).scriptNode()

	def getToolTip( self ) :

		toolTip = GafferUI.Frame.getToolTip( self )
		if toolTip :
			return toolTip

		editTargetPerPath = self.__tool.editTargetPerPath()
		if len( editTargetPerPath ) == 0:
			return ""

		result = ""
		for s in editTargetPerPath.items() :
			target = s[1]
			targetName = ""
			if target:
				targetName = target.relativeName( target.ancestor( Gaffer.ScriptNode ) )
			if result :
				result += "\n"
			result += "- Painting {0} using {1}".format( s[0], targetName )

		return result

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __update( self, *unused ) :

		if not self.__tool["active"].getValue() :
			# We're about to be made invisible so all our update
			# would do is cause unnecessary flickering in Qt's
			# redraw.
			return

		scene = self.__tool["__scene"].getInput()

		editTargets = self.__tool.editTargets()
		warnings = self.__tool.warnings()

		if len( editTargets ) or len( warnings ) :

			# Update info row to show what we're editing

			if not self.__tool.selectionEditable() :
				self.__infoRow.setVisible( False )
			elif len( editTargets ) == 1 :
				self.__infoRow.setVisible( True )
				self.__infoLabel.setText( "Editing " )
				editTarget = next( iter( editTargets ) )

				numComponents = _distance(
					editTarget.commonAncestor( scene ),
					editTarget,
				)
				if scene.isAncestorOf( editTarget ) :
					numComponents += 1
				self.__nameLabel.setNumComponents( numComponents )
				self.__nameLabel.setGraphComponent( editTarget )
			else :
				self.__infoRow.setVisible( True )
				self.__infoLabel.setText( "Editing {0} transforms".format( len( editTargets ) ) )
				self.__nameLabel.setGraphComponent( None )

			# Update warning row

			if warnings :
				if len( warnings ) == 1 :
					self.__warningLabel.setText( next( iter( warnings ) ) )
					self.__warningRow.setToolTip( "" )
				else :
					self.__warningLabel.setText( "{} warnings".format( len( warnings ) ) )
					self.__warningRow.setToolTip( "\n".join( "- " + w for w in warnings ) )
				self.__warningRow.setVisible( True )
			else :
				self.__warningRow.setVisible( False )

		else :

			self.__infoRow.setVisible( True )
			self.__warningRow.setVisible( False )
			self.__infoLabel.setText( "Select something to paint. Ctrl and Shift modifiers can be used to change selection in the viewport while PaintTool is active." )
			self.__nameLabel.setGraphComponent( None )

GafferUI.Pointer.registerPointer( "invisible", GafferUI.Pointer( "pointerInvisible.png", imath.V2i( 0, 0 ) ) )

class ColorChooserWindow( GafferUI.PopupWindow ) :

	def __init__( self ) :

		self.__colorChooserWidget = GafferUI.ColorChooser()

		GafferUI.PopupWindow.__init__( self, "Select Color", child = self.__colorChooserWidget )

		self.keyReleaseSignal().connect( Gaffer.WeakMethod( self.__keyRelease ) )

	def popup( self, colorPlug ):
		self.__colorPlug = colorPlug
		value = colorPlug.getValue()
		if isinstance( value, float ):
			value = imath.Color3f( value )
		self.__colorChooserWidget.setColor( value )
		GafferUI.PopupWindow.popup( self )


	def __keyRelease( self, qObject, event ):
		if event.key == "J" :

			if isinstance( self.__colorPlug, Gaffer.FloatPlug ):
				self.__colorPlug.setValue( self.__colorChooserWidget.getColor().dot( imath.Color3f( 1.0/3.0 ) ) )
			else:
				self.__colorPlug.setValue( self.__colorChooserWidget.getColor() )
			self.setVisible( False )

__colorChooserPopup = None
def colorChooserFunction( plug ):
	global __colorChooserPopup
	if not __colorChooserPopup:
		__colorChooserPopup = ColorChooserWindow()

	__colorChooserPopup.popup( plug )

GafferSceneUI.PaintTool.registerColorChooserFunction( colorChooserFunction )
