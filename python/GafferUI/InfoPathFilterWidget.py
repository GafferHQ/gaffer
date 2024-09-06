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

import re
import time
import fnmatch
import functools

import IECore

import Gaffer
import GafferUI

class InfoPathFilterWidget( GafferUI.PathFilterWidget ) :

	def __init__( self, pathFilter, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=2, borderWidth=0 )

		GafferUI.PathFilterWidget.__init__( self, self.__row, pathFilter, **kw )
		with self.__row :

			filterButton = GafferUI.Button( image="collapsibleArrowDown.png", hasFrame=False )
			filterButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )

			self.__filterText = GafferUI.TextWidget()
			self.__filterText.setPlaceholderText( "Filter..." )

			self.__filterText.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__filterEditingFinished ) )
			self.__filterText.textChangedSignal().connect( Gaffer.WeakMethod( self.__filterTextChanged ) )

	def _updateFromPathFilter( self ) :

		# we only do one way synchronisation at present
		pass

	def __filterEditingFinished( self, textWidget ) :

		assert( textWidget is self.__filterText )

		self.__updateFilter()

	def __filterTextChanged( self, textWidget ) :

		assert( textWidget is self.__filterText )

		if self.__filterText.getText()=="" :
			self.__updateFilter()

	def __updateFilter( self, newInfoKey=None ) :

		infoKey, matcher = self.pathFilter().getMatcher()
		if newInfoKey is not None :
			infoKey = newInfoKey

		t = self.__filterText.getText()

		if t=="" :
			matcher = None
		else :
			if "?" not in t and "*" not in t :
				t = "*" + t + "*"
			stringifier = str
			if infoKey == "fileSystem:modificationTime" :
				stringifier = time.ctime

			regex = re.compile( fnmatch.translate( t ) )
			matcher = lambda v : regex.match( stringifier( v ) ) is not None

		self.pathFilter().setMatcher( infoKey, matcher )

	def __buttonClicked( self, button ) :

		## \todo Make this and the stringifier configurable
		infoFields = (
			( "name", "Name" ),
			( "fileSystem:owner", "Owner" ),
			( "fileSystem:modificationTime", "Modified" ),
		)

		menuDefinition = IECore.MenuDefinition()
		for key, label in infoFields :
			menuDefinition.append( "/" + label, { "command" : functools.partial( Gaffer.WeakMethod( self.__setInfoKey ), self.pathFilter(), key ), "checkBox" : key == self.pathFilter().getMatcher()[0] } )

		self.__menu = GafferUI.Menu( menuDefinition )
		self.__menu.popup()

	def __setInfoKey( self, filter, infoKey, checked ) :

		self.__updateFilter( newInfoKey=infoKey )

GafferUI.PathFilterWidget.registerType( Gaffer.InfoPathFilter, InfoPathFilterWidget )
