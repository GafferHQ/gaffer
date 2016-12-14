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

	"layout:customWidget:Expression:widgetType", "GafferUI.ExpressionUI._ExpressionWidget",

	plugs = {

		# This plug is added by the expressionCompatibility.py
		# config file to provide compatibility for loading old
		# files, so we must hide it.
		"engine" : (

			"plugValueWidget:type", "",
			"nodule:type", "",

		),

		# This plug is added by the expressionCompatibility.py
		# config file to provide compatibility for loading old
		# files, so we must hide it.
		"expression" : (

			"plugValueWidget:type", "",
			"nodule:type", "",

		),

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

	with Gaffer.UndoContext( node.scriptNode() ) :

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

__popupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __popupMenu )

# _ExpressionPlugValueWidget
##########################################################################

class _ExpressionWidget( GafferUI.Widget ) :

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

			self.__activatedConnection = self.__textWidget.activatedSignal().connect( Gaffer.WeakMethod( self.__activated ) )
			self.__editingFinishedConnection = self.__textWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__editingFinished ) )
			self.__dropTextConnection = self.__textWidget.dropTextSignal().connect( Gaffer.WeakMethod( self.__dropText ) )

			self.__messageWidget = GafferUI.MessageWidget()

		self.__expressionChangedConnection = self.__node.expressionChangedSignal().connect( Gaffer.WeakMethod( self.__expressionChanged ) )
		self.__errorConnection = self.__node.errorSignal().connect( Gaffer.WeakMethod( self.__error ) )

		self.__update()

	def __update( self ) :

		expression = self.__node.getExpression()

		self.__textWidget.setText( expression[0] )
		self.__languageMenu.setText( IECore.CamelCase.toSpaced( expression[1] ) )

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
		with Gaffer.UndoContext( self.__node.scriptNode() ) :
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

		self.__messageWidget.setVisible( True )
		self.__messageWidget.messageHandler().handle( IECore.Msg.Level.Error, "Execution error", error )
