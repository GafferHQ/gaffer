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

import bisect
import functools
import imath
import six
import weakref

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from ._TableView import _TableView

## The MessageWidget class displays a list of messages using the IECore MessageHandler
# format. Two display roles are available depending on the nature/quantity of
# the messages to be shown. Optional toolbars allow message navigation, search
# and severity selection.
class MessageWidget( GafferUI.Widget ) :

	# Messages : For presenting longer messages in detail. They are shown as line-wrapped paragraphs.
	# Log : For presenting a large number of messages in tabular form with un-wrapped lines.
	Role = IECore.Enum.create( "Messages", "Log" )

	# messageLevel : The minimum importance of message that will be displayed.
	# role : The style of message presentation.
	# toolbars : When true, search/navigation toolbars will be displayed with the widget.
	# follow : When enabled, the widget will auto-scroll to the latest message unless the
	#     user has set a custom scroll position (scrolling to the end will re-enable).
	def __init__( self, messageLevel = IECore.MessageHandler.Level.Info, role = Role.Messages, toolbars = False, follow = False, **kw ) :

		rows = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=4 )
		GafferUI.Widget.__init__( self, rows, **kw )

		upperToolbar = None

		with rows :

			if toolbars :

				upperToolbar = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
				with upperToolbar :

					GafferUI.Label( "Show" )
					self.__levelWidget = _MessageLevelWidget()
					self.__levelWidget.messageLevelChangedSignal().connect( Gaffer.WeakMethod( self.__messageLevelChanged ), scoped = False )

					GafferUI.Spacer( imath.V2i( 6 ), preferredSize = imath.V2i( 100, 0 ) )

			self.__table = _MessageTableView( follow = follow, expandRows = role is MessageWidget.Role.Messages )

			if toolbars :

				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal ) :

					shortcuts = self.__table.eventNavigationShortcuts()
					toolTips = { l : "Click to jump to next {} message [{}]".format( l, shortcuts[l] ) for l in _messageLevels }

					self.__summaryWidget = MessageSummaryWidget( displayLevel = IECore.MessageHandler.Level.Debug, hideUnusedLevels = False, buttonToolTip = toolTips )
					self.__summaryWidget.levelButtonClickedSignal().connect( Gaffer.WeakMethod( self.__levelButtonClicked ), scoped = False )

					GafferUI.Spacer( imath.V2i( 0 ) )

					self.__toEndButton = GafferUI.Button( image = "scrollToBottom.png", hasFrame = False )
					self.__toEndButton.setToolTip( "Scroll to bottom and follow new messages [B]" )
					self.__toEndButton.buttonPressSignal().connect( Gaffer.WeakMethod( self.__table.scrollToLatest ), scoped = False )

					GafferUI.Spacer( imath.V2i( 3 ), imath.V2i( 3 ) )

		if toolbars :

			upperToolbar.addChild( self.__table.searchWidget() )

			self.__table.messageLevelChangedSignal().connect( Gaffer.WeakMethod( self.__messageLevelChanged ), scoped = False )
			self.__table.messagesChangedSignal().connect( Gaffer.WeakMethod( self.__messagesChanged ), scoped = False )

			if follow :

				# When following, we manage the enabled state of the toEndButton based on the auto-scroll
				# state of the table view. If we're not, then it should remain active the whole time.
				self.__isFollowingMessagesChanged( self.__table )
				self.__table.isFollowingMessagesChangedSignal().connect( Gaffer.WeakMethod( self.__isFollowingMessagesChanged ), scoped = False )

		self.__messageHandler = _MessageHandler( self )

		self.setMessageLevel( messageLevel )
		self.setMessages( Gaffer.Private.IECorePreview.Messages() )

	## Displays the specified messages. To add individual messages, submit them
	# via the widget's message handler \see messageHandler().
	def setMessages( self, messages ) :

		self.__table.setMessages( messages )

	## Returns (a copy of) the messages displayed by the widget.
	def getMessages( self ) :

		return Gaffer.Private.IECorePreview.Messages( self.__table.getMessages() )

	## Clears all the displayed messages.
	def clear( self ) :

		self.__table.clear()

	## Returns a MessageHandler which will output to this Widget.
	## \threading It is safe to use the handler on threads other than the main thread.
	def messageHandler( self ) :

		return self.__messageHandler

	## It can be useful to forward messages captured by this widget
	# on to other message handlers - for instance to perform centralised
	# logging in addition to local display. This method returns a
	# CompoundMessageHandler which can be used for such forwarding -
	# simply add a handler with forwardingMessageHandler().addHandler().
	def forwardingMessageHandler( self ) :

		return self.__messageHandler._forwarder

	## Sets an IECore.MessageHandler.Level specifying which
	# type of messages will be visible to the user - levels above
	# that specified will be invisible. Note that the invisible
	# messages are still stored, so they can be made visible at a later
	# time by a suitable call to setMessageLevel(). This can be useful
	# for revealing debug messages only after a warning or error has
	# alerted the user to a problem.
	def setMessageLevel( self, messageLevel ) :

		assert( isinstance( messageLevel, IECore.MessageHandler.Level ) )

		self.__table.setMessageLevel( messageLevel )

	## Returns the current IECore.MessageHandler.Level at and below which
	# messages will be shown in the widget.
	def getMessageLevel( self ) :

		return self.__table.getMessageLevel()

	## Returns the number of messages being displayed, optionally
	# restricted to the specified level.
	def messageCount( self, level = None ) :

		messages = self.__table.getMessages()
		if level is None :
			return len( messages )
		else :
			return messages.count( level )

	# Friendship for our internal message handler
	def _addMessage( self, level, context, message ) :

		self.__table.addMessage( Gaffer.Private.IECorePreview.Message( level, context, message ) )

	# Signal callbacks - only called when toolbars are present

	def __messageLevelChanged( self, widget ) :

		messageLevel = widget.getMessageLevel()
		self.__table.setMessageLevel( messageLevel )
		self.__levelWidget.setMessageLevel( messageLevel )

	def __levelButtonClicked( self, level ) :

		if GafferUI.Widget.currentModifiers() == GafferUI.ModifiableEvent.Modifiers.Shift :
			self.__table.scrollToPreviousMessage( level )
		else :
			self.__table.scrollToNextMessage( level )

	def __messagesChanged( self, widget ) :

		self.__summaryWidget.setMessages( widget.getMessages() )

	def __isFollowingMessagesChanged( self, widget ) :

		self.__toEndButton.setEnabled( not widget.isFollowingMessages() )

# ================
# Internal Classes
# ================

# A message handler that adds messages directly to the widgets messages container.
class _MessageHandler( IECore.MessageHandler ) :

	def __init__( self, messageWidget ) :

		IECore.MessageHandler.__init__( self )

		self._forwarder = IECore.CompoundMessageHandler()
		self.__processingEvents = False

		# using a weak reference because we're owned by the MessageWidget,
		# so we mustn't have a reference back.
		self.__messageWidget = weakref.ref( messageWidget )

	def handle( self, level, context, msg ) :

		self._forwarder.handle( level, context, msg )

		w = self.__messageWidget()

		if w :

			application = QtWidgets.QApplication.instance()

			if QtCore.QThread.currentThread() == application.thread() :

				w._addMessage( level, context, msg )

				# Code like GafferCortexUI.OpDialogue has the option to run the op on the
				# main thread. We want to update the ui as they occur, so we force the
				# event loop to clear here. As processEvents may result in re-entry to this
				# function (the called code may desire to log another message through this
				# handler), we must guard against recursion so we don't run out of stack).
				if not self.__processingEvents :
					try :
						self.__processingEvents = True
						# Calling processEvents can cause almost anything to be executed,
						# including idle callbacks that might build UIs. We must push an
						# empty parent so that any widgets created will not be inadvertently
						# parented to the wrong thing.
						## \todo Calling `processEvents()` has also caused problems in the
						# past where a simple error message has then led to idle callbacks
						# being triggered which in turn triggered a graph evaluation. Having
						# a message handler lead to arbitarary code execution is not good! Is
						# there some way we can update the UI without triggering arbitrary
						# code evaluation?
						w._pushParent( None )
						application.processEvents( QtCore.QEventLoop.ExcludeUserInputEvents )
						w._popParent()
					finally :
						self.__processingEvents = False

			else :

				GafferUI.EventLoop.executeOnUIThread( functools.partial( w._addMessage, level, context, msg ) )

		else :
			# the widget has died. bad things are probably afoot so its best
			# that we output the messages somewhere to aid in debugging.
			IECore.MessageHandler.getDefaultHandler().handle( level, context, msg )

# =================
# Component Widgets
# =================

_messageLevels = (
	IECore.MessageHandler.Level.Error, IECore.MessageHandler.Level.Warning,
	IECore.MessageHandler.Level.Info, IECore.MessageHandler.Level.Debug
)

# Provides badge + count for each message level. The badges are clickable,
# \see levelButtonClickedSignal.
class MessageSummaryWidget( GafferUI.Widget ) :

	# displayLevel :     Only display counts or messages of this level or lower
	# hideUnusedLevels : When true, counts will be hidden for unused message levels
	# buttonToolTip :    The tooltip to display on the count buttons. This can be a string, applied to all buttons
	#                    or a dict, keyed by message level.
	def __init__( self, displayLevel = IECore.MessageHandler.Level.Warning, hideUnusedLevels = True, buttonToolTip = None, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.Widget.__init__( self, row, **kw )

		self.__hideUnusedLevels = hideUnusedLevels

		# Keep in a local too to allow us to capture the signal in a lambda without dragging in self
		buttonSignal = Gaffer.Signal1()
		self.__levelButtonClickedSignal = buttonSignal

		self.__buttons = {}

		with row :

			for level in _messageLevels :

				if int( level ) > int( displayLevel ) :
					break

				button = GafferUI.Button( image = str(level).lower() + "Small.png", hasFrame = False )
				button.clickedSignal().connect( functools.partial( lambda l, _ : buttonSignal( l ), level ), scoped = False )

				if isinstance( buttonToolTip, dict ) :
					button.setToolTip( buttonToolTip[ level ] )
				elif isinstance( buttonToolTip, six.string_types ) :
					button.setToolTip( buttonToolTip )

				self.__buttons[ level ] = button

		self.setMessages( Gaffer.Private.IECorePreview.Messages() )

	# Emitted with the level of the button that was pressed
	def levelButtonClickedSignal( self ) :

		return self.__levelButtonClickedSignal

	# Updates the button status and message count to that of the supplied messages
	def setMessages( self, messages ) :

		self.__messages = messages

		for level, button in self.__buttons.items() :

			count = messages.count( level )
			button.setEnabled( count > 0 )
			button.setText( "%d" % count )
			if self.__hideUnusedLevels :
				button.setVisible( count > 0 )

	def getMessages( self ) :

		return Gaffer.Private.IECorePreview.Messages( self.__messages )

## Provides a drop down menu to select an IECore.MessageHandler.Level
class _MessageLevelWidget( GafferUI.Widget ) :

	def __init__( self, messageLevel = IECore.MessageHandler.Level.Info, **kw ) :

		self.__menuButton = GafferUI.MenuButton( menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
		GafferUI.Widget.__init__( self, self.__menuButton, **kw )

		self.__menuButton._qtWidget().setFixedWidth( 75 )

		self.__level = None
		self.__messageLevelChangedSignal = GafferUI.WidgetSignal()
		self.setMessageLevel( messageLevel )

	def setMessageLevel( self, level ) :

		assert( isinstance( level, IECore.MessageHandler.Level ) )

		if level == self.__level :
			return

		self.__menuButton.setText( str(level) )
		self.__level = level

		self.__messageLevelChangedSignal( self )

	def getMessageLevel( self ) :

		return self.__level

	def messageLevelChangedSignal( self ) :

		return self.__messageLevelChangedSignal

	def __setMessageLevel( self, level, unused ) :

		self.setMessageLevel( level )

	def __menuDefinition( self ) :

		menuDefinition = IECore.MenuDefinition()
		for level in _messageLevels :
			menuDefinition.append(
				"/%s" % level,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setMessageLevel ), level ),
					"checkBox" : self.__level == level
				}
			)

		return menuDefinition

## Provides a search field along with result count display and navigation buttons for
# a _MessageTableView
class _MessageTableSearchWidget( GafferUI.Widget ) :

	def __init__( self, tableView, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.Widget.__init__( self, row, **kw )

		with row :

			self.__results = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
			with self.__results :

				self.__resultCount = GafferUI.Label()

				self.__prevButton = GafferUI.Button( image = "arrowLeft10.png", hasFrame = False )
				self.__prevButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ), scoped = False )

				self.__nextButton = GafferUI.Button( image = "arrowRight10.png", hasFrame = False )
				self.__nextButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ), scoped = False )

				self.__focusButton = GafferUI.Button( image = "searchFocusOff.png", hasFrame = False )
				self.__focusButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ), scoped = False )

			self.__searchField = GafferUI.TextWidget()
			# Edited catches focus-out and makes sure we update the search text
			self.__searchField.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__textEdited ), scoped = False )
			# Activated allows <enter> to repeatedly jump to the next search result
			self.__searchField.activatedSignal().connect( Gaffer.WeakMethod( self.__textActivated ), scoped = False )
			self.__searchField._qtWidget().setObjectName( "gafferSearchField" )
			self.__searchField._qtWidget().setPlaceholderText( "Search" )
			self.__searchField._qtWidget().setMaximumWidth( 250 )

		self.__prevButton.setToolTip( "Show previous match [P]" )
		self.__nextButton.setToolTip( "Show next match [N]" )

		# Though Qt provides clearButtonEnabled(), this seems to be missing its icon on macOS, resulting in a
		# clickable-but-not-visible clear button. As such we need to make our own. Icons need to be 16x16 exactly.
		clearImage = GafferUI.Image( "clearSearch.png" )
		self.__clearAction = QtWidgets.QAction( clearImage._qtIcon(), "Clear Search", None )
		self.__clearAction.triggered.connect( Gaffer.WeakMethod( self.__clear ) )
		self.__searchField._qtWidget().addAction( self.__clearAction, QtWidgets.QLineEdit.TrailingPosition )

		self.__table = weakref.ref( tableView )
		tableView.searchTextChangedSignal().connect( Gaffer.WeakMethod( self.__searchTextChanged ), scoped = False )
		tableView.focusSearchResultsChangedSignal().connect( Gaffer.WeakMethod( self.__focusSearchResultsChanged ), scoped = False )
		tableView.searchResultsChangedSignal().connect( Gaffer.WeakMethod( self.__searchResultsChanged ), scoped = False )

		self.__searchTextChanged( tableView )
		self.__focusSearchResultsChanged( tableView )
		self.__searchResultsChanged( tableView )

	def grabFocus( self ) :

		self.__searchField.grabFocus()
		self.__searchField.setSelection( None, None )

	def __buttonClicked( self, button ) :

		if button is self.__prevButton :
			self.__table().scrollToPreviousSearchResult( self )
		elif button is self.__nextButton :
			self.__table().scrollToNextSearchResult( self )
		elif button is self.__focusButton :
			self.__table().setFocusSearchResults( not self.__table().getFocusSearchResults() )

	def __textEdited( self, *unused ) :

		self.__table().setSearchText( self.__searchField.getText() )

	def __textActivated( self, *unused ) :

		self.__table().setSearchText( self.__searchField.getText() )

		if not self.__table().getFocusSearchResults() and self.__table().searchResultCount() > 0 :
			self.__table().scrollToNextSearchResult()

	def __clear( self ) :

		self.__table().clearSearch()
		self.grabFocus()

	def __searchTextChanged( self, table ) :

		text = table.getSearchText()
		self.__searchField.setText( text )
		self.__clearAction.setVisible( len(text) > 0 )

	def __focusSearchResultsChanged( self, table ) :

		isFocused = table.getFocusSearchResults()
		haveResults = table.searchResultCount()

		self.__focusButton.setImage( "searchFocusOn.png" if isFocused else "searchFocusOff.png" )
		self.__focusButton.setToolTip( "Show all [S]" if isFocused else "Only show matches [S]" )

		self.__prevButton.setEnabled( haveResults and not isFocused )
		self.__nextButton.setEnabled( haveResults and not isFocused )

	def __searchResultsChanged( self, table ) :

		haveSearchString = len( table.getSearchText() ) > 0
		self.__results.setVisible( haveSearchString )

		isFocused = table.getFocusSearchResults()
		count = table.searchResultCount()

		self.__resultCount.setText( "{} match{}".format( count, "" if count == 1 else "es" ) )
		self.__prevButton.setEnabled( count > 0 and not isFocused )
		self.__nextButton.setEnabled( count > 0 and not isFocused )

## The main table view presenting messages to the user.
#
# The view manages three QAbstractItemModels :
#
#  - __model :       A model presenting the raw message data.
#  - __filterModel : A proxy model filtering the message data for display based on the selected message level.
#  - __searchModel : A side-car proxy model used to determine the result count for the free-text search
#                    independent of the current display.
#
# The table's view is driven from the __displayModel - which is set to either the __filterModel or __searchModel
# depending on getFocusSearchResults().
#
# The optional __displayTransform proxy facilitates 'expanded rows' display (\see MessageWidge.Role.Messages), to
# avoid duplication of search/message navigation coding.
#
class _MessageTableView( GafferUI.Widget ) :

	SearchWidget = _MessageTableSearchWidget

	# - follow :     When set, the view will scroll to new messages as they are added (or to the end, when
	#                setMessages is used). If the user sets a custom scroll position, then following will be
	#                temporarily disabled. This state changed can be queried via isFollowingMessages.
	# - expandRows : When set, a proxy model will be set in __displayTransform that unpacks message columns into
	#                separate rows.
	def __init__( self, follow = False, expandRows = True, **kw ) :

		tableView = _TableView()
		GafferUI.Widget.__init__( self, tableView, **kw )

		self.__setupSignals()
		self.__setupModels( expandRows )
		self.__setupAppearance( expandRows )

		self.__didInitiateScroll = False
		self.__userSetScrollPosition( False )
		self.__setFollowMessages( follow )

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

		self.setMessageLevel( IECore.MessageHandler.Level.Info )

		self.__searchWidget = None

	# Provides a search widget controlling this view that can be embedded in the containing UI.
	def searchWidget( self ) :

		if self.__searchWidget is None :
			self.__searchWidget = _MessageTableView.SearchWidget( self )

		return self.__searchWidget

	def setMessageLevel( self, level ) :

		if self.__filterModel.getLevel() == level :
			return

		self.__filterModel.setLevel( level )
		self.__scrollIfNeeded()

		self.__messageLevelChangedSignal( self )

	def getMessageLevel( self ) :

		return self.__filterModel.getLevel()

	def messageLevelChangedSignal( self ) :

		return self.__messageLevelChangedSignal

	# Message management

	def setMessages( self, messages ) :

		self.__model.setMessages( messages )
		self.__scrollIfNeeded()

		self.__messagesChangedSignal( self )

	def getMessages( self ) :

		return self.__model.getMessages()

	def addMessage( self, message ) :

		self.__model.addMessage( message )
		self.__scrollIfNeeded()

		self.__messagesChangedSignal( self )

	def clear( self ) :

		self.__userSetScrollPosition( False )
		self.setMessages( Gaffer.Private.IECorePreview.Messages() )

	def messagesChangedSignal( self ) :

		return self.__messagesChangedSignal

	# Search

	def setSearchText( self, searchText ) :

		if searchText == self.__searchText :
			return

		self.__searchText = searchText
		self.__searchModel.setFilterWildcard( searchText )

		if not searchText :
			self.setFocusSearchResults( False )

		self.__searchTextChangedSignal( self )

	def getSearchText( self ) :

		return self.__searchText

	def clearSearch( self, *unused ) :

		self.setSearchText( "" )

	def searchResultCount( self ) :

		if not self.getSearchText() :
			return 0

		return self.__searchModel.rowCount()

	def scrollToNextSearchResult( self, *unused ) :

		self.__navigateSearchResult( previous = False )

	def scrollToPreviousSearchResult( self, *unused ) :

		self.__navigateSearchResult( previous = True )

	def setFocusSearchResults( self, focus ) :

		if self.getFocusSearchResults() == focus :
			return

		self.__setDisplayModel( self.__searchModel if focus else self.__filterModel )

		self.__focusSearchResultsChangedSignal( self )

	def getFocusSearchResults( self ) :

		return self.__displayModel == self.__searchModel

	def focusSearchResultsChangedSignal( self ) :

		return self.__focusSearchResultsChangedSignal

	def searchTextChangedSignal( self ) :

		return self.__searchTextChangedSignal

	def searchResultsChangedSignal( self ) :

		return self.__searchResultsChangedSignal

	# Message navigation

	def scrollToNextMessage( self, messageLevel, select = True, wrap = True ) :

		assert( isinstance( messageLevel, IECore.MessageHandler.Level ) )

		self.setFocusSearchResults( False )

		if messageLevel > self.getMessageLevel() :
			self.setMessageLevel( messageLevel )

		nextMessageIndex = self.__findNextMessage( messageLevel, reverse = False, wrap = wrap )
		self.__scrollToMessage( nextMessageIndex, select )

	def scrollToPreviousMessage( self, messageLevel, select = True, wrap = True ) :

		assert( isinstance( messageLevel, IECore.MessageHandler.Level ) )

		self.setFocusSearchResults( False )

		if messageLevel > self.getMessageLevel() :
			self.setMessageLevel( messageLevel )

		prevMessageIndex = self.__findNextMessage( messageLevel, reverse = True, wrap = wrap )
		self.__scrollToMessage( prevMessageIndex, select )


	def isFollowingMessages( self ) :

		return not self.__userScrollPosition

	def isFollowingMessagesChangedSignal( self ) :

		return self.__isFollowingMessagesChangedSignal

	def scrollToLatest( self, *unused ) :

		self.__userSetScrollPosition( False )
		self.__scrollToBottom()

	__eventLevelShortcuts = {
		"E" : IECore.MessageHandler.Level.Error,
		"W" : IECore.MessageHandler.Level.Warning,
		"I" : IECore.MessageHandler.Level.Info,
		"D" : IECore.MessageHandler.Level.Debug,
	}

	def eventNavigationShortcuts( self ) :

		return { v : k for k, v in self.__eventLevelShortcuts.items() }

	# Internal

	def __setupSignals( self ) :

		self.__messagesChangedSignal = GafferUI.WidgetSignal()
		self.__searchResultsChangedSignal = GafferUI.WidgetSignal()
		self.__searchTextChangedSignal = GafferUI.WidgetSignal()
		self.__focusSearchResultsChangedSignal = GafferUI.WidgetSignal()
		self.__messageLevelChangedSignal = GafferUI.WidgetSignal()
		self.__isFollowingMessagesChangedSignal = GafferUI.WidgetSignal()

	def __setupModels( self, expandRows ) :

		self.__model = _MessageTableModel()

		self.__filterModel = _MessageTableFilterModel()
		self.__filterModel.setSourceModel( self.__model )

		self.__searchModel = QtCore.QSortFilterProxyModel()
		self.__searchModel.setFilterCaseSensitivity( QtCore.Qt.CaseInsensitive )
		self.__searchModel.setFilterKeyColumn( -1 )
		self.__searchModel.setSourceModel( self.__filterModel )
		searchResultsChangedSlot = Gaffer.WeakMethod( self.__searchResultsChanged )
		self.__searchModel.rowsInserted.connect( searchResultsChangedSlot )
		self.__searchModel.rowsRemoved.connect( searchResultsChangedSlot )
		self.__searchModel.dataChanged.connect( searchResultsChangedSlot )
		self.__searchModel.modelReset.connect( searchResultsChangedSlot )
		# QSortFilterProxyModel doesn't support a transparent get/set (as it goes via regex)
		self.__searchText = ""

		self.__displayTransform = _MessageTableExpandedViewProxy() if expandRows else _MessageTableCollapseColumnsProxy()

		self.__setDisplayModel( self.__filterModel )

		self._qtWidget().setModel( self.__displayTransform )

	def __setupAppearance( self, expandRows ) :

		tableView = self._qtWidget()

		tableView.setEditTriggers( tableView.NoEditTriggers )
		tableView.setSelectionBehavior( QtWidgets.QAbstractItemView.SelectRows )
		tableView.setSelectionMode( QtWidgets.QAbstractItemView.ContiguousSelection )

		tableView.verticalHeader().setVisible( False )
		tableView.horizontalHeader().setVisible( False )

		tableView.setHorizontalScrollMode( tableView.ScrollPerPixel )

		tableView.setShowGrid( False )

		if expandRows :

			tableView.horizontalHeader().setSectionResizeMode( 0, QtWidgets.QHeaderView.Stretch )
			tableView.verticalHeader().setSectionResizeMode( QtWidgets.QHeaderView.ResizeToContents )
			tableView.setWordWrap( True )

		else :

			tableView.verticalHeader().setSectionResizeMode( QtWidgets.QHeaderView.Fixed )
			tableView.verticalHeader().setDefaultSectionSize( 14 )

			# Fortunately we have a fixed set of known message levels so its ok to hard code this here
			tableView.setColumnWidth( 0, 75 )
			tableView.horizontalHeader().setStretchLastSection( True )

			tableView.setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAsNeeded )

			tableView.setWordWrap( False )

	def __setDisplayModel( self, model ) :

		self.__displayModel = model
		self.__displayTransform.setSourceModel( model )

	#
	# A display index refers to indices into self.__displayModel, before any self.__displayTransform
	#

	def __displayIndexForMessage( self, messageIndex ) :

		displayIndex = self.__filterModel.mapFromSource( self.__model.index( messageIndex, 0 ) )
		if self.__displayModel != self.__filterModel :
			displayIndex = self.__displayModel.mapFromSource( displayIndex )
		return displayIndex

	# Selection

	def __selectedDisplayIndexes( self ) :

		displayIndexes = self._qtWidget().selectedIndexes()
		if self.__displayTransform is not None :
			displayIndexes = [ self.__displayTransform.mapToSource(i) for i in displayIndexes ]

		return displayIndexes

	def __selectDisplayIndex( self, index ) :

		if not index.isValid() :
			return

		selectionMode = QtCore.QItemSelectionModel.ClearAndSelect | QtCore.QItemSelectionModel.Rows
		selection = self._qtWidget().selectionModel()

		if self.__displayTransform is not None :
			# Expand the selection to make sure we have the whole row as the transform may map columns to rows
			row = index.row()
			lastColumn = index.model().columnCount() - 1
			rowSelection = QtCore.QItemSelection( index.sibling( row, 0 ), index.sibling( row, lastColumn ) )
			selection.select( self.__displayTransform.mapSelectionFromSource( rowSelection ), selectionMode )
		else :
			selection.select( index, selectionMode )

	def __selectedMessageIndices( self ) :

		# Gets back to the base model index, whose indices equate to the actual message container indices.
		def messageModelIndex( index ) :
			model = self.__displayModel
			while hasattr( model, "sourceModel" ) :
				index = model.mapToSource( index )
				model = model.sourceModel()
			return index

		# remove duplicates, either due to the expanded display model, or multi-column selection
		return sorted( { messageModelIndex( i ).row() for i in self.__selectedDisplayIndexes() } )

	# Scrolling

	def __scrollToDisplayIndex( self, index ) :

		if not index.isValid() :
			return

		if self.__displayTransform is not None :
			index = self.__displayTransform.mapFromSource( index )

		self._qtWidget().scrollTo( index )

	def __scrollToBottom( self ) :

		self.__didInitiateScroll = True
		self._qtWidget().scrollToBottom()
		self.__didInitiateScroll = False

	def __scrollToMessage( self, messageIndex, select ) :

		if messageIndex is None :
			return

		displayIndex = self.__displayIndexForMessage( messageIndex )
		if displayIndex.isValid() :
			self.__scrollToDisplayIndex( displayIndex )
			self.__userSetScrollPosition( True )
			if select :
				self.__selectDisplayIndex( displayIndex )

	# Search result management

	def __searchResultsChanged( self, *unused ) :

		self.__searchResultsChangedSignal( self )

	def __navigateSearchResult( self, previous = False ) :

		if self.searchResultCount() == 0 :
				return

		selected = self.__selectedDisplayIndexes()
		selectedIndex = selected[0] if selected else None

		if selectedIndex is None :
			row = ( self.__searchModel.rowCount() - 1 ) if previous else 0
			resultIndex = self.__searchModel.mapToSource( self.__searchModel.index( row, 0 ) )
		else :
			resultIndex = self.__adjacentSearchResultDisplayIndex( selectedIndex, previous )

		if resultIndex is not None :
			self.__scrollToDisplayIndex( resultIndex )
			self.__selectDisplayIndex( resultIndex )

	def __adjacentSearchResultDisplayIndex( self, currentDisplayIndex, previous ) :

		displayIsSearchModel = currentDisplayIndex.model() == self.__searchModel

		if displayIsSearchModel :
			currentResult = currentDisplayIndex
		else :
			currentResult = self.__searchModel.mapFromSource( currentDisplayIndex )

		result = None

		if currentResult.isValid() :
			# If the selected row is already a search result, we simply increment/decrement to the next
			currentRow = currentResult.row()
			if previous :
				if currentRow > 0 :
					result = currentResult.sibling( currentRow - 1, 0 )
			else :
				if currentRow < currentResult.model().rowCount() - 1 :
					result = currentResult.sibling( currentRow + 1, 0 )

		else :
			# Find the nearest result
			result = self.__findNearestSearchResult( currentDisplayIndex, previous )

		if result is not None :
			return result if displayIsSearchModel else self.__searchModel.mapToSource( result )

	# Exposes a proxy models source rows via the sequence interface
	class __ModelToSourceRowsWrapper() :

		def __init__( self, searchModel ) :
			self.__model = searchModel

		def __len__( self ) :
			return self.__model.rowCount()

		def __getitem__( self, index ) :
			return self.__model.mapToSource( self.__model.index( index, 0 ) ).row()

	def __findNearestSearchResult( self, displayIndex, before = False ) :

		model = self.__searchModel
		selectedDisplayRow = displayIndex.row()

		# As bisect needs a sequence type, but we don't want to pre-generate a list of all result
		# source rows, we wrap the model in a class that will convert the lookups to our source rows.
		bisectable = _MessageTableView.__ModelToSourceRowsWrapper( model )

		if before :
			nearest = bisect.bisect_left( bisectable, selectedDisplayRow ) - 1
		else :
			nearest = bisect.bisect_right( bisectable, selectedDisplayRow )

		if nearest < 0 or nearest == model.rowCount() :
			return None

		return model.index( nearest, 0 )

	# Message navigation

	def __findNextMessage( self, messageLevel, reverse = False, wrap = True ) :

		lastIndex = len( self.__model.getMessages() ) - 1

		searchStart = lastIndex if reverse else 0

		selected = self.__selectedMessageIndices()
		if selected :
			i = selected[0]
			searchStart = ( i - 1 ) if reverse else ( i + 1 )

		nextMessageIndex = self.__nextMessageIndex( messageLevel, searchStart, 0 if reverse else lastIndex  )
		if nextMessageIndex is None and selected and wrap :
			nextMessageIndex = self.__nextMessageIndex( messageLevel, lastIndex if reverse else 0, searchStart )

		return nextMessageIndex

	def __nextMessageIndex( self, messageLevel, startIndex, endIndex ) :

		reverse = startIndex > endIndex
		step = -1 if reverse else 1
		rangeEnd = endIndex + step

		messages = self.__model.getMessages()
		if startIndex < 0 or startIndex >= len(messages) :
			return None

		for i in range( startIndex, rangeEnd, step ) :
			if messages[i].level == messageLevel :
				return i

		return None

	# Auto-follow

	def __setFollowMessages( self, follow ) :

		self.__followMessages = follow

		if self.__followMessages :
			slot = Gaffer.WeakMethod( self.__vScrollBarValueChanged )
			self._qtWidget().verticalScrollBar().valueChanged.connect( slot )

	def __scrollIfNeeded( self ) :

		if not self.__followMessages :
			return

		if self.__userScrollPosition :
			return

		self.__scrollToBottom()

	def __vScrollBarValueChanged( self, value ) :

		if self.__didInitiateScroll :
			return

		if ( self._qtWidget().verticalScrollBar().maximum() - value ) == 0 :
			self.__userSetScrollPosition( False )
		else:
			self.__userSetScrollPosition( True )

	def __userSetScrollPosition( self, didSet ) :

		self.__userScrollPosition = didSet
		self.__isFollowingMessagesChangedSignal( self )

	# Keyboard shortcuts

	def __keyPress( self, unused, event ) :

		if event.key == "C" and event.modifiers == event.Modifiers.Control :

			self.__copySelectedRows()
			return True

		elif event.key == "A" and event.modifiers == event.Modifiers.Control :
			self._qtWidget().selectAll()
			return True

		elif event.key == "F" and event.modifiers == event.Modifiers.Control and self.__searchWidget is not None :

			self.__searchWidget.grabFocus()
			return True

		elif event.key in self.__eventLevelShortcuts :

			if event.modifiers == event.Modifiers.None_ :
				self.scrollToNextMessage( self.__eventLevelShortcuts[ event.key ] )
				return True
			elif event.modifiers == event.Modifiers.Shift :
				self.scrollToPreviousMessage( self.__eventLevelShortcuts[ event.key ] )
				return True

		elif event.key == "S" and event.modifiers == event.Modifiers.None_ :

			self.setFocusSearchResults( not self.getFocusSearchResults() )
			return True

		elif event.key == "P" and event.modifiers == event.Modifiers.None_ :

			self.scrollToPreviousSearchResult()
			return True

		elif event.key == "N" and event.modifiers == event.Modifiers.None_ :

			self.scrollToNextSearchResult()
			return True

		elif event.key in ( "End", "B" ) and event.modifiers == event.Modifiers.None_ :

			self.__userSetScrollPosition( False )
			self.__scrollToBottom()
			return True

		return False

	# Copy/Paste

	def __copySelectedRows( self ) :

		# TODO only slected, can we get something for free from QT?

		messageIndices = self.__selectedMessageIndices()
		text = self.__plainTextForMessages( messageIndices )
		QtWidgets.QApplication.clipboard().setText( text )

	def __plainTextForMessages( self, messageIndices ) :

		messages = self.getMessages()
		indices = messageIndices or range( len(messages) )

		text = ""
		for i in indices :
			m = messages[ i ]
			text += "%s [%s] %s\n" % ( str(m.level).ljust(7).upper(), m.context, m.message )

		return text

# Combines context and message to work around column sizing issues. Asking the table view
# to autoresize sections is prohibitively slow for the update rate that we receive messages.
# Having context as a separate column consequently requires either a fixed width, specified
# by the parent UI, or truncated contents. Neither or which are ideal. This proxy combines
# context/message such that we don't have to worry about how long the context string is.
# It would save some boilerplate if we derived from QIdentityProxyModel (though strictly, this
# wouldn't be an identity proxy), but it is missing from the bindings.
class _MessageTableCollapseColumnsProxy( QtCore.QAbstractProxyModel ) :

	def columnCount( self, parent ) :

		return 2

	def rowCount( self, parent ) :

		return self.sourceModel().rowCount()

	def mapFromSource( self, sourceIndex ):

		if not sourceIndex.isValid() or sourceIndex.row() < 0 :
			return QtCore.QModelIndex()

		# This does double up on indexes, but means you get the
		# correct mapping for selection rectangles.
		if sourceIndex.column() == 2 :
			return self.index( sourceIndex.row(), 1 )
		else :
			return self.index( sourceIndex.row(), sourceIndex.column() )

	def mapToSource( self, proxyIndex ) :

		if not proxyIndex.isValid() or proxyIndex.row() < 0 :
			return QtCore.QModelIndex()

		if proxyIndex.column() == 1 :
			return self.sourceModel().index( proxyIndex.row(), 2 )
		else :
			return self.sourceModel().index( proxyIndex.row(), proxyIndex.column() )

	def data( self, index, role = QtCore.Qt.DisplayRole ) :

		sourceModel = self.sourceModel()

		if index.column() == 1 and role == QtCore.Qt.DisplayRole :
			contextIndex = sourceModel.index( index.row(), 1 )
			messageIndex = sourceModel.index( index.row(), 2 )
			return "%s : %s" % (
				sourceModel.data( contextIndex, role ),
				sourceModel.data( messageIndex, role )
			)

		return sourceModel.data( self.mapToSource( index ), role )

	def setSourceModel( self, model ) :

		oldModel = self.sourceModel()

		# We don't encounter column changes so we don't need to bother with those signals here.
		# We don't have to worry about parent as it's always invalid as the model isn't a tree.
		for signal in (
			"modelReset", "rowsAboutToBeInserted", "rowsInserted", "rowsAboutToBeRemoved", "rowsRemoved"
		) :
			slot = getattr( self, signal )
			if oldModel :
				getattr( oldModel, signal ).disconnect( slot )
			if model :
				getattr( model, signal ).connect( slot )

		if oldModel :
			oldModel.dataChanged.disconnect( self.__dataChanged )
		if model :
			model.dataChanged.connect( self.__dataChanged )

		self.beginResetModel()
		QtCore.QAbstractProxyModel.setSourceModel( self, model )
		self.endResetModel()

	def index( self, row, column, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return QtCore.QModelIndex()

		return self.createIndex( row, column )

	def parent( self, index ) :

		return QtCore.QModelIndex()

	def __dataChanged( self, topLeft, bottomRight, roles ) :

		self.dataChanged.emit( self.mapFromSource( topLeft ), self.mapFromSource( bottomRight ), roles )

# Expands messages into a two-row presentation, with level + context on one
# row, and the body of the message on the next.
class _MessageTableExpandedViewProxy( QtCore.QAbstractProxyModel ) :

	def columnCount( self, parent ) :

		return 1

	def rowCount( self, parent ) :

		if parent.isValid() :
			return 0

		return 2 * self.sourceModel().rowCount() if self.sourceModel() else 0

	def mapFromSource( self, sourceIndex )  :

		if not sourceIndex.isValid() or sourceIndex.row() < 0 :
			return QtCore.QModelIndex()

		row = sourceIndex.row() * 2
		if sourceIndex.column() == int( _MessageTableModel.Column.Message ) :
			row += 1

		return self.index( row, 0 )

	def mapToSource( self, proxyIndex ) :

		if not proxyIndex.isValid() or proxyIndex.row() < 0 :
			return QtCore.QModelIndex()

		if proxyIndex.row() % 2 == 0 :
			column = _MessageTableModel.Column.Level
		else :
			column = _MessageTableModel.Column.Message

		return self.sourceModel().index( proxyIndex.row() // 2, int(column) )

	def data( self, index, role = QtCore.Qt.DisplayRole ) :

		source = self.sourceModel()
		sourceIndex = self.mapToSource( index )

		# We combine the level/context columns into one row, and the message into another

		if index.row() % 2 == 0 :

			levelIndex = source.index( sourceIndex.row(), 0 )

			if role == QtCore.Qt.DisplayRole :
				# Combine level/context
				contextIndex = source.index( sourceIndex.row(), 1 )
				return "%s: %s" % ( source.data( levelIndex, role ), source.data( contextIndex, role ) )

			elif role == QtCore.Qt.ForegroundRole :
				# In expanded mode, only colourise the header
				return self.__headerColor( source.data( levelIndex, _MessageTableModel.ValueRole ) )

		else :

			if role == QtCore.Qt.DisplayRole :
				# Add a new line to separate messages out
				return "%s\n" % source.data( sourceIndex, role )

			elif role == QtCore.Qt.ForegroundRole :
				return GafferUI._Variant.toVariant( GafferUI._StyleSheet.styleColor( "foreground" ) )

		return source.data( sourceIndex, role )

	def index( self, row, column, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return QtCore.QModelIndex()

		return self.createIndex( row, column )

	def parent( self, index ) :

		return QtCore.QModelIndex()

	def setSourceModel( self, model ) :

		oldModel = self.sourceModel()

		# We don't encounter column changes so we don't need to bother with those signals here.
		for signal in (
			"dataChanged", "modelReset",
			"rowsAboutToBeInserted", "rowsInserted", "rowsAboutToBeRemoved", "rowsRemoved"
		) :
			slot = getattr( self, "_MessageTableExpandedViewProxy__" + signal )
			if oldModel :
				getattr( oldModel, signal ).disconnect( slot )
			if model :
				getattr( model, signal ).connect( slot )

		self.beginResetModel()
		QtCore.QAbstractProxyModel.setSourceModel( self, model )
		self.endResetModel()

	def __headerColor( self, levelData ) :

		# Sadly as QAbstractProxyModel is, well - abstract, we can't add a constructor of our own
		# as python will complain we haven't called the base constructor. Uses _ to avoid mangling fun.
		if not hasattr( self, "_colorMap" ) :
			self._colorMap = {}
			for l in _messageLevels :
				self._colorMap[ int(l) ] = GafferUI._Variant.toVariant( GafferUI._StyleSheet.styleColor( "foreground%s" % l ) )

		return self._colorMap[ levelData ]

	# Signal forwarding.

	def __dataChanged( self, topLeft, bottomRight, roles ) :

		self.dataChanged.emit( self.index( topLeft.row() * 2, 0 ), self.index( ( bottomRight.row() * 2 ) + 1, 0 ), roles )

	def __modelReset( self ) :

		self.modelReset.emit()

	def __rowsAboutToBeInserted( self, parent, start, end ) :

		self.rowsAboutToBeInserted.emit( QtCore.QModelIndex(), start * 2, end * 2 + 1 )

	def __rowsInserted( self, parent, start, end ) :

		self.rowsInserted.emit( QtCore.QModelIndex(), start * 2, end * 2 + 1 )

	def __rowsAboutToBeRemoved( self, parent, start, end ) :

		self.rowsAboutToBeRemoved.emit( QtCore.QModelIndex(), start * 2, end * 2 + 1 )

	def __rowsRemoved( self, parent, start, end ) :

		self.rowsRemoved.emit( QtCore.QModelIndex(), start * 2, end * 2 + 1 )


# Provides filtering based on message level. This isn't directly used for search
# filtering as we often want search not to affect the number messages displayed.
class _MessageTableFilterModel( QtCore.QSortFilterProxyModel ) :

	def __init__( self, level = IECore.MessageHandler.Level.Info, *kw ) :

		QtCore.QSortFilterProxyModel.__init__( self, *kw )
		self.setLevel( level )

	def setLevel( self, level ) :

		self.__maxLevel = level
		self.invalidateFilter()

	def getLevel( self ) :

		return self.__maxLevel

	# Overrides for methods inherited from QSortFilterProxyModel
	# --------------------------------------------------------

	def filterAcceptsRow( self, sourceRow, sourceParent ) :

		levelIndex = self.sourceModel().index( sourceRow, _MessageTableModel.Column.Level, sourceParent )
		return self.sourceModel().data( levelIndex, _MessageTableModel.ValueRole ) <= self.__maxLevel

# The base TabelModel representing the underlying message data.
class _MessageTableModel( QtCore.QAbstractTableModel ) :

	ColumnCount = 3
	Column = IECore.Enum.create( "Level", "Context", "Message" )

	# A role to allow access the underlying Message data, without any display coercion.
	ValueRole = 100

	def __init__( self, messages = None, parent = None ) :

		QtCore.QAbstractTableModel.__init__( self, parent )

		self.__messages = messages

	def setMessages( self, messages ) :

		# We make use of existing rows here rather than resetting
		# the model as it avoids flickering where the view first
		# scrolls to the top, and then is re-scrolled back to the
		# bottom.

		firstDifference = messages.firstDifference( self.__messages ) if self.__messages is not None else 0

		numRows = len( self.__messages ) if self.__messages else 0
		targetNumRows = len( messages )

		if targetNumRows > numRows :

			self.beginInsertRows( QtCore.QModelIndex(), numRows, targetNumRows - 1 )
			self.__messages = messages
			self.endInsertRows()

		elif targetNumRows < numRows :

			self.beginRemoveRows( QtCore.QModelIndex(), targetNumRows, numRows - 1 )
			self.__messages = messages
			self.endRemoveRows()

		else :

			self.__messages = messages

		if targetNumRows > 0 :

			lastRowIndex = targetNumRows - 1
			if firstDifference is not None :
				self.dataChanged.emit(
					self.index( firstDifference, 0 ),
					self.index( lastRowIndex, self.columnCount() - 1 )
				)

	def getMessages( self ) :

		return self.__messages

	def addMessage( self, message ) :

		nextIndex = self.rowCount()
		self.beginInsertRows( QtCore.QModelIndex(), nextIndex, nextIndex )
		self.__messages.add( message )
		self.endInsertRows()

	# Overrides for methods inherited from QAbstractTableModel
	# --------------------------------------------------------

	def rowCount( self, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return 0

		if self.__messages is None :
			return 0

		return len( self.__messages )

	def columnCount( self, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return 0

		return _MessageTableModel.ColumnCount

	def headerData( self, section, orientation, role ) :

		if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal :
			return str( _MessageTableModel.Column( section ) )

	def flags( self, index ) :

		return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

	def data( self, index, role ) :

		if not index.isValid() :
			return None

		if role == QtCore.Qt.DisplayRole or role == _MessageTableModel.ValueRole :

			message = self.__messages[ index.row() ]

			if index.column() == int( _MessageTableModel.Column.Level ) :
				return str(message.level).upper() if role == QtCore.Qt.DisplayRole else message.level
			elif index.column() == int( _MessageTableModel.Column.Context ) :
				return message.context
			elif index.column() == int( _MessageTableModel.Column.Message ) :
				return message.message

		elif role == QtCore.Qt.ForegroundRole :

			message = self.__messages[ index.row() ]
			# Keep info level messages white
			suffix = "" if message.level == IECore.MessageHandler.Level.Info else str( message.level )
			return GafferUI._Variant.toVariant( GafferUI._StyleSheet.styleColor( "foreground%s" % suffix ) )
