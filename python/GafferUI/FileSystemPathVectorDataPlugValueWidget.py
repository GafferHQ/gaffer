##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
# - "fileSystemPath:extensions"
# - "fileSystemPath:extensionsLabel"
class FileSystemPathVectorDataPlugValueWidget( GafferUI.PathVectorDataPlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		GafferUI.PathVectorDataPlugValueWidget.__init__( self, plug, Gaffer.FileSystemPath(), **kw )

	def _updateFromMetadata( self ) :

		GafferUI.PathVectorDataPlugValueWidget._updateFromMetadata( self )

		self.path().setFilter(
			Gaffer.FileSystemPath.createStandardFilter(
				self.__extensions(),
				Gaffer.Metadata.value( self.getPlug(), "fileSystemPath:extensionsLabel" ) or "",
			)
		)

	def __extensions( self ) :

		if self.getPlug() is None :
			return []

		extensions = Gaffer.Metadata.value( self.getPlug(), "fileSystemPath:extensions" ) or []
		if isinstance( extensions, str ) :
			extensions = extensions.split()
		else :
			extensions = list( extensions )

		return extensions
