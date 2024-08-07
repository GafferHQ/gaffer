##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui

class NameWidget( GafferUI.TextWidget ) :

	def __init__( self, graphComponent, **kw ) :

		GafferUI.TextWidget.__init__( self, **kw )

		self._qtWidget().setValidator( _Validator( self._qtWidget() ) )

		self.__graphComponent = False # Sentinel that forces `setGraphComponent()` to update
		self.setGraphComponent( graphComponent )

		self.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__setName ), scoped = False )

	def setGraphComponent( self, graphComponent ) :

		if self.__graphComponent == graphComponent :
			return

		self.__graphComponent = graphComponent
		self.__nameChangedConnection = None
		self.__nodeMetadataChangedConnection = None
		self.__plugMetadataChangedConnection = None

		if self.__graphComponent is not None :
			self.__nameChangedConnection = self.__graphComponent.nameChangedSignal().connect(
				Gaffer.WeakMethod( self.__setText ), scoped = True
			)
			if isinstance( self.__graphComponent, ( Gaffer.Node, Gaffer.Plug ) ) :
				self.__nodeMetadataChangedConnection = Gaffer.Metadata.nodeValueChangedSignal().connect(
					Gaffer.WeakMethod( self.__nodeMetadataChanged ), scoped = True
				)

			if isinstance( self.__graphComponent, Gaffer.Plug ) :
				self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal( self.__graphComponent.node() ).connect(
					Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = True
				)

		self.__setText()
		self.__updateEditability()

	def getGraphComponent( self ) :

		return self.__graphComponent

	def __setName( self, *unwantedArgs ) :

		if self.__graphComponent is None :
			return

		with Gaffer.UndoScope( self.__graphComponent.ancestor( Gaffer.ScriptNode ) ) :
			self.setText( self.__graphComponent.setName( self.getText() ) )

	def __setText( self, *unwantedArgs ) :

		self.setText( self.__graphComponent.getName() if self.__graphComponent is not None else "" )

	def __updateEditability( self ) :

		editable = False
		if self.__graphComponent is not None :
			editable = not Gaffer.MetadataAlgo.readOnly( self.__graphComponent ) and Gaffer.Metadata.value( self.__graphComponent, "renameable" )

		self.setEditable( editable )

	def __nodeMetadataChanged( self, nodeTypeId, key, node ) :

		if (
			Gaffer.MetadataAlgo.readOnlyAffectedByChange( self.__graphComponent, nodeTypeId, key, node ) or
			node == self.__graphComponent and key == "renameable"
		) :
			self.__updateEditability()

	def __plugMetadataChanged( self, plug, key, reason ) :

		if (
			Gaffer.MetadataAlgo.readOnlyAffectedByChange( self.__graphComponent, plug, key ) or
			plug == self.__graphComponent and key == "renameable"
		) :
			self.__updateEditability()

class _Validator( QtGui.QValidator ) :

	def __init__( self, parent ) :

		QtGui.QValidator.__init__( self, parent )

	def validate( self, input, pos ) :

		input = input.replace( " ", "_" )
		if len( input ) :
			if re.match( "^(?!__)[A-Za-z_]+[A-Za-z_0-9]*$", input ) :
				result = QtGui.QValidator.Acceptable
			else :
				result = QtGui.QValidator.Invalid
		else :
			result = QtGui.QValidator.Intermediate

		if hasattr( QtCore, "QString" ) and isinstance( input, QtCore.QString ) :
			# PyQt API, where QString type is exposed and we modify it in place
			return result, pos
		else :
			# PySide API, where QString is mapped automatically to python string
			# and we return a new string.
			return result, input, pos
