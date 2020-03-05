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

Gaffer.Metadata.registerNode(

	Gaffer.Expression,

	"description",
	"""
	Utility node for computing values via
	scripted expressions.
	""",

	"layout:customWidget:Expression:widgetType", "GafferUI.ExpressionUI.ExpressionWidget",
	"nodeGadget:type", "GafferUI::AuxiliaryNodeGadget",
	"auxiliaryNodeGadget:label", "e",

	plugs = {

		"user" : (

			"plugValueWidget:type", "",

		),

	}

)

# PlugValueWidget popup menu for creating expressions
##########################################################################

def __createExpression( plug, language ) :

	node = plug.node()
	parentNode = node.ancestor( Gaffer.Node )

	with Gaffer.UndoScope( node.scriptNode() ) :

		expressionNode = Gaffer.Expression()
		parentNode.addChild( expressionNode )

		expressionNode.setExpression(
			Gaffer.Expression.defaultExpression( plug, language ),
			language
		)

	__editExpression( plug )

def __editExpression( plug ) :

	expressionNode = plug.getInput().node()

	GafferUI.NodeEditor.acquire( expressionNode )

def __popupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if not isinstance( plug, Gaffer.ValuePlug ) :
		return

	node = plug.node()
	if node is None or node.parent() is None :
		return

	input = plug.getInput()
	if input is not None or not plugValueWidget._editable() or Gaffer.MetadataAlgo.readOnly( plug ) :
		return

	languages = [ l for l in Gaffer.Expression.languages() if Gaffer.Expression.defaultExpression( plug, l ) ]
	if not languages :
		return

	menuDefinition.prepend( "/ExpressionDivider", { "divider" : True } )
	for language in languages :
		menuDefinition.prepend(
			"/Create " + IECore.CamelCase.toSpaced( language ) + " Expression...",
			{
				"command" : functools.partial( __createExpression, plug, language )
			}
		)

GafferUI.PlugValueWidget.popupMenuSignal().connect( __popupMenu, scoped = False )

# ExpressionWidget
##########################################################################

class ExpressionWidget( GafferUI.Widget ) :

	def __init__( self, node, **kw ) :

		column = GafferUI.ListContainer( spacing = 4 )
		GafferUI.Widget.__init__( self, column, **kw )

		self.__node = node

		with column :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				GafferUI.Label( "Language" )
				self.__languageMenu = GafferUI.MenuButton( "", menu = GafferUI.Menu( Gaffer.WeakMethod( self.__languageMenuDefinition ) ) )
				self.__languageMenu.setEnabled( not Gaffer.MetadataAlgo.readOnly( node ) )

			self.__textWidget = GafferUI.MultiLineTextWidget( role = GafferUI.MultiLineTextWidget.Role.Code )
			self.__textWidget.setEditable( not Gaffer.MetadataAlgo.readOnly( node ) )

			self.__textWidget.activatedSignal().connect( Gaffer.WeakMethod( self.__activated ), scoped = False )
			self.__textWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__editingFinished ), scoped = False )
			self.__textWidget.dropTextSignal().connect( Gaffer.WeakMethod( self.__dropText ), scoped = False )
			self.__textWidget.contextMenuSignal().connect( Gaffer.WeakMethod( self.__expressionContextMenu ), scoped = False )

			self.__messageWidget = GafferUI.MessageWidget()

		self.__node.expressionChangedSignal().connect( Gaffer.WeakMethod( self.__expressionChanged ), scoped = False )
		self.__node.errorSignal().connect( Gaffer.WeakMethod( self.__error ), scoped = False )

		self.__update()

	def node( self ) :

		return self.__node

	def textWidget( self ) :

		return self.__textWidget

	__expressionContextMenuSignal = Gaffer.Signal2()
	## This signal is emitted whenever a popup menu
	# for an ExpressionWidget is about to be shown.
	# This provides an opportunity to customise the
	# menu from external code. The signature for
	# slots is ( menuDefinition, widget ), and slots
	# should just modify the menu definition in place.
	@classmethod
	def expressionContextMenuSignal( cls ) :

		return cls.__expressionContextMenuSignal

	def __expressionContextMenuDefinition( self ) :

		menuDefinition = IECore.MenuDefinition()

		bookmarks = Gaffer.MetadataAlgo.bookmarks( self.__node.parent() )

		def __bookmarkMenu( bookmarks ) :

			bookmarkMenuDefinition = IECore.MenuDefinition()

			def __walk( graphComponent, result ) :

				if (
					isinstance( graphComponent, Gaffer.ValuePlug ) and
					self.__node.identifier( graphComponent ) and
					not graphComponent.relativeName( graphComponent.node() ).startswith( "__" )
				) :
					result.append( graphComponent )

				for c in graphComponent.children( Gaffer.Plug ) :
					__walk( c, result )

			for bookmark in bookmarks :

				compatiblePlugs = []
				__walk( bookmark, compatiblePlugs )

				if not compatiblePlugs :
					continue

				for plug in compatiblePlugs :
					label = "/" + bookmark.getName()
					if len( compatiblePlugs ) > 1 :
						label += "/"  + plug.relativeName( bookmark )
					bookmarkMenuDefinition.append(
						label,
						{
							"command" : functools.partial( self.__textWidget.insertText, self.__node.identifier( plug ) ),
							"active" : self.__textWidget.getEditable() and not Gaffer.MetadataAlgo.readOnly( self.__node['__expression'] ),
						}
					)

			return bookmarkMenuDefinition

		menuDefinition.append( "/Insert Bookmark", { "subMenu" : functools.partial( __bookmarkMenu, bookmarks ) } )

		self.expressionContextMenuSignal()( menuDefinition, self )

		return menuDefinition

	def __expressionContextMenu( self, *unused ) :

		menuDefinition = self.__expressionContextMenuDefinition()
		if not len( menuDefinition.items() ) :
			return False

		title = self.__node.relativeName( self.__node.scriptNode() )
		title = ".".join( [ IECore.CamelCase.join( IECore.CamelCase.split( x ) ) for x in title.split( "." ) ] )

		self.____expressionContextMenu = GafferUI.Menu( menuDefinition, title = title )
		self.____expressionContextMenu.popup()

		return True

	def __update( self ) :

		expression, language = self.__node.getExpression()

		self.__textWidget.setText( expression )
		self.__textWidget.setEnabled( bool( language ) )
		self.__languageMenu.setText( IECore.CamelCase.toSpaced( language ) if language else "Choose..." )

		self.__messageWidget.clear()
		self.__messageWidget.setVisible( False )

	def __languageMenuDefinition( self ) :

		currentLanguage = self.__node.getExpression()[1]

		result = IECore.MenuDefinition()
		for language in self.__node.languages() :
			result.append(
				"/" + IECore.CamelCase.toSpaced( language ),
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__changeLanguage ), language = language ),
					"checkBox" : language == currentLanguage,
				}
			)

		return result

	def __changeLanguage( self, unused, language ) :

		## \todo Can we do better? Maybe start with the default expression
		# for the current output plugs?
		self.__node.setExpression( "", language )

	def __setExpression( self ) :

		language = self.__node.getExpression()[1]
		with Gaffer.UndoScope( self.__node.scriptNode() ) :
			try :
				self.__node.setExpression( self.__textWidget.getText(), language )
				self.__messageWidget.setVisible( False )
			except Exception as e :
				self.__messageWidget.clear()
				self.__messageWidget.setVisible( True )
				self.__messageWidget.messageHandler().handle(
					IECore.Msg.Level.Error, "Parse error", str( e )
				)

	def __expressionChanged( self, node ) :

		self.__update()

	def __activated( self, widget ) :

		self.__setExpression()

	def __editingFinished( self, widget ) :

		self.__setExpression()

	def __dropText( self, widget, dragData ) :

		if isinstance( dragData, IECore.StringVectorData ) :
			return repr( list( dragData ) )
		elif isinstance( dragData, Gaffer.Plug ) :
			name = self.__node.identifier( dragData )
			return name if name else None
		elif isinstance( dragData, Gaffer.Set ) :
			if len( dragData ) == 1 :
				return self.__dropText( widget, dragData[0] )
			else :
				return None

		return None

	def __error( self, plug, source, error ) :

		# Error signal can be emitted on any thread, but we need to be on the UI
		# thread to display it.
		GafferUI.EventLoop.executeOnUIThread( functools.partial( self.__displayError, error ) )

	# An error in the expression could occur during a compute triggered by a repaint.
	# ( For example, if a user uses an expression to drive Backdrop text )
	# If we forced a repaint right away, this would be a recursive repaint which could cause
	# a Qt crash, so we wait for idle.
	@GafferUI.LazyMethod()
	def __displayError( self, error ) :

		self.__messageWidget.setVisible( True )
		self.__messageWidget.messageHandler().handle( IECore.Msg.Level.Error, "Execution error", error )
