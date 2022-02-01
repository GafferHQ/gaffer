##########################################################################
#
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferCortex

class FileIndexedIOPathPreview( GafferUI.DeferredPathPreview ) :

	def __init__( self, path ) :

		tmpPath = Gaffer.DictPath( {}, "/" ) # empty path we can use till we get an indexed io file
		with GafferUI.ListContainer( borderWidth = 8, spacing = 8 ) as column :

			self.__pathWidget = GafferUI.PathWidget( tmpPath )

			with GafferUI.SplitContainer( GafferUI.SplitContainer.Orientation.Horizontal ) :

				self.__pathListing = GafferUI.PathListingWidget(
					tmpPath,
					columns = [
						GafferUI.PathListingWidget.defaultNameColumn,
						GafferUI.PathListingWidget.defaultIndexedIODataTypeColumn,
					],
					displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
				)

				self.__pathPreview = GafferUI.DataPathPreview( tmpPath )

		GafferUI.DeferredPathPreview.__init__( self, column, path )

		self.__prevPath = tmpPath
		self._updateFromPath()

	def isValid( self ) :

		if not isinstance( self.getPath(), Gaffer.FileSystemPath ) or not self.getPath().isLeaf() :
			return False

		if os.path.splitext( self.getPath()[-1] )[1] not in ( ".cob", ".fio", ".scc", ".lscc" ) :
			return False

		return True

	def _load( self ) :

		return IECore.FileIndexedIO( str( self.getPath() ), IECore.IndexedIO.OpenMode.Read )

	def _deferredUpdate( self, indexedIO ) :

		self.__indexedIOPath = GafferCortex.IndexedIOPath( indexedIO, "/" )
		self.__indexedIOPathChangedConnection = self.__indexedIOPath.pathChangedSignal().connect( Gaffer.WeakMethod( self.__indexedIOPathChanged ), scoped = True )

		self.__pathWidget.setPath( self.__indexedIOPath )
		self.__pathPreview.setPath( self.__indexedIOPath )

		# we use a separate path for the listing so it'll always be rooted at the start
		listingPath = GafferCortex.IndexedIOPath( indexedIO, "/" )
		self.__pathListing.setPath( listingPath )
		self.__pathListingSelectionChangedConnection = self.__pathListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__pathListingSelectionChanged ), scoped = True )

	def __indexedIOPathChanged( self, path ) :

		pathCopy = path.copy()
		pathCopy.truncateUntilValid()

		with Gaffer.Signals.BlockedConnection( self.__pathListingSelectionChangedConnection ) :
			## \todo This functionality might be nice in the PathChooserWidget. We could
			# maybe even use a PathChooserWidget here anyway.
			self.__pathListing.setSelection( IECore.PathMatcher( [ str( pathCopy ) ] ), expandNonLeaf=False )
			# expand as people type forwards
			if len( pathCopy ) > len( self.__prevPath ) :
				self.__pathListing.setPathExpanded( pathCopy, True )
			# collapse as people delete backwards
			else :
				while len( pathCopy ) < len( self.__prevPath ) :
					self.__pathListing.setPathExpanded( self.__prevPath, False )
					del self.__prevPath[-1]

		self.__prevPath = pathCopy

	def __pathListingSelectionChanged( self, pathListing ) :

		selection = pathListing.getSelection()
		if not selection.isEmpty() :
			with Gaffer.Signals.BlockedConnection( self.__indexedIOPathChangedConnection ) :
				self.__indexedIOPath.setFromString( selection.paths()[0] )

GafferUI.PathPreviewWidget.registerType( "Indexed IO", FileIndexedIOPathPreview )
