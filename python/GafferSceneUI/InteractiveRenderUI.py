##########################################################################
#
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

import imath

from PySide6 import QtCore

import Gaffer
import GafferImage
import GafferScene
import GafferSceneUI
import GafferUI
import GafferImageUI

from GafferUI.PlugValueWidget import sole

import IECore

##########################################################################
# ImageView UI for the viewed image's render node (if available)
##########################################################################

for key, value in {

	"toolbarLayout:customWidget:RenderControlBalancingSpacer:widgetType" : "GafferSceneUI.InteractiveRenderUI._ViewRenderControlBalancingSpacer",
	"toolbarLayout:customWidget:RenderControlBalancingSpacer:section" :  "Top",
	"toolbarLayout:customWidget:RenderControlBalancingSpacer:visibilityActivator" : "viewSupportsRenderControl" ,
	"toolbarLayout:customWidget:RenderControlBalancingSpacer:index" :  1,

	"toolbarLayout:customWidget:RenderControl:widgetType" : "GafferSceneUI.InteractiveRenderUI._ViewRenderControlUI",
	"toolbarLayout:customWidget:RenderControl:section" :  "Top",
	"toolbarLayout:customWidget:RenderControl:visibilityActivator" : "viewSupportsRenderControl" ,
	"toolbarLayout:customWidget:RenderControl:index" :  -1,

	"toolbarLayout:customWidget:RightCenterSpacer:index" :  -3,
	"toolbarLayout:customWidget:StateWidgetBalancingSpacer:index" :  -2,

	"toolbarLayout:activator:viewSupportsRenderControl" : lambda view : _ViewRenderControlUI._interactiveRenderNode( view ) is not None,

}.items() :
	Gaffer.Metadata.registerValue( GafferImageUI.ImageView, key, value )

class _ViewRenderControlBalancingSpacer( GafferUI.Spacer ) :

	def __init__( self, imageView, **kw ) :

		width = 104
		GafferUI.Spacer.__init__(
			self,
			imath.V2i( 0 ), # Minimum
			preferredSize = imath.V2i( width, 1 ),
			maximumSize = imath.V2i( width, 1 )
		)

class _ViewRenderControlUI( GafferUI.Widget ) :

	def __init__( self, view, **kwargs ) :

		self.__frame = GafferUI.Frame( borderWidth = 0 )
		GafferUI.Widget.__init__( self, self.__frame, **kwargs )

		with self.__frame :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
				GafferUI.Spacer( imath.V2i( 1, 1 ), imath.V2i( 1, 1 ) )
				self.__label = GafferUI.Label( "Render" )
				self.__stateWidget = _StatePlugValueWidget( None )
				self.__messagesWidget = _MessageSummaryWidget( None )

		self.__view = view

		if isinstance( self.__view["in"], GafferImage.ImagePlug ) :
			view.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__viewPlugDirtied ) )

		self.__update()

	def __update( self ) :

		renderNode = self._interactiveRenderNode( self.__view )
		if renderNode is not None:

			statePlug = renderNode["state"].source()

			if not statePlug.isSame( self.__stateWidget.getPlug() ) :
				self.__stateWidget.setPlug( statePlug )
				self.__messagesWidget.setNode( renderNode )
				self.__renderNodePlugDirtiedConnection = renderNode.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__renderNodePlugDirtied ), scoped = True )

			# We disable the controls if a render is in progress, but not being viewed
			with self.__view.context() :
				renderNodeStopped = statePlug.getValue() == GafferScene.InteractiveRender.State.Stopped
				viewedImageIsRendering = self.__imageIsRendering( self.__view["in"] )
				controlsEnabled  = ( viewedImageIsRendering and not renderNodeStopped ) or renderNodeStopped

			self.__stateWidget.setToolTip(
				"" if controlsEnabled else "Controls disabled because image is not the one currently rendering."
			)
			self.__stateWidget.setEnabled( controlsEnabled )
			self.__messagesWidget.setEnabled( controlsEnabled )

		else :
			self.__stateWidget.setPlug( None )
			self.__messagesWidget.setNode( None )
			self.__renderNodePlugDirtiedConnection = None

	@staticmethod
	def _interactiveRenderNode( view ) :

		if not isinstance( view["in"], GafferImage.ImagePlug ) :
			return None

		with view.context() :
			try :
				renderScene = GafferScene.SceneAlgo.sourceScene( view["in"] )
			except :
				return None

		if not renderScene :
			return None

		node = renderScene.node()
		return node if isinstance( node, GafferScene.InteractiveRender ) else None

	def __imageIsRendering( self, imagePlug ) :

		rendering = False

		try :
			rendering = imagePlug.metadata()[ "gaffer:isRendering" ].value
		except :
			pass

		return rendering

	@GafferUI.LazyMethod()
	def __updateLazily( self ) :

		self.__update()

	def __viewPlugDirtied( self, plug ) :

		if plug.isSame( self.__view["in"]["metadata"] ) :
			self.__updateLazily()

	def __renderNodePlugDirtied( self, plug ) :

		if plug.getName() == "state" :
			self.__updateLazily();

##########################################################################
# UI for the state plug that allows setting the state through buttons
##########################################################################

class _StatePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, *args, **kwargs) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :
			self.__startPauseButton = GafferUI.Button( image = 'renderStart.png', highlightOnOver = False )
			self.__stopButton = GafferUI.Button( image = 'renderStop.png', highlightOnOver = False )

		GafferUI.WidgetAlgo.joinEdges( row )

		# Sadly unable to use setFixedWidth on row to take effect, regardless of size policies...
		self.__startPauseButton._qtWidget().setFixedWidth( 25 )
		self.__stopButton._qtWidget().setFixedWidth( 25 )
		# The button retaining focus causes problems when embedding in other UIs
		self.__startPauseButton._qtWidget().setFocusPolicy( QtCore.Qt.FocusPolicy.NoFocus )
		self.__stopButton._qtWidget().setFocusPolicy( QtCore.Qt.FocusPolicy.NoFocus )

		self.__startPauseButton.clickedSignal().connect( Gaffer.WeakMethod( self.__startPauseClicked ) )
		self.__stopButton.clickedSignal().connect( Gaffer.WeakMethod( self.__stopClicked ) )

		self.__stateIcons = {
			GafferScene.InteractiveRender.State.Running : 'renderPause.png',
			GafferScene.InteractiveRender.State.Paused : 'renderResume.png',
			GafferScene.InteractiveRender.State.Stopped : 'renderStart.png',
			None : 'renderStart.png',
		}

		self.__state = None

	def _updateFromValues( self, values, exception ) :

		self.__state = sole( values )
		self.__startPauseButton.setImage( self.__stateIcons[self.__state] )
		self._updateFromEditable()

	def _updateFromEditable( self ) :

		self.__startPauseButton.setEnabled( self._editable() )
		self.__stopButton.setEnabled( self._editable() and self.__state != GafferScene.InteractiveRender.State.Stopped )

	def __startPauseClicked( self, button ) :

		with self.context() :
			state = self.getPlug().getValue()

		# When setting the plug value here, we deliberately don't use an UndoScope.
		# Not enabling undo here is done so that users won't accidentally restart/stop their renderings.
		if state != GafferScene.InteractiveRender.State.Running:
			self.getPlug().setValue( GafferScene.InteractiveRender.State.Running )
		else:
			self.getPlug().setValue( GafferScene.InteractiveRender.State.Paused )

	def __stopClicked( self, button ) :
		self.getPlug().setValue( GafferScene.InteractiveRender.State.Stopped )

class _MessagesWidgetBase( GafferUI.Widget ) :

	def __init__( self, topLevelWidget, node, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )

		self.__node = None
		self.__messagesChangedConnection = None

		self.setNode( node )

	def setNode( self, node ) :

		if node == self.__node :
			return

		self.__node = node
		self.__messagesChangedConnection = self.__node.messagesChangedSignal().connect(
			Gaffer.WeakMethod( self.__messagesChanged ), scoped = True
		) if self.__node is not None else None

		self.__update()

	def getNode( self ) :

		return self.__node

	def _updateFromMessages( self, messages ) :

		raise NotImplementedError

	def __update( self ) :

		self._updateFromMessages(
			self.__node.messages() if self.__node is not None else Gaffer.Private.IECorePreview.Messages()
		)

	def __messagesChanged( self, renderNode ) :

		self.__update()

###############################################################################
# A widget presenting a summary of the messages from an interactive render
###############################################################################

class _MessageSummaryWidget( _MessagesWidgetBase ) :

	def __init__( self, node ) :

		self.__summaryWidget = GafferUI.MessageSummaryWidget(
			displayLevel = IECore.MessageHandler.Level.Warning,
			hideUnusedLevels = True,
			buttonToolTip = "Click to open the render log"
		)

		_MessagesWidgetBase.__init__( self, self.__summaryWidget, node )

		self.__summaryWidget.levelButtonClickedSignal().connect( Gaffer.WeakMethod( self.__levelButtonClicked ) )

	def _updateFromMessages( self, messages ) :

		self.__summaryWidget.setMessages( messages )

	def __levelButtonClicked( self, level ) :

		window = _MessagesWindow.acquire( self.getNode() )
		window.setVisible( True )
		window.messageWidget().scrollToNextMessage( level )

###############################################################################
# A utility window containing a render nodes message log
###############################################################################

class _MessagesWindow( GafferUI.Window ) :

	# Use acquire instead to retrieve an existing window or create a new one
	def __init__( self, parentWindow, node ) :

		GafferUI.Window.__init__( self, borderWidth = 8 )

		self.setChild( _MessagesWidget( node ) )
		self._qtWidget().resize( 600, 500 )

		parentWindow.addChildWindow( self, removeOnClose = True )

		scriptNode = node.scriptNode()
		while node and not node.isSame( scriptNode ) :
			node.nameChangedSignal().connect( Gaffer.WeakMethod( self.__updateTitle ) )
			node.parentChangedSignal().connect( Gaffer.WeakMethod( self.__destroy ) )
			node = node.parent()

		self.__updateTitle()

	def messageWidget( self ) :

		return self.getChild().messageWidget()

	def __updateTitle( self, *unused ) :

		node = self.getChild().getNode()
		self.setTitle( "{} Messages".format( node.relativeName( node.scriptNode() ) ) )

	def __destroy( self, *unused ) :

		self.parent().removeChild( self )

	@classmethod
	def acquire( cls, node ) :

		script = node.scriptNode()
		scriptWindow = GafferUI.ScriptWindow.acquire( script )
		childWindows = scriptWindow.childWindows()

		for window in childWindows :
			if isinstance( window, cls ) and window.getChild().getNode().isSame( node ) :
				return window

		window = cls( scriptWindow, node )
		window.setVisible( True )

		return window

##########################################################################
# UI presenting the render log
##########################################################################

class _MessagesWidget( _MessagesWidgetBase ) :

	def __init__( self, node ) :

		self.__messages = GafferUI.MessageWidget(
			toolbars = True,
			follow = True,
			role = GafferUI.MessageWidget.Role.Log
		)

		_MessagesWidgetBase.__init__( self, self.__messages, node )

	def messageWidget( self ) :

		return self.__messages

	def _updateFromMessages( self, messages ) :

		self.__messages.setMessages( messages )

##########################################################################
# Metadata for InteractiveRender node.
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.InteractiveRender,

	"description",
	"""
	Performs interactive renders, updating the render on the fly
	whenever the input scene changes.
	""",

	"layout:section:Settings.Log:collapsed", False,

	"layout:customWidget:messages:widgetType", "GafferSceneUI.InteractiveRenderUI._MessagesWidget",
	"layout:customWidget:messages:section", "Settings.Log",

	plugs = {

		"*" : {

			"nodule:type" : "",

		},

		"in" : {

			"description" :
			"""
			The scene to be rendered.
			""",

			"nodule:type" : "GafferUI::StandardNodule",

		},

		"renderer" : {

			"description" :
			"""
			The renderer to use. Default mode uses the `render:defaultRenderer` option from
			the input scene globals to choose the renderer. This can be authored using
			the StandardOptions node.

			> Note : Changing renderer currently requires that the current render is
			> manually stopped and restarted.
			""",

			"plugValueWidget:type" : "GafferSceneUI.RenderUI.RendererPlugValueWidget",

			"presetNames" : lambda plug : IECore.StringVectorData( [
				"Default" if n == "None" else n
				for n in Gaffer.Metadata.value( "option:render:defaultRenderer", "presetNames" )
				if n != "OpenGL"
			] ),
			"presetValues" : lambda plug : IECore.StringVectorData( [
				n for n in Gaffer.Metadata.value( "option:render:defaultRenderer", "presetValues" )
				if n != "OpenGL"
			] ),

		},

		"state" : {

			"description" :
			"""
			Turns the rendering on and off, or pauses it.
			""",

			"label" : "Render",
			"plugValueWidget:type" : "GafferSceneUI.InteractiveRenderUI._StatePlugValueWidget",

		},

		"useVisibleSet" : {

			"description" :
			"""
			When on, the Visible Set will control which locations are rendered.

			> Tip : Use the HierarchyView and/or SetEditor to control the Visible Set.
			""",

		},

		"resolvedRenderer" : {

			"description" :
			"""
			The renderer that will be used, accounting for the value of the
			`render:defaultRenderer` option if `renderer` is set to "Default".
			""",

			"layout:section" : "Advanced",

		},

		"out" : {

			"description" :
			"""
			A direct pass-through of the input scene.
			""",

		},

	}
)
