##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import re

import IECore

import Gaffer
import GafferUI
import GafferScene

from GafferUI.PlugValueWidget import sole

class SetExpressionPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__codeWidget = GafferUI.CodeWidget()

		GafferUI.PlugValueWidget.__init__( self, self.__codeWidget, plug, **kw )

		self._addPopupMenu( self.__codeWidget )

		self.__codeWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__setPlugValues ) )

		self.__availableSets = {}
		self.__sourceSubstitionAvailable = False

	def textWidget( self ) :

		return self.__codeWidget

	def setPlugs( self, plugs ) :

		GafferUI.PlugValueWidget.setPlugs( self, plugs )
		self.__updateHighlighterAndCompleter()

	def _auxiliaryPlugs( self, plug ) :

		# We have two types of auxiliary plug :
		#
		# - `ScenePlug.setNames` for determining what sets are available.
		# - `TweakPlug.modePlug` for determining if the `{source}` substitution is available.

		node = plug.node()
		if isinstance( node, GafferScene.Filter ) :
			nodes = GafferScene.SceneAlgo.filteredNodes( node )
		else :
			nodes = { node }

		result = []
		for node in nodes :
			firstInputScene = next( GafferScene.ScenePlug.RecursiveInputRange( node ), None )
			if firstInputScene is not None :
				result.append( firstInputScene["setNames"] )

		if isinstance( plug.parent(), Gaffer.TweakPlug ) :
			result.append( plug.parent()["mode"] )

		return result

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		result = []

		for plug, auxPlugs in zip( plugs, auxiliaryPlugs ) :

			availableSets = set()
			sourceSubstitionAvailable = False
			for auxPlug in auxPlugs :
				if isinstance( auxPlug.parent(), GafferScene.ScenePlug ) :
					# `ScenePlug.setNames`
					availableSets.update( str( x ) for x in auxPlug.getValue() )
				else :
					# `TweakPlug.mode`
					if auxPlug.getValue() == Gaffer.TweakPlug.Mode.Replace :
						sourceSubstitionAvailable = True

			result.append( {
				"value" : plug.getValue(),
				"availableSets" : availableSets,
				"sourceSubstitionAvailable" : sourceSubstitionAvailable,
			} )

		return result

	def _updateFromValues( self, values, exception ) :

		if self.getPlugs() and not values and exception is None :
			# Background compute starting. If this is only for our
			# auxiliary plugs, then avoid unnecessary flicker in
			# the text itself.
			if not any( Gaffer.PlugAlgo.dependsOnCompute( p ) for p in self.getPlugs() ) :
				return

		self.__codeWidget.setErrored( exception is not None )
		value = sole( v["value"] for v in values )
		self.__codeWidget.setText( value or "" )
		self.__codeWidget.setPlaceholderText( "---" if value is None else "" )

		updateHighlightAndCompleter = False

		availableSets = set().union( *( v["availableSets"] for v in values ) )
		if availableSets != self.__availableSets :
			self.__availableSets = availableSets
			updateHighlightAndCompleter = True

		sourceSubstitionAvailable = values and all( v["sourceSubstitionAvailable"] for v in values )
		if sourceSubstitionAvailable != self.__sourceSubstitionAvailable :
			self.__sourceSubstitionAvailable = sourceSubstitionAvailable
			updateHighlightAndCompleter = True

		if updateHighlightAndCompleter :
			self.__updateHighlighterAndCompleter()

	def _updateFromEditable( self ) :

		self.__codeWidget.setEditable( self._editable() )

	def __setPlugValues( self, *unused ) :

		if not self._editable() :
			return

		text = self.__codeWidget.getText()
		with Gaffer.UndoScope( self.scriptNode() ) :
			for plug in self.getPlugs() :
				plug.setValue( text )

	def __updateHighlighterAndCompleter( self ) :

		self.__codeWidget.setHighlighter( _Highlighter(
			self.__availableSets, self.__sourceSubstitionAvailable
		) )

		tokens = list( self.__availableSets ) + [ "in", "containing" ]
		if self.__sourceSubstitionAvailable :
			tokens.append( "{source}" )

		self.__codeWidget.setCompleter( _Completer( sorted( tokens ) ) )

class _Highlighter( GafferUI.CodeWidget.Highlighter ) :

	__highlightTypes = {
		"|" : GafferUI.CodeWidget.Highlighter.Type.Operator,
		"&" : GafferUI.CodeWidget.Highlighter.Type.Operator,
		"-" : GafferUI.CodeWidget.Highlighter.Type.Operator,
		"in" : GafferUI.CodeWidget.Highlighter.Type.Operator,
		"containing" : GafferUI.CodeWidget.Highlighter.Type.Operator,
		"(" :  GafferUI.CodeWidget.Highlighter.Type.Braces,
		")" :  GafferUI.CodeWidget.Highlighter.Type.Braces,
	}

	__tokenRe = re.compile( r"([()|&\- \t])" )

	def __init__( self, availableSets, sourceSubstitutionAvailable ) :

		GafferUI.CodeWidget.Highlighter.__init__( self )

		self.__availableSets = availableSets
		self.__sourceSubstitutionAvailable = sourceSubstitutionAvailable

	def highlights( self, line, previousHighlightType ) :

		result = []

		l = 0
		for token in self.__tokenRe.split( line ) :
			highlightType = self.__highlightTypes.get( token )
			if highlightType is None :
				if token == "{source}" :
					highlightType = GafferUI.CodeWidget.Highlighter.Type.SingleQuotedString if self.__sourceSubstitutionAvailable else GafferUI.CodeWidget.Highlighter.Type.ReservedWord
				elif (
					len( token ) and not token.isspace() and
					token[0] != "/"
				) :
					# Set name. Highlight if it matches an available set, taking into
					# account wildcards.
					if token in self.__availableSets or any( IECore.StringAlgo.match( s, token ) for s in self.__availableSets ) :
						highlightType = GafferUI.CodeWidget.Highlighter.Type.Keyword
				elif len( token ) and token[0] == "/" :
					# Path. These aren't allowed to contain wildcards, so highlight
					# as a reserved word if it does.
					if IECore.StringAlgo.hasWildcards( token ) :
						highlightType = GafferUI.CodeWidget.Highlighter.Type.ReservedWord

			if highlightType is not None :
				result.append(
					self.Highlight( l, l + len( token ), highlightType )
				)
			l += len( token )

		return result

class _Completer( GafferUI.CodeWidget.Completer ) :

	__lastTokenRe = re.compile( r"[^()|&\- \t]+$" )

	def __init__( self, tokens = [] ) :

		GafferUI.CodeWidget.Completer.__init__( self )
		self.__tokens = sorted( tokens )

	def completions( self, text ) :

		lastToken = self.__lastTokenRe.search( text )
		if lastToken is None :
			return []

		return [
			self.Completion( text[:lastToken.start()] + t, t )
			for t in self.__tokens
			if t.startswith( lastToken.group() ) and ( len( t ) > len( lastToken.group() ) )
		]
