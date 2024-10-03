##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import imath

import IECore

import Gaffer
import GafferUI
import GafferCortex
import GafferCortexUI

class OpPathPreview( GafferUI.DeferredPathPreview ) :

	def __init__( self, path ) :

		self.__column = GafferUI.ListContainer( borderWidth = 8 )

		GafferUI.DeferredPathPreview.__init__( self, self.__column, path )

		with self.__column :
			# we'll replace this with the op in _deferredUpdate()
			GafferUI.Spacer( imath.V2i( 1 ) )
			button = GafferUI.Button( "Launch" )
			button.clickedSignal().connect( Gaffer.WeakMethod( self.__executeClicked ) )

		self._updateFromPath()

	def isValid( self ) :

		path = self.getPath()
		if not isinstance( path, GafferCortex.ClassLoaderPath ) :
			return False

		if hasattr( path.classLoader(), "classType" ) :
			if not issubclass( path.classLoader().classType(), IECore.Op ) :
				return False
		else :
			if path.classLoader().searchPath() != IECore.ClassLoader.defaultOpLoader().searchPath() :
				return False

		return path.isLeaf()

	def _load( self ) :

		return self.getPath().load()()

	def _deferredUpdate( self, op ) :

		self.__node = GafferCortex.ParameterisedHolderNode()
		self.__node.setParameterised( op )
		GafferCortexUI.ParameterPresets.autoLoad( self.__node )

		self.__column[0] = GafferUI.NodeUI.create( self.__node )

	def __executeClicked( self, button ) :

		# Create a copy of our op

		self.__node.setParameterisedValues()
		op = self.__node.getParameterised()[0]
		opCopy = self.getPath().load()()
		IECore.ParameterAlgo.copyClasses(
			op.parameters(),
			opCopy.parameters(),
		)
		opCopy.parameters().setValue( op.parameters().getValue().copy() )

		# Launch an OpDialogue, executing the copy in the background

		dialogue = GafferCortexUI.OpDialogue(
			opCopy,
			executeInBackground = True,
			executeImmediately = True
		)
		self.ancestor( GafferUI.Window ).addChildWindow( dialogue )
		dialogue.setVisible( True )

GafferUI.PathPreviewWidget.registerType( "Op", OpPathPreview )
