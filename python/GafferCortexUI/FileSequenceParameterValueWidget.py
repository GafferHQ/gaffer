##########################################################################
#
#  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferCortex

import GafferCortexUI

class FileSequenceParameterValueWidget( GafferCortexUI.PathParameterValueWidget ) :

	def __init__( self, parameterHandler, **kw ) :

		GafferCortexUI.PathParameterValueWidget.__init__( self, parameterHandler, **kw )

	def _path( self ) :

		return Gaffer.FileSystemPath( "/", filter = self._filter(), includeSequences = True )

	def _filter( self ) :

		return Gaffer.FileSystemPath.createStandardFilter( includeSequenceFilter = True )

GafferCortexUI.ParameterValueWidget.registerType( IECore.FileSequenceParameter, FileSequenceParameterValueWidget )
GafferCortexUI.ParameterValueWidget.registerType( IECore.PathParameter, FileSequenceParameterValueWidget, uiTypeHint="includeSequences" )

# we've copied this list of node types from
# ParameterisedHolderUI because it seemed
# better to keep this FileSequence metadata
# logic self contained in this file.
__nodeTypes = (
	GafferCortex.ParameterisedHolderNode,
	GafferCortex.ParameterisedHolderComputeNode,
	GafferCortex.ParameterisedHolderDependencyNode,
	GafferCortex.ParameterisedHolderTaskNode,
)

def __isFileSequence( plug ) :

	handler = plug.node().parameterHandler()
	if not handler :
		return None

	parameter = handler.parameter()
	for p in plug.relativeName( plug.node() ).split( "." )[1:] :
		parameter = parameter[p]

	if isinstance( parameter, IECore.FileSequenceParameter ) :
		return True

	if isinstance( parameter, IECore.PathParameter ) :
		with IECore.IgnoredExceptions( KeyError ) :
			return parameter.userData()["UI"]["typeHint"].value == "includeSequences"

	return False


def __includeFrameRange( plug ) :

	handler = plug.node().parameterHandler()
	if not handler :
		return None

	parameter = handler.parameter()
	for p in plug.relativeName( plug.node() ).split( "." )[1:] :
		parameter = parameter[p]

	if not isinstance( parameter, IECore.FileSequenceParameter ) :
		return None

	includeFrameRange = True
	with IECore.IgnoredExceptions( KeyError ) :
		includeFrameRange = parameter.userData()["UI"]["includeFrameRange"].value

	return includeFrameRange

for nodeType in __nodeTypes :
	Gaffer.Metadata.registerValue( nodeType, "parameters.*...", "fileSystemPath:includeSequences", __isFileSequence )
	Gaffer.Metadata.registerValue( nodeType, "parameters.*...", "fileSystemPath:includeSequenceFrameRange", __includeFrameRange )
