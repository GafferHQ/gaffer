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

from __future__ import with_statement

import re

import IECore

import Gaffer
import GafferUI

import GafferScene
import GafferSceneUI

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

				GafferUI.Spacer( IECore.V2i( 1 ), maximumSize = IECore.V2i( 100000, 1 ), parenting = { "expand" : True } )

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		pass

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
					"command" : IECore.curry( node.addOutput, name ),
					"active" : name not in currentNames
				}
			)

		if len( registeredOutputs ) :
			m.append( "/BlankDivider", { "divider" : True } )

		m.append( "/Blank", { "command" : IECore.curry( node.addOutput, "", IECore.Display( "", "", "" ) ) } )

		return m

# A widget for representing an individual output.
class _ChildPlugWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, childPlug ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=4 )
		GafferUI.PlugValueWidget.__init__( self, column, childPlug )

		with column :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=4 ) as header :

				collapseButton = GafferUI.Button( image = "collapsibleArrowRight.png", hasFrame=False )
				collapseButton.__clickedConnection = collapseButton.clickedSignal().connect( Gaffer.WeakMethod( self.__collapseButtonClicked ) )

				GafferUI.PlugValueWidget.create( childPlug["active"] )
				self.__label = GafferUI.Label( self.__namePlug().getValue() )

				GafferUI.Spacer( IECore.V2i( 1 ), maximumSize = IECore.V2i( 100000, 1 ), parenting = { "expand" : True } )

				self.__deleteButton = GafferUI.Button( image = "delete.png", hasFrame=False )
				self.__deleteButton.__clickedConnection = self.__deleteButton.clickedSignal().connect( Gaffer.WeakMethod( self.__deleteButtonClicked ) )
				self.__deleteButton.setVisible( False )

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing= 4 ) as self.__detailsColumn :

				GafferUI.PlugWidget( self.__namePlug() )
				GafferUI.PlugWidget( self.__fileNamePlug() )
				GafferUI.PlugWidget( childPlug["type"] )
				GafferUI.PlugWidget( childPlug["data"] )
				GafferUI.CompoundDataPlugValueWidget( childPlug["parameters"], collapsed=None )

				GafferUI.Divider( GafferUI.Divider.Orientation.Horizontal )

			self.__detailsColumn.setVisible( False )

			self.__enterConnection = header.enterSignal().connect( Gaffer.WeakMethod( self.__enter ) )
			self.__leaveConnection = header.leaveSignal().connect( Gaffer.WeakMethod( self.__leave ) )

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		with self.getContext() :

			enabled = self.getPlug()["active"].getValue()
			self.__label.setEnabled( enabled )
			self.__detailsColumn.setEnabled( enabled )

			self.__label.setText( self.__namePlug().getValue() )

	def __namePlug( self ) :

		plug = self.getPlug()
		# backwards compatibility with old plug layout
		return plug.getChild( "label" ) or plug.getChild( "name" )

	def __fileNamePlug( self ) :

		plug = self.getPlug()
		# backwards compatibility with old plug layout
		return plug.getChild( "fileName" ) or plug.getChild( "name" )

	def __enter( self, widget ) :

		self.__deleteButton.setVisible( True )

	def __leave( self, widget ) :

		self.__deleteButton.setVisible( False )

	def __collapseButtonClicked( self, button ) :

		visible = not self.__detailsColumn.getVisible()
		self.__detailsColumn.setVisible( visible )
		button.setImage( "collapsibleArrowDown.png" if visible else "collapsibleArrowRight.png" )

	def __deleteButtonClicked( self, button ) :

		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().parent().removeChild( self.getPlug() )

GafferUI.PlugValueWidget.registerCreator( GafferScene.Outputs, "outputs", OutputsPlugValueWidget )

## \todo This regex is an interesting case to be considered during the string matching unification for #707. Once that
# is done, intuitively we want to use an "outputs.*" glob expression, but because the "*" will match anything
# at all, including ".", it will match the children of what we want too. We might want to prevent wildcards from
# matching "." when we come to use them in this context.
GafferUI.PlugValueWidget.registerCreator( GafferScene.Outputs, re.compile( "outputs\.[^\.]+$" ), _ChildPlugWidget )

##########################################################################
# Simple PlugValueWidget registrations for child plugs of outputs
##########################################################################

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.Outputs,
	"outputs.*.active",
	GafferUI.BoolPlugValueWidget,
	displayMode = GafferUI.BoolWidget.DisplayMode.Switch,
)

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.Outputs,
	re.compile( "outputs.*.parameters.quantize" ),
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = [
		( "8 bit", IECore.IntVectorData( [ 0, 255, 0, 255 ] ) ),
		( "16 bit", IECore.IntVectorData( [ 0, 65535, 0, 65535 ] ) ),
		( "Float", IECore.IntVectorData( [ 0, 0, 0, 0 ] ) ),
	]
)

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.Outputs,
	"outputs.*.name",
	lambda plug : GafferUI.PathPlugValueWidget( plug,
		path = Gaffer.FileSystemPath( "/", filter = Gaffer.FileSystemPath.createStandardFilter() ),
		pathChooserDialogueKeywords = {
			"bookmarks" : GafferUI.Bookmarks.acquire( plug, category = "image" ),
			"leaf" : True,
		},
	)
)
