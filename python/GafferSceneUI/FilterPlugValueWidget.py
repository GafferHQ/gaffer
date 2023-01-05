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

import functools

import imath

import IECore

import Gaffer
import GafferUI

from GafferUI.PlugValueWidget import sole

import GafferScene

class FilterPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__column = GafferUI.ListContainer( spacing = 8 )
		GafferUI.PlugValueWidget.__init__( self, self.__column, plug, **kw )

		with self.__column :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				label = GafferUI.LabelPlugValueWidget(
					plug,
					horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
					verticalAlignment = GafferUI.Label.VerticalAlignment.Top,
				)
				label.label()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )

				self.__menuButton = GafferUI.MenuButton()
				self.__menuButton.setMenu( GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 100000, 1 ), parenting = { "expand" : True } )

			GafferUI.Divider()

	def hasLabel( self ) :

		return True

	@staticmethod
	def _valuesForUpdate( plugs ) :

		return [ FilterPlugValueWidget.__filterNode( p ) for p in plugs ]

	def _updateFromValues( self, values, exception ) :

		thisNode = self.getPlug().node()
		filterNode = sole( values )

		# update the selection menu text
		if filterNode is None :
			self.__menuButton.setText( "Add..." )
		elif filterNode.parent().isSame( thisNode ) :
			self.__menuButton.setText( filterNode.getName() )
		else :
			self.__menuButton.setText(
				filterNode.relativeName(
					filterNode.commonAncestor( thisNode, Gaffer.Node ),
				)
			)

		# update the filter node ui
		filterUI = self.__column[-1] if isinstance( self.__column[-1], GafferUI.PlugLayout ) else None
		if filterNode is None :
			if filterUI is not None :
				self.__column.removeChild( filterUI )
		else :
			if filterUI is None or not filterUI.__node.isSame( filterNode ) :
				if filterUI is not None :
					self.__column.removeChild( filterUI )
				filterUI = GafferUI.PlugLayout( filterNode, rootSection = "Settings" )
				filterUI.__node = filterNode
				self.__column.append( filterUI )

	def _updateFromEditable( self ) :

		# We don't use `_editable()` directly because it considers us to be non-editable
		# if the plug has an input, and our whole purpose is to manage that input.
		self.__menuButton.setEnabled( not Gaffer.MetadataAlgo.readOnly( self.getPlug() ) )

	@staticmethod
	def __filterNode( plug ) :

		input = plug.getInput()
		if input is None :
			return None

		return input.node()

	def __removeFilter( self ) :

		with Gaffer.UndoScope( self.getPlug().node().scriptNode() ) :
			filterNode = self.__filterNode( self.getPlug() )
			filterNode.parent().removeChild( filterNode )

	def __addFilter( self, filterType ) :

		filterNode = filterType()

		with Gaffer.UndoScope( self.getPlug().node().scriptNode() ) :
			self.getPlug().node().parent().addChild( filterNode )
			self.getPlug().setInput( filterNode["out"] )

	def __menuDefinition( self ) :

		filterNode = self.__filterNode( self.getPlug() )
		result = IECore.MenuDefinition()

		if filterNode is not None :
			result.append( "/Remove", { "command" : Gaffer.WeakMethod( self.__removeFilter ) } )
			result.append( "/RemoveDivider", { "divider" : True } )

		for filterType in self.__filterTypes() :
			result.append( "/" + filterType.staticTypeName().rpartition( ":" )[2], { "command" : functools.partial( Gaffer.WeakMethod( self.__addFilter ), filterType ) } )

		return result

	@staticmethod
	def __filterTypes() :

		def walk( f ) :

			result = []

			subClasses = f.__subclasses__()
			if not len( subClasses ) :
				result.append( f )
			else :
				for s in subClasses :
					result += walk( s )

			return result

		return walk( GafferScene.Filter )
