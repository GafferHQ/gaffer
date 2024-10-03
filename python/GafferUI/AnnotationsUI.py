##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Cinesite VFX Ltd. nor the names of
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
import re
import imath

import IECore

import Gaffer
import GafferUI

def appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition ) :

	def append( menuPath, name ) :

		menuDefinition.append(
			menuPath,
			{
				"command" : functools.partial( __annotate, node, name ),
				"active" : not Gaffer.MetadataAlgo.readOnly( node ),
			}
		)

	names = Gaffer.MetadataAlgo.annotationTemplates( userOnly = True )
	if not names :
		append( "/Annotate...", "user" )
	else :
		for name in names :
			append(
				"/Annotate/{}...".format( IECore.CamelCase.toSpaced( name ) ),
				name
			)
		menuDefinition.append( "/Annotate/Divider", { "divider" : True } )
		append( "/Annotate/User...", "user" )

def __annotate( node, name, menu ) :

	dialogue = __AnnotationsDialogue( node, name )
	dialogue.wait( parentWindow = menu.ancestor( GafferUI.Window ) )

class _AnnotationsHighlighter( GafferUI.CodeWidget.Highlighter ) :

	__substitutionRe = re.compile( r"(\{[^}]+\})" )

	def __init__( self, node ) :

		GafferUI.CodeWidget.Highlighter.__init__( self )
		self.__node = node

	def highlights( self, line, previousHighlightType ) :

		result = []

		l = 0
		for token in self.__substitutionRe.split( line ) :
			if (
				len( token ) > 2 and
				token[0] == "{" and token[-1] == "}" and
				isinstance( self.__node.descendant( token[1:-1] ), Gaffer.ValuePlug )
			) :
				result.append(
					self.Highlight( l, l + len( token ), self.Type.Keyword )
				)
			l += len( token )

		return result

class _AnnotationsCompleter( GafferUI.CodeWidget.Completer ) :

	__incompleteSubstitutionRe = re.compile( r"\{([^.}][^}]*$)" )

	def __init__( self, node ) :

		GafferUI.CodeWidget.Completer.__init__( self )
		self.__node = node

	def completions( self, text ) :

		m = self.__incompleteSubstitutionRe.search( text )
		if m is None :
			return []

		parentPath, _, childName = m.group( 1 ).rpartition( "." )
		parent = self.__node.descendant( parentPath ) if parentPath else self.__node
		if parent is None :
			return []

		result = []
		for plug in Gaffer.Plug.Range( parent ) :
			if not hasattr( plug, "getValue" ) and not len( plug ) :
				continue
			if plug.getName().startswith( childName ) :
				childPath = plug.relativeName( self.__node )
				result.append(
					self.Completion(
						"{prefix}{{{childPath}{closingBrace}".format(
							prefix = text[:m.start()],
							childPath = childPath,
							closingBrace = "}" if hasattr( plug, "getValue" ) else ""
						),
						label = childPath
					)
				)

		return result

class __AnnotationsDialogue( GafferUI.Dialogue ) :

	def __init__( self, node, name ) :

		GafferUI.Dialogue.__init__( self, "Annotate" )

		self.__node = node
		self.__name = name

		template = Gaffer.MetadataAlgo.getAnnotationTemplate( name )
		annotation = Gaffer.MetadataAlgo.getAnnotation( node, name ) or template

		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 ) as layout :

			self.__textWidget = GafferUI.CodeWidget(
				text = annotation.text() if annotation else "",
				placeholderText = "Tip : Use {plugName} to include plug values",
			)
			self.__textWidget.setHighlighter( _AnnotationsHighlighter( node ) )
			self.__textWidget.setCompleter( _AnnotationsCompleter( node ) )
			self.__textWidget.textChangedSignal().connect(
				Gaffer.WeakMethod( self.__updateButtonStatus )
			)
			self.__textWidget.activatedSignal().connect(
				Gaffer.WeakMethod( self.__textActivated )
			)
			self.__textWidget.contextMenuSignal().connect(
				Gaffer.WeakMethod( self.__textWidgetContextMenu )
			)
			if not template :
				self.__colorChooser = GafferUI.ColorChooser(
					annotation.color() if annotation else imath.Color3f( 0.15, 0.26, 0.26 ),
					displayTransform = GafferUI.Widget.identityDisplayTransform
				)
				self.__colorChooser.colorChangedSignal().connect(
					Gaffer.WeakMethod( self.__updateButtonStatus )
				)
			else :
				self.__colorChooser = None

		self._setWidget( layout )

		self.__cancelButton = self._addButton( "Cancel" )
		self.__removeButton = self._addButton( "Remove" )
		self.__annotateButton = self._addButton( "Annotate" )

		self.__updateButtonStatus()

	def wait( self, **kw ) :

		button = self.waitForButton( **kw )
		if button is self.__cancelButton or button is None :
			return

		with Gaffer.UndoScope( self.__node.scriptNode() ) :
			if button is self.__removeButton :
				Gaffer.MetadataAlgo.removeAnnotation( self.__node, self.__name )
			else :
				Gaffer.MetadataAlgo.addAnnotation(
					self.__node, self.__name,
					self.__makeAnnotation()
				)

	def __updateButtonStatus( self, *unused ) :

		existingAnnotation = Gaffer.MetadataAlgo.getAnnotation( self.__node, self.__name )
		newAnnotation = self.__makeAnnotation()

		self.__cancelButton.setEnabled( newAnnotation != existingAnnotation )
		self.__removeButton.setEnabled( bool( existingAnnotation ) )
		self.__annotateButton.setEnabled( bool( newAnnotation ) and newAnnotation != existingAnnotation )

	def __makeAnnotation( self ) :

		if not self.__textWidget.getText() :
			return Gaffer.MetadataAlgo.Annotation()

		if self.__colorChooser is not None :
			return Gaffer.MetadataAlgo.Annotation(
				self.__textWidget.getText(),
				self.__colorChooser.getColor()
			)
		else :
			return Gaffer.MetadataAlgo.Annotation( self.__textWidget.getText() )

	def __textActivated( self, *unused ) :

		if self.__annotateButton.getEnabled() :
			self.__annotateButton.clickedSignal()( self.__annotateButton )

	def __textWidgetContextMenu( self, *unused ) :

		menuDefinition = IECore.MenuDefinition()

		def menuLabel( name ) :

			if "_" in name :
				name = IECore.CamelCase.fromSpaced( name.replace( "_", " " ) )
			return IECore.CamelCase.toSpaced( name )

		def walkPlugs( graphComponent ) :

			if graphComponent.getName().startswith( "__" ) :
				return

			if isinstance( graphComponent, Gaffer.ValuePlug ) and hasattr( graphComponent, "getValue" ) :
				relativeName = graphComponent.relativeName( self.__node )
				menuDefinition.append(
					"/Insert Plug Value/{}".format( "/".join( menuLabel( n ) for n in relativeName.split( "." ) ) ),
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__textWidget.insertText ), f"{{{relativeName}}}" ),
					}
				)
			else :
				for plug in Gaffer.Plug.InputRange( graphComponent ) :
					walkPlugs( plug )

		walkPlugs( self.__node )

		if not menuDefinition.size() :
			menuDefinition.append( "/Insert Plug Value/No plugs available", { "active" : False } )

		self.__popupMenu = GafferUI.Menu( menuDefinition )
		self.__popupMenu.popup( parent = self )

		return True
