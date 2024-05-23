##########################################################################
#
#  Copyright (c) 2020, John Haddon. All rights reserved.
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

import os
import re
import enum
import functools
import token
import keyword
import tokenize
import collections
import io

import imath

import IECore

import Gaffer
import GafferUI

from Qt import QtGui

class CodeWidget( GafferUI.MultiLineTextWidget ) :

	def __init__( self, text="", editable=True, fixedLineHeight=None, **kw ) :

		GafferUI.MultiLineTextWidget.__init__( self, text, editable, fixedLineHeight = fixedLineHeight, wrapMode = self.WrapMode.None_, role = self.Role.Code, **kw )

		self.__completer = None
		self.__completionMenu = None
		self.__highlighter = _QtHighlighter( self._qtWidget().document() )
		self.__commentPrefix = None

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )
		self.__textChangedConnection = self.textChangedSignal().connect( Gaffer.WeakMethod( self.__textChanged ), scoped = False )

	def setCompleter( self, completer ) :

		self.__completer = completer

	def getCompleter( self ) :

		return self.__completer

	def setHighlighter( self, highlighter ) :

		# Changing the highlighting counts as changing the text as far as Qt is
		# concerned, so `textChangedSignal()` will be emitted. Block the connection
		# so that we don't pop up the completion menu inappropriately.
		with Gaffer.Signals.BlockedConnection( self.__textChangedConnection ) :
			self.__highlighter.setHighlighter( highlighter )

	def getHighlighter( self ) :

		return self.__highlighter.getHighlighter()

	def setCommentPrefix( self, commentPrefix ) :

		self.__commentPrefix = commentPrefix

	def getCommentPrefix( self ) :

		return self.__commentPrefix

	def _emitEditingFinished( self ) :

		# MultiLineTextWidget considers editing to have finished as soon as
		# we lose focus. That doesn't make sense when we lost focus due to
		# popping up the completion menu, because we did that to assist the user
		# in editing. So we only emit the signal if the menu isn't visible.
		# We get back focus as soon as the menu closes, so will get another
		# opportunity to emit the signal before the user navigates elsewhere.
		if self.__completionMenu is None or not self.__completionMenu.visible() :
			GafferUI.MultiLineTextWidget._emitEditingFinished( self )

	def __keyPress( self, widget, event ) :

		if event.key == "Tab" :
			if self._qtWidget().textCursor().hasSelection() :
				if event.modifiers == event.Modifiers.None_ :
					return self.__indentPress( 1 )
				elif event.modifiers == event.Modifiers.Shift :
					return self.__indentPress( -1 )
			elif event.modifiers == event.Modifiers.None_ :
				return self.__completionPress()
		elif event.key == "Backtab" :
			return self.__indentPress( -1 )
		elif event.modifiers == event.Modifiers.Control and event.key == "BracketLeft" :
			return self.__indentPress( -1 )
		elif event.modifiers == event.Modifiers.Control and event.key == "BracketRight" :
			return self.__indentPress( 1 )
		elif event.modifiers == event.Modifiers.Control and event.key == "Slash" :
			return self.__commentPress()
		elif event.key == "Return" and event.modifiers == event.Modifiers.None_ :
			return self.__returnPress()
		elif event.modifiers == event.Modifiers.Control and event.key == "L" :
			return self.__extendSelectionPress()

		return False

	def __completionsAndLine( self ) :

		if self.__completer is None :
			return [], ""

		text = self.getText()
		cursor = self.getCursorPosition()
		previousNewline = text.rfind( "\n", 0, cursor )
		line = text[previousNewline+1:cursor]

		return self.__completer.completions( line ), line

	def __completionPress( self ) :

		completions, line = self.__completionsAndLine()
		if not completions :
			return False

		commonPrefix = os.path.commonprefix( [ c.text for c in completions ] )
		if len( commonPrefix ) > len( line ) :
			self.insertText( commonPrefix[len(line):] )

		return bool( completions )

	def __selectedBlocks( self ) :

		cursor = self._qtWidget().textCursor()
		startBlock = self._qtWidget().document().findBlock( cursor.selectionStart() )
		endBlock = self._qtWidget().document().findBlock( cursor.selectionEnd() )

		result = []
		while True :
			result.append( startBlock )
			if startBlock == endBlock :
				break
			else :
				startBlock = startBlock.next()

		if len( result ) > 1 and result[-1].position() == cursor.selectionEnd() :
			# Omit last block if cursor is at the start of the line.
			del result[-1]

		return result

	def __indentPress( self, indent ) :

		cursor = self._qtWidget().textCursor()
		try :

			cursor.beginEditBlock()

			for block in self.__selectedBlocks() :

				cursor = QtGui.QTextCursor( block )
				if indent > 0 :
					cursor.insertText( "\t" * indent )
				else :
					for i in range( 0, len( os.path.commonprefix( [ block.text(), "\t" * -indent ] ) ) ) :
						cursor.deleteChar()

		finally :

			cursor.endEditBlock()

		return True

	def __commentPress( self ) :

		if not self.__commentPrefix :
			return False

		# Capture groups :
		#
		# 1) optional indent
		# 2) optional comment prefix with optional trailing space
		regex = re.compile( r"^(\t*)({commentPrefix} ?)?".format( commentPrefix = self.__commentPrefix ) )

		blocks = self.__selectedBlocks()
		matches = [ regex.match( block.text() ) for block in blocks ]

		cursor = self._qtWidget().textCursor()
		try :

			cursor.beginEditBlock()

			if all( m.group( 2 ) is not None for m in matches ) :

				# Every block has a comment prefix. Remove them.
				for block, match in zip( blocks, matches ) :
					cursor = QtGui.QTextCursor( block )
					cursor.movePosition( cursor.Right, n = len( match.group( 1 ) ) )
					for i in range( 0, len( match.group( 2 ) ) ) :
						cursor.deleteChar()

			else :

				# Not every block is commented. Add comment prefix
				# to all.
				indent = len( os.path.commonprefix( [ m.group( 1 ) for m in matches ] ) )
				for block in blocks :
					cursor = QtGui.QTextCursor( block )
					cursor.movePosition( cursor.Right, n = indent )
					cursor.insertText( self.__commentPrefix + " " )

		finally :

			cursor.endEditBlock()

		return True

	def __returnPress( self ) :

		# Maintain indentation when adding newline

		cursor = self._qtWidget().textCursor()
		line = cursor.block().text()
		indent = line[:len(line)-len(line.lstrip())]

		try :
			cursor.beginEditBlock()
			cursor.insertText( "\n" + indent )
			self._qtWidget().ensureCursorVisible()
		finally :
			cursor.endEditBlock()

		return True

	def __extendSelectionPress( self ) :

		cursor = self._qtWidget().textCursor()

		if cursor.hasSelection() :
			# Extend an existing selection to contain the beginning of the
			# first selected line through to the end of the last selected line.
			selectionEnd = cursor.selectionEnd()
			cursor.setPosition( cursor.selectionStart(), cursor.MoveAnchor )
			cursor.movePosition( cursor.StartOfLine, cursor.MoveAnchor )
			cursor.setPosition( selectionEnd, cursor.KeepAnchor )
			cursor.movePosition( cursor.EndOfLine, cursor.KeepAnchor )
		else :
			# Select the entire line where the cursor is currently positioned.
			cursor.movePosition( cursor.StartOfLine, cursor.MoveAnchor )
			cursor.movePosition( cursor.EndOfLine, cursor.KeepAnchor )

		if not cursor.atEnd() :
			# Move the cursor to the start of the next line to allow
			# repeated presses to extend the selection to subsequent lines.
			cursor.movePosition( cursor.Down, cursor.KeepAnchor )
			cursor.movePosition( cursor.StartOfLine, cursor.KeepAnchor )

		self._qtWidget().setTextCursor( cursor )

		return True

	def __textChanged( self, widget ) :

		if self.__completionMenu is not None :
			# Dispose of current menu safely. We can be called from the keypress
			# forwarding code of the menu, so we can't destroy it immediately.
			GafferUI.WidgetAlgo.keepUntilIdle( self.__completionMenu )
			self.__completionMenu = None

		completions, line = self.__completionsAndLine()
		if not completions :
			return

		prefix = "/"
		menuDefinition = IECore.MenuDefinition()
		for i, c in enumerate( completions ) :
			menuDefinition.append(
				"{}{}".format( prefix, i ),
				{
					"label" : c.label,
					"command" : functools.partial(
						Gaffer.WeakMethod( self.insertText ), c.text[len(line):]
					)
				}
			)
			if i == 5 :
				menuDefinition.append( "/Divider", { "divider" : True } )
				prefix = "/More/"

		self.__completionMenu = GafferUI.Menu( menuDefinition )
		self.__completionMenu.popup(
			parent = self.ancestor( GafferUI.Window ),
			position = self.cursorBound().max(),
		)
		# We can only get `Close` mode via the `grabFocus` argument to `popup`,
		# but we want `Forward` mode because it removes unwanted flicker when
		# replacing the old menu with the new one.
		## \todo Expose KeyboardMode publicly in `popup()`?
		self.__completionMenu._qtWidget().keyboardMode = self.__completionMenu._qtWidget().KeyboardMode.Forward

# Highlighter classes
# ===================

class Highlighter( object ) :

	Type = enum.IntEnum(
		"Type",
		[
			"SingleQuotedString", "DoubleQuotedString", "Number",
			"Keyword", "ControlFlow", "Braces", "Operator", "Call",
			"Comment", "ReservedWord", "Preprocessor"
		]
	)

	# Specifies a highlight type to be used for the characters
	# between `start` and `end`. End may be `None` to signal that
	# the last highlight on the line continues to the next line.
	Highlight = collections.namedtuple( "Highlight", [ "start", "end", "type" ] )

	# Must be implemented to return a list of Highlight
	# objects for the text in `line`. If the last highlight
	# on the previous line had `end == None`, its type is passed
	# as `previousHighlightType`, allowing the highlighting to be
	# continued on this line.
	def highlights( self, line, previousHighlightType ) :

		raise NotImplementedError

class PythonHighlighter( Highlighter ) :

	__controlFlowKeywords = {
		"if", "elif", "else",
		"try", "except", "finally",
		"for", "while",
		"from", "import",
		"return",
	}

	__braces = {
		"(", ")", "[", "]", "{", "}",
	}

	__operators = {
		"=", "==", "!=",
		"+", "+=", "-", "-=", "*", "*=", "/", "/=", "//", "//=", "%", "%=",
		"|", "|=", "&", "&=", "^", "^=", "~",
		">", ">=", "<", "<=", "**", "<<", ">>",
	}

	def highlights( self, line, previousHighlightType ) :

		if previousHighlightType in ( self.Type.SingleQuotedString, self.Type.DoubleQuotedString ) :
			# Continuation of multi-line string
			openingQuote = '"""' if previousHighlightType == self.Type.DoubleQuotedString else "'''"
			highlights = self.highlights( openingQuote + line, None )
			return [
				self.Highlight( max( 0, h.start - 3 ), h.end - 3 if h.end is not None else None, h.type )
				for h in highlights
			]

		result = []

		pendingName = None
		try :
			for tokenType, string, start, end, _  in tokenize.generate_tokens( io.StringIO( line ).readline ) :
				highlightType = None
				if tokenType == token.NAME :
					if string in self.__controlFlowKeywords :
						highlightType = self.Type.ControlFlow
					elif keyword.iskeyword( string ) or string == "self" :
						highlightType = self.Type.Keyword
					else :
						pendingName = self.Highlight( start[1], end[1], self.Type.Call )
						continue
				elif tokenType == token.OP :
					if string in self.__braces :
						highlightType = self.Type.Braces
						if string == "(" :
							if pendingName is not None :
								result.append( pendingName )
					elif string in self.__operators :
						highlightType = self.Type.Operator
				elif tokenType == token.STRING :
					highlightType = self.__stringType( string[-1] )
				elif tokenType == tokenize.COMMENT :
					highlightType = self.Type.Comment
				elif tokenType == token.NUMBER :
					highlightType = self.Type.Number

				if highlightType is not None  :
					result.append( self.Highlight( start[1], end[1], highlightType ) )

				pendingName = None
		except tokenize.TokenError as e :
			if e.args[0] == "EOF in multi-line string" :
				result.append( self.Highlight( e.args[1][1], None, self.__stringType( line[e.args[1][1]] ) ) )

		return result

	def __stringType( self, quote ) :

		return {
			"'" : self.Type.SingleQuotedString,
			'"' : self.Type.DoubleQuotedString
		}[quote]

CodeWidget.Highlighter = Highlighter
CodeWidget.PythonHighlighter = PythonHighlighter

# QSyntaxHighlighter used to adapt our Highlighter class
# for use with a QTextDocument.
class _QtHighlighter( QtGui.QSyntaxHighlighter ) :

	def __init__( self, document ) :

		QtGui.QSyntaxHighlighter.__init__( self, document )

		self.__highlighter = None

		def format( color ) :

			f = QtGui.QTextCharFormat()
			f.setForeground( color )
			return f

		self.__formats = {
			Highlighter.Type.SingleQuotedString : format( QtGui.QColor( 216, 146, 115 ) ),
			Highlighter.Type.DoubleQuotedString : format( QtGui.QColor( 216, 146, 115 ) ),
			Highlighter.Type.Number : format( QtGui.QColor( 174, 208, 164 ) ),
			Highlighter.Type.Keyword : format( QtGui.QColor( 64, 156, 219 ) ),
			Highlighter.Type.ControlFlow : format( QtGui.QColor( 207, 128, 195 ) ),
			Highlighter.Type.Braces : format( QtGui.QColor( 255, 215, 0 ) ),
			Highlighter.Type.Operator : format( QtGui.QColor( 155, 218, 252 ) ),
			Highlighter.Type.Call : format( QtGui.QColor( 220, 221, 189 ) ),
			Highlighter.Type.Comment : format( QtGui.QColor( 125, 154, 104 ) ),
			Highlighter.Type.ReservedWord : format( QtGui.QColor( 200, 0, 0 ) ),
			Highlighter.Type.Preprocessor : format( QtGui.QColor( 207, 128, 195 ) ),
		}

	# Our methods
	# ===========

	def setHighlighter( self, highlighter ) :

		self.__highlighter = highlighter
		self.rehighlight()

	def getHighlighter( self ) :

		return self.__highlighter

	# Qt methods
	# ==========

	def highlightBlock( self, text ) :

		self.setCurrentBlockState( -1 )
		if self.__highlighter is None :
			return

		previousType = None
		if self.previousBlockState() != -1 :
			previousType = Highlighter.Type( self.previousBlockState() )

		highlights = self.__highlighter.highlights( text, previousType )

		for h in highlights :
			end = h.end
			if end is None :
				self.setCurrentBlockState( int( h.type ) )
				end = len( text )
			f = self.__formats[h.type]
			if f is not None :
				self.setFormat( h.start, end - h.start, f )

# Completer classes
# ===================

class Completer( object ) :

	## Specifies completed text and a label suitable
	# for referring to it
	Completion = collections.namedtuple( "Completion", [ "text", "label" ] )

	## Must be implemented to return a list of possible
	# completions for the specified text.
	def completions( self, text ) :

		raise NotImplementedError

class PythonCompleter( Completer ) :

	__searchPrefix = r"(?:^|(?<=[\s,(]))"

	def __init__( self, namespace, includeGraphComponentAttributes = True ) :

		self.__namespace = namespace
		self.__includeGraphComponentAttributes = includeGraphComponentAttributes

	def completions( self, text ) :

		return sorted( set(
			self.__attrAndItemCompletions( text ) +
			self.__globalCompletions( text )
		) )

	def __globalCompletions( self, text ) :

		globalVariable = r"{searchPrefix}([a-zA-Z0-9]+)$".format( searchPrefix = self.__searchPrefix )

		match = re.search( globalVariable, text )
		if not match :
			return []

		word = match.group( 0 )

		namespace = __builtins__.copy()
		namespace.update( self.__namespace )

		return self.__completions( namespace.items(), text[:-len(word)], word )

	def __attrAndItemCompletions( self, text ) :

		word = r"[a-zA-Z0-9_]+"
		optionalWord = r"[a-zA-Z0-9_]*"
		getAttr = r"\.{word}".format( word = word )
		partialGetAttr = r"\.{optionalWord}".format( optionalWord = optionalWord )
		quotedWord = r"""(?:'{word}'|"{word}")""".format( word = word )
		getItem = r"\[{quotedWord}\]".format( quotedWord = quotedWord )
		partialGetItem = r"\[(?:['\"]{optionalWord})?".format( optionalWord = optionalWord )
		path = r"{searchPrefix}({word}(?:{getAttr}|{getItem})*)({partialGetAttr}|{partialGetItem})$".format(
			searchPrefix = self.__searchPrefix, word = word, getAttr = getAttr, getItem = getItem,
			partialGetAttr = partialGetAttr, partialGetItem = partialGetItem
		)

		pathMatch = re.search( path, text )
		if not pathMatch :
			return []

		objectPath, partial = pathMatch.group( 1, 2 )
		try :
			rootObject = eval( objectPath, self.__namespace )
		except :
			return []

		prefix = text[:-len(partial)]

		if partial.startswith( "." ) :
			# Attribute
			if isinstance( rootObject, Gaffer.GraphComponent ) and not self.__includeGraphComponentAttributes :
				return []
			items = []
			for n in dir( rootObject ) :
				with IECore.IgnoredExceptions( AttributeError ) :
					items.append( ( n, getattr( rootObject, n ) ) )
			return self.__completions(
				items = items,
				prefix = prefix, partialName = partial[1:],
				namePrefix = "."
			)
		else :
			# Item
			try :
				items = rootObject.items()
			except :
				return []
			quote = partial[1] if len( partial ) > 1 else '"'
			return self.__completions(
				items = items,
				prefix = prefix,
				partialName = partial[2:],
				namePrefix = "[" + quote,
				nameSuffix = quote + "]"
			)

	def __completions( self, items, prefix, partialName, namePrefix = "", nameSuffix = "" ) :

		result = []
		for name, value in items :
			if not isinstance( name, str ):
				# This could be called when trying to index a dict with non string keys,
				# and we don't want an exception when we try to call startswith
				continue
			if name.startswith( "_" ) and not partialName :
				# We only provide completions for protected and private
				# names if they have been explicitly started by the user.
				continue
			if name.startswith( partialName ) and ( name != partialName or nameSuffix ) :
				if hasattr( value, "__call__" ) :
					result.append(
						self.Completion(
							prefix + namePrefix + name + nameSuffix + "(",
							namePrefix + name + nameSuffix + "()"
						)
					)
				else :
					result.append(
						self.Completion(
							prefix + namePrefix + name + nameSuffix,
							namePrefix + name + nameSuffix
						)
					)

		return sorted( result )

CodeWidget.Completer = Completer
CodeWidget.PythonCompleter = PythonCompleter
