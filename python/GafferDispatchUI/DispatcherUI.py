##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

import weakref
import functools

import imath

import Gaffer
import GafferUI
import GafferDispatch

from GafferUI._StyleSheet import _styleColors

from Qt import QtGui

Gaffer.Metadata.registerNode(

	GafferDispatch.Dispatcher,

	"description",
	"""
	Used to schedule the execution of a network
	of TaskNodes.
	""",

	"layout:activator:framesModeIsCustomRange", lambda node : node["framesMode"].getValue() == GafferDispatch.Dispatcher.FramesMode.CustomRange,
	"layout:customWidget:dispatchButton:widgetType", "GafferDispatchUI.DispatcherUI._DispatchButton",

	plugs = {

		"user" : (

			"plugValueWidget:type", "",

		),

		"tasks" : (

			"description",
			"""
			The tasks to be executed by this dispatcher.
			""",

			"nodule:type", "GafferUI::CompoundNodule",
			"noduleLayout:spacing", 0.4,

			"plugValueWidget:type", "",

		),

		"preTasks" : (

			# Move to the left to give greater precedence to
			# the `tasks` plug at the top.
			"noduleLayout:section", "left",

		),

		"framesMode" : (

			"description",
			"""
			Determines the active frame range to be dispatched as
			follows :

			  - CurrentFrame dispatches the current frame only, as
			    specified by the `${frame}` context variable.
			  - FullRange uses the full frame range as specified by the
			    `${frameRange:start}` and `${frameRange:end}`
			    context variables.
			  - CustomRange uses a user defined range, as specified by
			    the `frameRange` plug.
			""",

			"preset:Current Frame", GafferDispatch.Dispatcher.FramesMode.CurrentFrame,
			"preset:Full Range", GafferDispatch.Dispatcher.FramesMode.FullRange,
			"preset:Custom Range", GafferDispatch.Dispatcher.FramesMode.CustomRange,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		),

		"frameRange" : (

			"description",
			"""
			The frame range to be used when framesMode is "CustomRange".
			""",

			"layout:visibilityActivator", "framesModeIsCustomRange",

		),

		"jobName" : (

			"description",
			"""
			A descriptive name for the job.
			"""

		),

		"jobsDirectory" : (

			"description",
			"""
			A directory to store temporary files used by the dispatcher.
			""",

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"path:leaf", False,

		),

	}

)

##################################################################################
# Dispatch
##################################################################################

def appendMenuDefinitions( menuDefinition, prefix = "" ) :

	menuDefinition.append(
		prefix + "/Repeat Previous",
		{
			"command" : __repeatLastDispatch,
			"shortCut" : "Ctrl+R",
			"active" : lambda menu : __getLastDispatcher( menu.ancestor( GafferUI.ScriptWindow ).scriptNode() ) is not None
		}
	)

def _dispatch( dispatcher, parentWindow  ) :

	with dispatcher.scriptNode().context() :
		with GafferUI.ErrorDialogue.ErrorHandler(
			title = "Errors Occurred During Dispatch",
			parentWindow = parentWindow
		) :
			dispatcher["task"].execute()
			__setLastDispatcher( dispatcher.scriptNode(), dispatcher )

def __setLastDispatcher( script, dispatcher ) :

	GafferUI.ScriptWindow.acquire( script ).__lastDispatcher = weakref.ref( dispatcher )

def __getLastDispatcher( script ) :

	try :
		return GafferUI.ScriptWindow.acquire( script ).__lastDispatcher()
	except AttributeError :
		return None

def __repeatLastDispatch( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	_dispatch( __getLastDispatcher( scriptWindow.scriptNode() ), scriptWindow )

##################################################################################
# DispatchButton
##################################################################################

class _DispatchButton( GafferUI.Button ) :

	def __init__( self, node, **kw ) :

		GafferUI.Button.__init__( self, "Dispatch", **kw )

		self.__node = node
		self.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ), scoped = False )

	def __clicked( self, button ) :

		_dispatch( self.__node, self.ancestor( GafferUI.Window ) )

##########################################################################
# Additional Metadata for TaskNode
##########################################################################

Gaffer.Metadata.registerNode(

	GafferDispatch.TaskNode,

	"layout:customWidget:dispatcherCreationWidget:widgetType", "GafferDispatchUI.DispatcherUI._DispatcherCreationWidget",

	plugs = {

		"dispatcher" : (

			"layout:activator:doesNotRequireSequenceExecution", lambda plug : not plug.node()["task"].requiresSequenceExecution(),

		),

		"dispatcher.batchSize" : (

			"description",
			"""
			Maximum number of frames to batch together when dispatching tasks.
			If the node requires sequence execution `batchSize` will be ignored.
			""",

			"layout:activator", "doesNotRequireSequenceExecution",

		),

		"dispatcher.immediate" : (

			"description",
			"""
			Causes this node to be executed immediately upon dispatch,
			rather than have its execution be scheduled normally by
			the dispatcher. For instance, when using the LocalDispatcher,
			the node will be executed immediately in the dispatching process
			and not in a background process as usual.

			When a node is made immediate, all upstream nodes are automatically
			considered to be immediate too, regardless of their settings.
			"""

		)

	}

)

class _DispatcherCreationWidget( GafferUI.Widget ) :

	def __init__( self, node, **kw ) :

		self.__frame = GafferUI.Frame(
			borderWidth = 4,
			borderStyle = GafferUI.Frame.BorderStyle.None_,
		)

		## \todo Add public "role" property to Frame widget and use that to determine styling.
		self.__frame._qtWidget().setProperty( "gafferDiff", "Other" )

		GafferUI.Widget.__init__( self, self.__frame, **kw )

		with self.__frame :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				GafferUI.Image( "infoSmall.png" )

				textColor = QtGui.QColor( *_styleColors["foregroundFaded"] ).name()
				label = GafferUI.Label(
					# Dummy `gaffer://...` URL is sufficient to trigger `linkActivatedSignal`, which is all we need.
					f'<a href="gaffer://createDispatcher"><font color={textColor}>Create a dispatcher</font></a> <font color={textColor}>to execute this node</font>',
				)
				label.linkActivatedSignal().connect( Gaffer.WeakMethod( self.__linkActivated ), scoped = False )

				GafferUI.Spacer( size = imath.V2i( 0 ), parenting = { "expand" : True } )

		self.__node = node
		self.__updateVisibility()

	def __updateVisibility( self ) :

		self.__frame.setVisible(
			not self.__node["task"].outputs() and
			not isinstance( self.__node, GafferDispatch.Dispatcher ) and
			not Gaffer.MetadataAlgo.readOnly( self.__node.parent() )
		)

	def __linkActivated( self, label, url ) :

		with Gaffer.UndoScope( self.__node.scriptNode() ) :

			dispatcher = GafferDispatch.LocalDispatcher()
			Gaffer.NodeAlgo.applyUserDefaults( dispatcher )
			self.__node.parent().addChild( dispatcher )
			dispatcher["tasks"][0].setInput( self.__node["task"] )

		selection = self.__node.scriptNode().selection()
		selection.clear()
		selection.add( dispatcher )

		self.__updateVisibility()
