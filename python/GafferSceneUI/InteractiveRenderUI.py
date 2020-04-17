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

import Gaffer
import GafferScene
import GafferUI

##########################################################################
# UI for the state plug that allows setting the state through buttons
##########################################################################

class _StatePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, *args, **kwargs) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :
			self.__startPauseButton = GafferUI.Button( image = 'timelinePlay.png' )
			self.__stopButton = GafferUI.Button( image = 'timelineStop.png' )

			self.__startPauseButton.clickedSignal().connect( Gaffer.WeakMethod( self.__startPauseClicked ), scoped = False )
			self.__stopButton.clickedSignal().connect( Gaffer.WeakMethod( self.__stopClicked ), scoped = False )

		self._updateFromPlug()

	def _updateFromPlug( self ) :

		if self.getPlug() is None :
			self.__startPauseButton.setEnabled( False )
			self.__stopButton.setEnabled( False )
			return
		else :
			self.__startPauseButton.setEnabled( True )

		with self.getContext() :
			state = self.getPlug().getValue()

		if state == GafferScene.InteractiveRender.State.Running :
			self.__startPauseButton.setImage( 'timelinePause.png' )
			self.__stopButton.setEnabled( True )
		elif state == GafferScene.InteractiveRender.State.Paused :
			self.__startPauseButton.setImage( 'timelinePlay.png' )
			self.__stopButton.setEnabled( True )
		elif state == GafferScene.InteractiveRender.State.Stopped :
			self.__startPauseButton.setImage( 'timelinePlay.png' )
			self.__stopButton.setEnabled( False )

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

