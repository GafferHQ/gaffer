##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import IECoreScene

import Gaffer
import GafferUI

from GafferUI.PlugValueWidget import sole

import GafferScene
import GafferSceneUI

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.Outputs,

	"description",
	"""
	Defines the image outputs to be created by the renderer. Arbitrary
	outputs can be defined within the UI and also via the
	`Outputs::addOutput()` API. Commonly used outputs may also
	be predefined at startup via a config file - see
	$GAFFER_ROOT/startup/gui/outputs.py for an example.
	""",

	plugs = {

		"outputs" : [

			"description",
			"""
			The outputs defined by this node.
			""",

			"plugValueWidget:type", "GafferSceneUI.OutputsUI.OutputsPlugValueWidget",

		],

		"outputs.*" : [

			"plugValueWidget:type", "GafferSceneUI.OutputsUI.ChildPlugValueWidget",

		],

		"outputs.*.parameters.quantize.value" : [

			"description",
			"""
			The bit depth of the image.
			""",

			"preset:8 bit", IECore.IntVectorData( [ 0, 255, 0, 255 ] ),
			"preset:16 bit", IECore.IntVectorData( [ 0, 65535, 0, 65535 ] ),
			"preset:Float", IECore.IntVectorData( [ 0, 0, 0, 0 ] ),

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"outputs.*.fileName" : [

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"path:bookmarks", "image",
			"path:leaf", True,

		],

		"outputs.*.active" : [

			"boolPlugValueWidget:displayMode", "switch",

		],

	}

)

##########################################################################
# Custom PlugValueWidgets for listing outputs
##########################################################################

class OutputsPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		column = GafferUI.ListContainer( spacing = 6 )
		GafferUI.PlugValueWidget.__init__( self, column, plug )

		with column :

			# this will take care of laying out our list of outputs, as
			# each output is represented as a child plug of the main plug.
			GafferUI.PlugLayout( plug )

			# now we just need a little footer with a button for adding new outputs
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				GafferUI.MenuButton(
					image="plus.png", hasFrame=False, menu = GafferUI.Menu( Gaffer.WeakMethod( self.__addMenuDefinition ) )
				)

				GafferUI.Spacer( imath.V2i( 1 ), maximumSize = imath.V2i( 100000, 1 ), parenting = { "expand" : True } )

	def hasLabel( self ) :

		return True

	def __addMenuDefinition( self ) :

		node = self.getPlug().node()
		currentNames = set( [ output["name"].getValue() for output in node["outputs"].children() ] )

		m = IECore.MenuDefinition()

		registeredOutputs = node.registeredOutputs()
		for name in registeredOutputs :
			menuPath = name
			if not menuPath.startswith( "/" ) :
				menuPath = "/" + menuPath
			m.append(
				menuPath,
				{
					"command" : functools.partial( node.addOutput, name ),
					"active" : name not in currentNames
				}
			)

		if len( registeredOutputs ) :
			m.append( "/BlankDivider", { "divider" : True } )

		m.append( "/Blank", { "command" : functools.partial( node.addOutput, "", IECoreScene.Output( "", "", "" ) ) } )

		return m

# A widget for representing an individual output.
class ChildPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, childPlug ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=4 )
		GafferUI.PlugValueWidget.__init__( self, column, childPlug )

		with column :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=4 ) as header :

				collapseButton = GafferUI.Button( image = "collapsibleArrowRight.png", hasFrame=False )
				collapseButton.clickedSignal().connect( Gaffer.WeakMethod( self.__collapseButtonClicked ), scoped = False )

				GafferUI.PlugValueWidget.create( childPlug["active"] )
				self.__label = GafferUI.Label( childPlug["name"].getValue() )

				GafferUI.Spacer( imath.V2i( 1 ), maximumSize = imath.V2i( 100000, 1 ), parenting = { "expand" : True } )

				self.__deleteButton = GafferUI.Button( image = "delete.png", hasFrame=False )
				self.__deleteButton.clickedSignal().connect( Gaffer.WeakMethod( self.__deleteButtonClicked ), scoped = False )
				self.__deleteButton.setVisible( False )

			self.__detailsColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )
			self.__detailsColumn.setVisible( False )

			header.enterSignal().connect( Gaffer.WeakMethod( self.__enter ), scoped = False )
			header.leaveSignal().connect( Gaffer.WeakMethod( self.__leave ), scoped = False )

	def hasLabel( self ) :

		return True

	@staticmethod
	def _valuesForUpdate( plugs ) :

		return [
			{
				"enabled" : plug["active"].getValue(),
				"name" : plug["name"].getValue(),
			}
			for plug in plugs
		]

	def _updateFromValues( self, values, exception ) :

		if values :
			enabled = all( v["enabled"] for v in values )
			self.__label.setEnabled( enabled )
			self.__detailsColumn.setEnabled( enabled )
			self.__label.setText( sole( v["name"] for v in values ) )

	def _updateFromEditable( self ) :

		self.__deleteButton.setEnabled( self._editable() )

	def __enter( self, widget ) :

		if self._editable() :
			self.__deleteButton.setVisible( True )

	def __leave( self, widget ) :

		self.__deleteButton.setVisible( False )

	def __collapseButtonClicked( self, button ) :

		visible = not self.__detailsColumn.getVisible()

		if visible and not len( self.__detailsColumn ) :
			# Build details section the first time it is shown,
			# to avoid excessive overhead in the initial UI build.
			with self.__detailsColumn :
				GafferUI.PlugWidget( self.getPlug()["name"] )
				GafferUI.PlugWidget( self.getPlug()["fileName"] )
				GafferUI.PlugWidget( self.getPlug()["type"] )
				GafferUI.PlugWidget( self.getPlug()["data"] )
				GafferUI.CompoundDataPlugValueWidget( self.getPlug()["parameters"] )
				GafferUI.Divider( GafferUI.Divider.Orientation.Horizontal )

		self.__detailsColumn.setVisible( visible )
		button.setImage( "collapsibleArrowDown.png" if visible else "collapsibleArrowRight.png" )

	def __deleteButtonClicked( self, button ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().parent().removeChild( self.getPlug() )
