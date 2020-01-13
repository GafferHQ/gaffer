##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import sys

import imath

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferSceneUI.TransformTool,

	"description",
	"""
	Base class for tools that edit object transforms.
	""",

	"nodeToolbar:bottom:type", "GafferUI.StandardNodeToolbar.bottom",

	"toolbarLayout:customWidget:SelectionWidget:widgetType", "GafferSceneUI.TransformToolUI._SelectionWidget",
	"toolbarLayout:customWidget:SelectionWidget:section", "Bottom",

	# So we don't obscure the corner gnomon
	"toolbarLayout:customWidget:LeftSpacer:widgetType", "GafferSceneUI.TransformToolUI._LeftSpacer",
	"toolbarLayout:customWidget:LeftSpacer:section", "Bottom",
	"toolbarLayout:customWidget:LeftSpacer:index", 0,

	# So our layout doesn't jump around too much when our selection widget changes size
	"toolbarLayout:customWidget:RightSpacer:widgetType", "GafferSceneUI.TransformToolUI._RightSpacer",
	"toolbarLayout:customWidget:RightSpacer:section", "Bottom",
	"toolbarLayout:customWidget:RightSpacer:index", -1,

)

class _LeftSpacer( GafferUI.Spacer ) :

	def __init__( self, imageView, **kw ) :

		GafferUI.Spacer.__init__( self, size = imath.V2i( 40, 1 ), maximumSize = imath.V2i( 40, 1 ) )

class _RightSpacer( GafferUI.Spacer ) :

	def __init__( self, imageView, **kw ) :

		GafferUI.Spacer.__init__( self, size = imath.V2i( 0, 0 ) )

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

class _SelectionWidget( GafferUI.Frame ) :

	def __init__( self, tool, **kw ) :

		GafferUI.Frame.__init__( self, borderWidth = 4, **kw )

		self.__tool = tool

		with self :
			with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal, spacing = 8 ) :

				with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal ) as self.__infoRow :
					GafferUI.Image( "infoSmall.png" )
					GafferUI.Spacer( size = imath.V2i( 4 ), maximumSize = imath.V2i( 4 ) )
					self.__infoLabel = GafferUI.Label( "" )
					self.__nameLabel = GafferUI.NameLabel( graphComponent = None, numComponents = sys.maxsize )
					self.__nameLabel.setFormatter( _boldFormatter )
					self.__nameLabel.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__buttonDoubleClick ), scoped = False )

				with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) as self.__warningRow :
					GafferUI.Image( "warningSmall.png" )
					self.__warningLabel = GafferUI.Label( "" )

		self.__tool.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__update, fallbackResult = None ), scoped = False )

		self.__update()

	def context( self ) :

		return self.ancestor( GafferUI.NodeToolbar ).getContext()

	def getToolTip( self ) :

		toolTip = GafferUI.Frame.getToolTip( self )
		if toolTip :
			return toolTip

		toolSelection = self.__tool.selection()
		if not toolSelection :
			return ""

		result = ""
		script = toolSelection[0].transformPlug().ancestor( Gaffer.ScriptNode )
		for s in toolSelection :
			if result :
				result += "\n"
			result += "- Transforming {0} using {1}".format( s.path(), s.transformPlug().relativeName( script ) )

		return result

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __update( self, *unused ) :

		if not self.__tool["active"].getValue() :
			# We're about to be made invisible so all our update
			# would do is cause unnecessary flickering in Qt's
			# redraw.
			return

		toolSelection = self.__tool.selection()
		selectedPaths = GafferSceneUI.ContextAlgo.getSelectedPaths( self.context() )

		if len( toolSelection ) :

			self.__infoRow.setVisible( True )
			if len( toolSelection ) == 1 :
				self.__infoLabel.setText( "Editing " )
				numComponents = _distance(
					toolSelection[0].transformPlug().commonAncestor( toolSelection[0].scene() ),
					toolSelection[0].transformPlug(),
				)
				if toolSelection[0].scene().node().isAncestorOf( toolSelection[0].transformPlug() ) :
					numComponents += 1
				self.__nameLabel.setNumComponents( numComponents )
				self.__nameLabel.setGraphComponent( toolSelection[0].transformPlug() )
			else :
				self.__infoLabel.setText( "Editing {0} transforms".format( len( toolSelection ) ) )
				self.__nameLabel.setGraphComponent( None )

			editingAncestor = any(
				not ( selectedPaths.match( s.path() ) & IECore.PathMatcher.Result.ExactMatch )
				for s in toolSelection
			)
			if editingAncestor :
				self.__warningLabel.setText( "( Parent location )" )
				self.__warningRow.setVisible( True )
			else :
				self.__warningRow.setVisible( False )

		else :

			validSelectedPaths = IECore.PathMatcher()
			with self.context() :
				GafferScene.SceneAlgo.matchingPaths(
					selectedPaths, self.__tool.view()["in"], validSelectedPaths
				)

			if validSelectedPaths.isEmpty() :
				self.__infoRow.setVisible( True )
				self.__warningRow.setVisible( False )
				self.__infoLabel.setText( "Select something to transform" )
				self.__nameLabel.setGraphComponent( None )
			else:
				self.__infoRow.setVisible( False )
				self.__warningRow.setVisible( True )
				self.__warningLabel.setText( "Transform not editable - create a Transform node" )

	def __buttonDoubleClick( self, widget, event ) :

		if widget.getGraphComponent() is None :
			return False

		GafferUI.NodeEditor.acquire( widget.getGraphComponent().node(), floating = True )
