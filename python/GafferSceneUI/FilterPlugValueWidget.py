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

import IECore

import Gaffer
import GafferUI

import GafferScene

class FilterPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__column = GafferUI.ListContainer()
		GafferUI.PlugValueWidget.__init__( self, self.__column, plug, **kw )

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		label = GafferUI.LabelPlugValueWidget(
			plug,
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top,
		)
		label.label()._qtWidget().setMinimumWidth( GafferUI.PlugWidget.labelWidth() )
		row.append( label )

		self.__menuButton = GafferUI.MenuButton()
		self.__menuButton.setMenu( GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
		row.append( self.__menuButton )
		row.append( GafferUI.Spacer( IECore.V2i( 1 ), IECore.V2i( 100000, 1 ) ), expand = True )

		self.__column.append( row )

		self._updateFromPlug()

	def hasLabel( self ) :

		return True

	## Must be implemented by subclasses so that the widget reflects the current
	# status of the plug.
	def _updateFromPlug( self ) :

		thisNode = self.getPlug().node()
		filterNode = self.__filterNode()

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
		if filterNode is None :
			del self.__column[1:]
		else :
			filterNodeUI = None
			if len( self.__column ) > 1 :
				filterNodeUI = self.__column[1]
			if filterNodeUI is None or not filterNodeUI.node().isSame( filterNode ) :
				filterNodeUI = GafferUI.StandardNodeUI( filterNode, displayMode = GafferUI.StandardNodeUI.DisplayMode.Bare )
			if len( self.__column ) > 1 :
				self.__column[1] = filterNodeUI
			else :
				self.__column.append( filterNodeUI )

	def __filterNode( self ) :

		input = self.getPlug().getInput()
		if input is None :
			return None

		return input.node()

	def __removeFilter( self ) :

		filterNode = self.__filterNode()
		filterNode.parent().removeChild( filterNode )

	def __addFilter( self, filterType ) :

		filterNode = filterType()

		with Gaffer.UndoContext( self.getPlug().node().scriptNode() ) :
			self.getPlug().node().parent().addChild( filterNode )
			self.getPlug().setInput( filterNode["match"] )

		# position the node appropriately.
		## \todo In an ideal world the GraphGadget would do this
		# without prompting.
		scriptWindow = self.ancestor( GafferUI.ScriptWindow )
		if scriptWindow is not None :
			nodeGraphs = scriptWindow.getLayout().editors( GafferUI.NodeGraph )
			if nodeGraphs :
				graphGadget = nodeGraphs[0].graphGadget()
				graphGadget.getLayout().positionNode( graphGadget, filterNode )

	def __linkFilter( self ) :

		## \todo Implement browsing to other nodes with existing filters
		pass

	def __menuDefinition( self ) :

		filterNode = self.__filterNode()
		result = IECore.MenuDefinition()

		if filterNode is not None :
			result.append( "/Remove", { "command" : Gaffer.WeakMethod( self.__removeFilter ) } )
			result.append( "/RemoveDivider", { "divider" : True } )

		for filterType in GafferScene.Filter.__subclasses__() :
			result.append( "/" + filterType.staticTypeName().rpartition( ":" )[2], { "command" : IECore.curry( Gaffer.WeakMethod( self.__addFilter ), filterType ) } )

		result.append( "/AddDivider", { "divider" : True } )
		result.append( "/Link...", { "command" : Gaffer.WeakMethod( self.__linkFilter ), "active" : False } )

		return result
