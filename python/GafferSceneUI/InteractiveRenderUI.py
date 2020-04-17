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

from Qt import QtCore

import Gaffer
import GafferImage
import GafferScene
import GafferUI
import GafferImageUI

##########################################################################
# ImageView UI for the viewed images render node (if available)
##########################################################################

for key, value in {

	"toolbarLayout:customWidget:RenderControlBalancingSpacer:widgetType" : "GafferSceneUI.InteractiveRenderUI._ViewRenderControlBalancingSpacer",
	"toolbarLayout:customWidget:RenderControlBalancingSpacer:section" :  "Top",
	"toolbarLayout:customWidget:RenderControlBalancingSpacer:visibilityActivator" : "viewSupportsRenderControl" ,
	"toolbarLayout:customWidget:RenderControlBalancingSpacer:index" :  0,

	"toolbarLayout:customWidget:RenderControl:widgetType" : "GafferSceneUI.InteractiveRenderUI._ViewRenderControlUI",
	"toolbarLayout:customWidget:RenderControl:section" :  "Top",
	"toolbarLayout:customWidget:RenderControl:visibilityActivator" : "viewSupportsRenderControl" ,
	"toolbarLayout:customWidget:RenderControl:index" :  -2,

	"toolbarLayout:activator:viewSupportsRenderControl" : lambda view : _ViewRenderControlUI._interactiveRenderNode( view ) is not None,

}.items() :
	Gaffer.Metadata.registerValue( GafferImageUI.ImageView, key, value )

class _ViewRenderControlBalancingSpacer( GafferUI.Spacer ) :

	def __init__( self, sceneView, **kw ) :

		GafferUI.Spacer.__init__(
			self,
			imath.V2i( 0 ), # Minimum
			maximumSize = imath.V2i( 100, 1 ),
			preferredSize = imath.V2i( 100, 1 )
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

		self.__view = view

		if isinstance( self.__view["in"], GafferImage.ImagePlug ) :
			view.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__viewPlugDirtied ), scoped = False )

		self.__update()

	def __update( self ) :

		renderNode = self._interactiveRenderNode( self.__view )
		if renderNode is not None:

			statePlug = renderNode["state"]

			if not statePlug.isSame( self.__stateWidget.getPlug() ) :
				self.__stateWidget.setPlug( statePlug )
				self.__renderNodePlugDirtiedConnection = renderNode.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__renderNodePlugDirtied ) )

			# We disable the controls if a render is in progress, but not being viewed
			with self.__view.getContext() :
				renderNodeStopped = statePlug.getValue() == GafferScene.InteractiveRender.State.Stopped
				viewedImageIsRendering = self.__imageIsRendering( self.__view["in"] )
				controlsEnabled  = ( viewedImageIsRendering and not renderNodeStopped ) or renderNodeStopped

			self.__stateWidget.setToolTip(
				"" if controlsEnabled else "Controls disabled because image is not the one currently rendering."
			)
			self.__stateWidget.setEnabled( controlsEnabled )

		else :
			self.__stateWidget.setPlug( None )
			self.__renderNodePlugDirtiedConnection = None

	@staticmethod
	def _interactiveRenderNode( view ) :

		if not isinstance( view["in"], GafferImage.ImagePlug ) :
			return None

		with view.getContext() :
			renderScene = GafferScene.SceneAlgo.sourceScene( view["in"] )

		if not renderScene :
			return None

		node = renderScene.node()
		return node if isinstance( node, GafferScene.InteractiveRender ) else None

	def __imageIsRendering( self, imagePlug ) :

		# Make-shift detection of an in-progress render.
		# Finished images have the `fileFormat` key courtesy of OIIO.
		## \TODO add more formal metadata to determine this
		return "fileFormat" not in imagePlug.metadata()

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
		self.__startPauseButton._qtWidget().setFocusPolicy( QtCore.Qt.NoFocus )
		self.__stopButton._qtWidget().setFocusPolicy( QtCore.Qt.NoFocus )

		self.__startPauseButton.clickedSignal().connect( Gaffer.WeakMethod( self.__startPauseClicked ), scoped = False )
		self.__stopButton.clickedSignal().connect( Gaffer.WeakMethod( self.__stopClicked ), scoped = False )

		self.__stateIcons = {
			GafferScene.InteractiveRender.State.Running : 'renderPause.png',
			GafferScene.InteractiveRender.State.Paused : 'renderResume.png',
			GafferScene.InteractiveRender.State.Stopped : 'renderStart.png'
		}

		self._updateFromPlug()

	def _updateFromPlug( self ) :

		if self.getPlug() is None :
			self.__startPauseButton.setEnabled( False )
			self.__stopButton.setEnabled( False )
			return

		with self.getContext() :
			state = self.getPlug().getValue()

		self.__startPauseButton.setEnabled( True )
		self.__startPauseButton.setImage( self.__stateIcons[state] )
		self.__stopButton.setEnabled( state != GafferScene.InteractiveRender.State.Stopped )

	def __startPauseClicked( self, button ) :

		with self.getContext() :
			state = self.getPlug().getValue()

		# When setting the plug value here, we deliberately don't use an UndoScope.
		# Not enabling undo here is done so that users won't accidentally restart/stop their renderings.
		if state != GafferScene.InteractiveRender.State.Running:
			self.getPlug().setValue( GafferScene.InteractiveRender.State.Running )
		else:
			self.getPlug().setValue( GafferScene.InteractiveRender.State.Paused )

	def __stopClicked( self, button ) :
		self.getPlug().setValue( GafferScene.InteractiveRender.State.Stopped )

##########################################################################
# Metadata for GafferScene.Preview.InteractiveRender node. We intend
# for this to entirely replace the GafferScene.InteractiveRender node
# which is registered under this section.
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.InteractiveRender,

	"description",
	"""
	Performs interactive renders, updating the render on the fly
	whenever the input scene changes.
	""",

	plugs = {

		"*" : [

			"nodule:type", "",

		],

		"in" : [

			"description",
			"""
			The scene to be rendered.
			""",

			"nodule:type", "GafferUI::StandardNodule",

		],

		"renderer" : [

			"description",
			"""
			The renderer to use.
			""",

		],

		"state" : [

			"description",
			"""
			Turns the rendering on and off, or pauses it.
			""",

			"label", "Render",
			"plugValueWidget:type", "GafferSceneUI.InteractiveRenderUI._StatePlugValueWidget",

		],

		"out" : [

			"description",
			"""
			A direct pass-through of the input scene.
			""",

		],

	}
)

