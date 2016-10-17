##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI

## Supported plug metadata :
#
# - "fileSystemPathPlugValueWidget:extensions"
# - "fileSystemPathPlugValueWidget:extensionsLabel"
# - "fileSystemPathPlugValueWidget:includeSequences"
# - "fileSystemPathPlugValueWidget:includeSequenceFrameRange"
#	Note that includeSequenceFrameRange is primarily used
#	by GafferCortex. Think twice before using it elsewhere
#	as it may not exist in the future.
class FileSystemPathPlugValueWidget( GafferUI.PathPlugValueWidget ) :

	def __init__( self, plug, path=None, **kw ) :

		GafferUI.PathPlugValueWidget.__init__(
			self,
			plug,
			path,
			**kw
		)

		self._updateFromPlug()

	def getToolTip( self ) :

		result = GafferUI.PathPlugValueWidget.getToolTip( self )

		extensions = self.__extensions()
		if extensions :
			result += "\n\nSupported file extensions : " + ", ".join( extensions )

		return result

	def _pathChooserDialogue( self ) :

		dialogue = GafferUI.PathPlugValueWidget._pathChooserDialogue( self )

		if Gaffer.Metadata.value( self.getPlug(), "fileSystemPathPlugValueWidget:includeSequences" ) :

			columns = dialogue.pathChooserWidget().pathListingWidget().getColumns()
			columns.append( GafferUI.PathListingWidget.StandardColumn( "Frame Range", "fileSystem:frameRange" ) )
			dialogue.pathChooserWidget().pathListingWidget().setColumns( columns )

		return dialogue

	def _updateFromPlug( self ) :

		GafferUI.PathPlugValueWidget._updateFromPlug( self )

		includeSequences = Gaffer.Metadata.value( self.getPlug(), "fileSystemPathPlugValueWidget:includeSequences" ) or False

		self.path().setFilter(
			Gaffer.FileSystemPath.createStandardFilter(
				self.__extensions(),
				Gaffer.Metadata.value( self.getPlug(), "fileSystemPathPlugValueWidget:extensionsLabel" ) or "",
				includeSequenceFilter = includeSequences,
			)
		)

		self.path().setIncludeSequences( includeSequences )

	def _setPlugFromPath( self, path ) :

		if Gaffer.Metadata.value( self.getPlug(), "fileSystemPathPlugValueWidget:includeSequenceFrameRange" ) :
			sequence = path.fileSequence()
			if sequence :
				self.getPlug().setValue( str(sequence) )
				return

		GafferUI.PathPlugValueWidget._setPlugFromPath( self, path )

	def __extensions( self ) :

		if self.getPlug() is None :
			return []

		extensions = Gaffer.Metadata.value( self.getPlug(), "fileSystemPathPlugValueWidget:extensions" ) or []
		if isinstance( extensions, str ) :
			extensions = extensions.split()
		else :
			extensions = list( extensions )

		return extensions
