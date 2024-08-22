##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

import types

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtWidgets

## Base class for UI components which display or manipulate a ScriptNode
# or its children. These make up the tabs in the UI layout.
class Editor( GafferUI.Widget ) :

	## Base class used to store settings for an Editor. We store our settings
	# as plugs on a node for a few reasons :
	#
	# - Some editors want to use an EditScopePlugValueWidget, and that requires
	#   it.
	# - We get a bunch of useful widgets and signals for free.
	# - Longer term we want to refactor all Editors to derive from Node, in the
	#   same way that View does already. This will let us serialise _all_ layout
	#   state in the same format we serialise node graphs in.
	# - The `userDefault` metadata provides a convenient way of configuring
	#   defaults.
	# - The PlugLayout we use to display the settings allows users to add their
	#   own widgets to the UI.
	#
	# Editor subclasses should subclass Settings as `EditorSubclass.Settings`,
	# and the settings node will then be created automatically upon
	# construction.
	class Settings( Gaffer.Node ) :

		def __init__( self ) :

			Gaffer.Node.__init__( self )

			# Hack to allow BackgroundTask to recover ScriptNode for
			# cancellation support - see `BackgroundTask.cpp`.
			## \todo Perhaps we can make this more natural at the point we derive
			# Editor from Node?
			self["__scriptNode"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.Serialisable )

	IECore.registerRunTimeTyped( Settings, typeName = "GafferUI::Editor::Settings" )

	def __init__( self, topLevelWidget, scriptNode, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )

		self._qtWidget().setFocusPolicy( QtCore.Qt.ClickFocus )

		assert( isinstance( scriptNode, Gaffer.ScriptNode ) )

		self.__scriptNode = scriptNode

		self.__settings = self.Settings()
		self.__settings.setName( self.__class__.__name__ + "Settings" )
		self.__settings["__scriptNode"].setInput( scriptNode["fileName"] )
		Gaffer.NodeAlgo.applyUserDefaults( self.__settings )
		self.settings().plugDirtiedSignal().connect( Gaffer.WeakMethod( self._updateFromSettings ) )

		self.__title = ""
		self.__titleChangedSignal = GafferUI.WidgetSignal()

		self.enterSignal().connect( Gaffer.WeakMethod( self.__enter ) )
		self.leaveSignal().connect( Gaffer.WeakMethod( self.__leave ) )

		self.__contextTracker = GafferUI.ContextTracker.acquireForFocus( self.__settings )
		self.__context = self.__contextTracker.context( self.__settings )
		self.__contextChangedConnection = self.__contextTracker.changedSignal( self.__settings ).connect(
			Gaffer.WeakMethod( self.__contextChanged ), scoped = True
		)

	def __del__( self ) :

		# Remove connection to ScriptNode now, on the UI thread.
		# Otherwise we risk deadlock if the Settings node gets garbage
		# collected in a BackgroundTask, which would attempt
		# cancellation of all tasks for the ScriptNode, including the
		# task itself. We also need to prevent emission of `plugDirtiedSignal()`
		# while we do that, to prevent half-destructed UIs from erroring.
		self.__settings.plugDirtiedSignal().disconnectAllSlots()
		self.__settings["__scriptNode"].setInput( None )

	def scriptNode( self ) :

		return self.__scriptNode

	def settings( self ) :

		return self.__settings

	## May be called to explicitly set the title for this editor. The
	# editor itself is not responsible for displaying the title - this
	# is left to the enclosing ui.
	def setTitle( self, title ) :

		if title == self.__title :
			return

		self.__title = title
		self.titleChangedSignal()( self )

	## May be overridden to provide sensible default behaviour for
	# the title, but must return BaseClass.getTitle() if it is non-empty.
	def getTitle( self ) :

		if self.__title :
			return self.__title

		# if there's no explicit title and a derived class
		# has overridden getTitle() then we return the empty
		# string to signify that the derived class is free
		# to return what it wants
		c = self.__class__
		while c is not Editor :
			if "getTitle" in c.__dict__ :
				return ""
			c = c.__bases__[0]

		# otherwise we default to using the classname
		return IECore.CamelCase.toSpaced( self.__class__.__name__ )

	## A signal emitted whenever the title changes.
	def titleChangedSignal( self ) :

		return self.__titleChangedSignal

	## Returns the context in which the Editor evaluates the node graph.
	def context( self ) :

		return self.__context

	## May be implemented by derived classes to update state based on a change of context.
	# To temporarily suspend calls to this function, use Gaffer.Signals.BlockedConnection( self._contextChangedConnection() ).
	def _updateFromContext( self, modifiedItems ) :

		pass

	def _contextChangedConnection( self ) :

		return self.__contextChangedConnection

	## May be implemented by derived classes to update based on changes to the
	# settings plugs.
	def _updateFromSettings( self, plug ) :

		pass

	## This must be implemented by all derived classes as it is used for serialisation of layouts.
	# It is not expected that the script being edited is also serialised as part of this operation -
	# instead the new script will be provided later as a variable named scriptNode. So a suitable
	# serialisation will look like "GafferUI.Editor( scriptNode )".
	def __repr__( self ) :

		raise NotImplementedError

	def __contextChanged( self, contextTracker ) :

		context = contextTracker.context( self.__settings )

		modifiedItems = {
			k for k in context.keys()
			if k not in self.__context or context[k] != self.__context[k]
		}
		modifiedItems.update( set( self.__context.keys() ) - set( context.keys() ) )

		self.__context = context
		if modifiedItems :
			self._updateFromContext( modifiedItems )

	@classmethod
	def types( cls ) :

		return list( cls.__namesToCreators.keys() )

	@classmethod
	def create( cls, name, scriptNode ) :

		return cls.__namesToCreators[name]( scriptNode = scriptNode )

	@classmethod
	def registerType( cls, name, creator ) :

		cls.__namesToCreators[name] = creator

	__namesToCreators = {}

	@classmethod
	def instanceCreatedSignal( cls ) :

		s = cls.__dict__.get( "__instanceCreatedSignal", None )
		if s is not None :
			return s

		s = Gaffer.Signals.Signal1()
		setattr( cls, "__instanceCreatedSignal", s )
		return s

	def _postConstructor( self ) :

		cls = self.__class__
		while hasattr( cls, "instanceCreatedSignal" ) :
			cls.instanceCreatedSignal()( self )
			cls = cls.__bases__[0]

	def __enter( self, widget ) :

		currentFocusWidget = QtWidgets.QApplication.focusWidget()

		# Don't disrupt in-progress text edits
		if isinstance( currentFocusWidget, ( QtWidgets.QLineEdit, QtWidgets.QPlainTextEdit ) ) :
			return

		try :
			gafferWidget = GafferUI.Widget._owner( currentFocusWidget )
		except :
			gafferWidget = None

		# Don't adjust focus if it is already with one of our children. This can happen,
		# for example, when a popup window launched by a child widget is dismissed.
		if gafferWidget is not None and ( gafferWidget is self or self.isAncestorOf( gafferWidget ) ) :
			return

		self._qtWidget().setFocus()

	def __leave( self, widget ) :

		self._qtWidget().clearFocus()
