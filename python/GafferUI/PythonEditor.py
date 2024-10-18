##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

import ast
import contextlib
import functools
import sys
import traceback
import weakref
import imath

import IECore

import Gaffer
import GafferUI

from Qt import QtWidgets
from Qt import QtCore

## \todo Custom right click menu with script load, save, execute file, undo, redo etc.
## \todo Standard way for users to customise all menus
class PythonEditor( GafferUI.Editor ) :

	def __init__( self, scriptNode, **kw ) :

		self.__splittable = GafferUI.SplitContainer( borderWidth = 2 )

		GafferUI.Editor.__init__( self, self.__splittable, scriptNode, **kw )

		self.__outputWidget = GafferUI.MultiLineTextWidget(
			editable = False,
			wrapMode = GafferUI.MultiLineTextWidget.WrapMode.None_,
			role = GafferUI.MultiLineTextWidget.Role.Code,
		)
		self.__outputWidget._qtWidget().setObjectName( "gafferPythonEditorOutputWidget" )
		self.__outputWidget.contextMenuSignal().connect(
			Gaffer.WeakMethod( self.__contextMenu )
		)

		self.__inputWidget = GafferUI.CodeWidget( lineNumbersVisible = True )

		self.__splittable.append( self.__outputWidget )
		self.__splittable.append( self.__inputWidget )

		self.__inputWidget.activatedSignal().connect( Gaffer.WeakMethod( self.__activated ) )
		self.__inputWidget.dropTextSignal().connect( Gaffer.WeakMethod( self.__dropText ) )
		self.__inputWidget.contextMenuSignal().connect(
			Gaffer.WeakMethod( self.__contextMenu )
		)
		GafferUI.WidgetAlgo.joinEdges(
			[ self.__outputWidget, self.__inputWidget ],
			orientation = GafferUI.ListContainer.Orientation.Vertical
		)

		self.__executionDict = {
			"imath" : imath,
			"IECore" : IECore,
			"Gaffer" : Gaffer,
			"GafferUI" : GafferUI,
			"root" : scriptNode,
		}
		self.__inputWidget.setCompleter( GafferUI.CodeWidget.PythonCompleter( self.__executionDict ) )
		self.__inputWidget.setHighlighter( GafferUI.CodeWidget.PythonHighlighter() )
		self.__inputWidget.setCommentPrefix( "#" )

	def inputWidget( self ) :

		return self.__inputWidget

	def outputWidget( self ) :

		return self.__outputWidget

	def execute( self ) :

		# decide what to execute
		haveSelection = True
		toExecute = self.__inputWidget.selectedText()
		if not toExecute :
			haveSelection = False
			toExecute = self.__inputWidget.getText()

		# parse it first. this lets us give better error formatting
		# for syntax errors, and also figure out whether we can eval()
		# and display the result or must exec() only.
		try :
			parsed = ast.parse( toExecute )
		except SyntaxError as e :
			self.__outputWidget.appendHTML( self.__syntaxErrorToHTML( e ) )
			return

		# execute it

		self.__outputWidget.appendHTML( self.__codeToHTML( toExecute ) )

		with self.__outputRedirection() :
			with _MessageHandler( self.__outputWidget ) :
				with Gaffer.UndoScope( self.scriptNode() ) :
					with self.context() :
						try :
							if len( parsed.body ) == 1 and isinstance( parsed.body[0], ast.Expr ) :
								result = eval( toExecute, self.__executionDict, self.__executionDict )
								if result is not None :
									self.__outputWidget.appendText( str( result ) )
							else :
								exec( toExecute, self.__executionDict, self.__executionDict )
							if not haveSelection :
								self.__inputWidget.setText( "" )
						except Exception as e :
							self.__outputWidget.appendHTML( self.__exceptionToHTML() )

	## The Python dictionary that provides the globals and locals for `execute()`.
	def namespace( self ) :

		return self.__executionDict

	def __repr__( self ) :

		return "GafferUI.PythonEditor( scriptNode )"

	def __activated( self, widget ) :

		self.execute()
		return True

	def __dropText( self, widget, dragData ) :

		if isinstance( dragData, IECore.StringVectorData ) :
			return repr( list( dragData ) )
		elif isinstance( dragData, Gaffer.GraphComponent ) :
			if self.scriptNode().isAncestorOf( dragData ) :
				return "root['" + dragData.relativeName( self.scriptNode() ).replace( ".", "']['" ) + "']"
		elif isinstance( dragData, Gaffer.Set ) :
			if len( dragData ) == 1 :
				return self.__dropText( widget, dragData[0] )
			else :
				return "[ " + ", ".join( [ self.__dropText( widget, d ) for d in dragData ] ) + " ]"
		elif isinstance( dragData, IECore.CompoundData ) :
			return repr( dragData )
		elif isinstance( dragData, IECore.Data ) and hasattr( dragData, "value" ) :
			return repr( dragData.value )

		return None

	def __codeToHTML( self, code ) :

		code = code.replace( "<", "&lt;" ).replace( ">", "&gt;" )
		return "<pre>" + code + "</pre>"

	def __syntaxErrorToHTML( self, syntaxError ) :

		formatted = traceback.format_exception_only( SyntaxError, syntaxError )
		lineNumber = formatted[0].rpartition( "," )[2].strip()
		headingText = formatted[-1].replace( ":", " : " + lineNumber + " : ", 1 )
		result = "<h1 class='ERROR'>%s</h1>" % headingText
		result += "<br>" + self.__codeToHTML( "".join( formatted[1:-1] ) )

		return result

	def __exceptionToHTML( self ) :

		t = traceback.extract_tb( sys.exc_info()[2] )
		lineNumber = str( t[1][1] )
		headingText = traceback.format_exception_only( *(sys.exc_info()[:2]) )[0].replace( ":", " : line " + lineNumber + " : ", 1 )
		result = "<h1 class='ERROR'>%s</h1>" % headingText
		if len( t ) > 2 :
			result += "<br>" + self.__codeToHTML( "".join( traceback.format_list( t[2:] ) ) )

		return result

	# Context manager used to redirect `sys.stdout` and `sys.stderr` into our
	# output widget during execution. This is a little bit of a faff for several
	# reasons :
	#
	# 1. `__outputWidget.appendText()` automatically appends the text on a new
	#    line.
	# 2. A simple call to `print( 1, 2 )` makes four separate calls to
	#    `stdout.write()`, with values of "1" "2", " " and "\n".
	# 3. We don't want to simply buffer up all the writes and print them after
	#    execution. Instead we want to update the UI for each new `print()` so
	#    that users can get feedback on the progress of their script.
	#
	# So we maintain a buffer that we flush to `appendText()` every time we
	# encounter a newline.
	@contextlib.contextmanager
	def __outputRedirection( self ) :

		buffer = ""
		def __redirect( output ) :

			nonlocal buffer
			buffer += output
			if buffer.endswith( "\n" ) :
				self.__outputWidget.appendText( buffer[:-1] )
				buffer = ""
				# Update the GUI so messages are output as they occur, rather
				# than all getting queued up till the end.
				QtWidgets.QApplication.instance().processEvents( QtCore.QEventLoop.ExcludeUserInputEvents )

		with Gaffer.OutputRedirection( stdOut = __redirect, stdErr = __redirect ) :
			yield

		if buffer :
			self.__outputWidget.appendText( buffer )

	def __contextMenu( self, widget ) :

		definition = IECore.MenuDefinition()

		if widget is self.inputWidget() :

			definition.append(
				"/Execute Selection" if widget.selectedText() else "/Execute",
				{
					"command" : self.execute,
					"shortCut" : "Enter",
				}
			)

			definition.append( "/ExecuteDivider", { "divider" : True } )

		definition.append(
			"/Copy",
			{
				"command" : functools.partial(
					self.scriptNode().ancestor( Gaffer.ApplicationRoot ).setClipboardContents,
					IECore.StringData( widget.selectedText() )
				),
				"active" : bool( widget.selectedText() )
			}
		)

		if widget is self.inputWidget() :
			definition.append(
				"/Paste",
				{
					"command" : functools.partial(
						widget.insertText,
						self.scriptNode().ancestor( Gaffer.ApplicationRoot ).getClipboardContents().value,
					),
					"active" : isinstance( self.scriptNode().ancestor( Gaffer.ApplicationRoot ).getClipboardContents(), IECore.StringData )
				}
			)

		definition.append( "/CopyPasteDivider", { "divider" : True } )

		definition.append(
			"/Select All",
			{
				"command" : widget._qtWidget().selectAll,
				"active" :  bool( widget.getText() )
			}
		)

		definition.append( "/SelectDivider", { "divider" : True } )

		definition.append(
			"/Clear",
			{
				"command" : functools.partial( widget.setText, "" ),
				"active" : bool( widget.getText() )
			}
		)

		self.__popupMenu = GafferUI.Menu( definition )
		self.__popupMenu.popup( parent = self )

		return True

GafferUI.Editor.registerType( "PythonEditor", PythonEditor )

class _MessageHandler( IECore.MessageHandler ) :

	def __init__( self, textWidget ) :

		IECore.MessageHandler.__init__( self )

		self.__textWidget = weakref.ref( textWidget )

	def handle( self, level, context, message ) :

		widget = self.__textWidget()
		if widget is None :
			return

		html = formatted = "<h1 class='%s'>%s : %s </h1><pre class='message'>%s</pre><br>" % (
			IECore.Msg.levelAsString( level ),
			IECore.Msg.levelAsString( level ),
			context,
			message
		)
		widget.appendHTML( html )
		# update the gui so messages are output as they occur, rather than all getting queued
		# up till the end.
		QtWidgets.QApplication.instance().processEvents( QtCore.QEventLoop.ExcludeUserInputEvents )
