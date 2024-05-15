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

class __AnnotationsDialogue( GafferUI.Dialogue ) :

	def __init__( self, node, name ) :

		GafferUI.Dialogue.__init__( self, "Annotate" )

		self.__node = node
		self.__name = name

		template = Gaffer.MetadataAlgo.getAnnotationTemplate( name )
		annotation = Gaffer.MetadataAlgo.getAnnotation( node, name ) or template

		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 ) as layout :

			self.__textWidget = GafferUI.MultiLineTextWidget(
				text = annotation.text() if annotation else "",
			)
			self.__textWidget.textChangedSignal().connect(
				Gaffer.WeakMethod( self.__updateButtonStatus ), scoped = False
			)
			self.__textWidget.activatedSignal().connect(
				Gaffer.WeakMethod( self.__textActivated ), scoped = False
			)

			if not template :
				self.__colorChooser = GafferUI.ColorChooser(
					annotation.color() if annotation else imath.Color3f( 0.15, 0.26, 0.26 ),
					displayTransform = GafferUI.Widget.identityDisplayTransform
				)
				self.__colorChooser.colorChangedSignal().connect(
					Gaffer.WeakMethod( self.__updateButtonStatus ), scoped = False
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
