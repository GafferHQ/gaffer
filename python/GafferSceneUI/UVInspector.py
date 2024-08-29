##########################################################################
#
#  Copyright (c) 2018, John Haddon. All rights reserved.
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

import Gaffer
import GafferImage
import GafferUI
import GafferSceneUI

class UVInspector( GafferSceneUI.SceneEditor ) :

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer()

		GafferSceneUI.SceneEditor.__init__( self, column, scriptNode, **kw )

		self.__uvView = GafferSceneUI.UVView( scriptNode )
		self.__uvView["in"].setInput( self.settings()["in"] )
		Gaffer.NodeAlgo.applyUserDefaults( self.__uvView )
		self.__uvView.setContext( self.context() )

		with column :

			with GafferUI.Frame( borderWidth = 4, borderStyle = GafferUI.Frame.BorderStyle.None_ ) :
				GafferUI.NodeToolbar.create( self.__uvView )

			self.__gadgetWidget = GafferUI.GadgetWidget()

			self.__gadgetWidget.setViewportGadget( self.__uvView.viewportGadget() )
			self.__gadgetWidget.getViewportGadget().frame( imath.Box3f( imath.V3f( 0, 0, 0 ), imath.V3f( 1, 1, 0 ) ) )

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )
		self.__gadgetWidget.getViewportGadget().buttonPressSignal().connect(
			Gaffer.WeakMethod( self.__buttonPress ), scoped = False
		)
		self.__gadgetWidget.getViewportGadget().dragBeginSignal().connect(
			Gaffer.WeakMethod( self.__dragBegin ), scoped = False
		)
		self.__gadgetWidget.getViewportGadget().dragEndSignal().connect(
			Gaffer.WeakMethod( self.__dragEnd ), scoped = False
		)

		self._updateFromSet()

	def __repr__( self ) :

		return "GafferSceneUI.UVInspector( scriptNode )"

	def __keyPress( self, widget, event ) :

		if event.key == "F" :
			bound = self.__gadgetWidget.getViewportGadget().getPrimaryChild().bound()
			if bound.isEmpty() :
				bound = imath.Box3f( imath.V3f( 0 ), imath.V3f( 1, 1, 0 ) )
			self.__gadgetWidget.getViewportGadget().frame( bound )
			return True

		return False

	def __buttonPress( self, viewportGadget, event ) :

		return event.buttons == event.Buttons.Left

	def __dragBegin( self, viewportGadget, event ) :

		uv = viewportGadget.rasterToGadgetSpace(
			imath.V2f( event.line.p0.x, event.line.p0.y ),
			viewportGadget.getPrimaryChild() # The gadget displaying the UVs
		)
		GafferUI.Pointer.setCurrent( "values" )
		return imath.V2f( uv.p0.x, uv.p0.y )

	def __dragEnd( self, viewportGadget, event ) :

		GafferUI.Pointer.setCurrent( "" )

GafferUI.Editor.registerType( "UVInspector", UVInspector )

Gaffer.Metadata.registerNode(

	GafferSceneUI.UVView,

	"toolbarLayout:customWidget:StateWidget:widgetType", "GafferSceneUI.UVInspector._StateWidget",
	"toolbarLayout:customWidget:StateWidget:section", "Top",
	"toolbarLayout:customWidget:StateWidget:index", 0,

	plugs = {

		"textureFileName" : [

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"path:leaf", True,
			"path:bookmarks", "image",
			"fileSystemPath:extensions", " ".join( GafferImage.ImageReader.supportedExtensions() ),
			"fileSystemPath:extensionsLabel", "Show only image files",

		],

	}

)

## \todo This widget is basically the same as the SceneView and ImageView ones. Perhaps the
# View base class should provide standard functionality for pausing and state, and we could
# use one standard widget for everything.
class _StateWidget( GafferUI.Widget ) :

	def __init__( self, uvView, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.Widget.__init__( self, row, **kw )

		with row :

			self.__button = GafferUI.Button( hasFrame = False )
			self.__busyWidget = GafferUI.BusyWidget( size = 20 )

		self.__uvView = uvView

		self.__button.clickedSignal().connect(
			Gaffer.WeakMethod( self.__buttonClick ), scoped = False
		)

		self.__uvView.stateChangedSignal().connect(
			Gaffer.WeakMethod( self.__stateChanged ), scoped = False
		)

		self.__update()

	def __stateChanged( self, sceneGadget ) :

		self.__update()

	def __buttonClick( self, button ) :

		self.__uvView.setPaused( not self.__uvView.getPaused() )
		self.__update()

	def __update( self ) :

		paused = self.__uvView.getPaused()
		self.__button.setImage( "viewPause.png" if not paused else "viewPaused.png" )
		self.__busyWidget.setBusy( self.__uvView.state() == self.__uvView.State.Running )
		self.__button.setToolTip( "Viewer updates suspended, click to resume" if paused else "Click to suspend viewer updates [esc]" )

UVInspector._StateWidget = _StateWidget
