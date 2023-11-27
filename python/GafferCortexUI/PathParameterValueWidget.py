##########################################################################
#
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

import contextlib

import IECore

import Gaffer
import GafferUI
import GafferCortex
import GafferCortexUI

class PathParameterValueWidget( GafferCortexUI.ParameterValueWidget ) :

	def __init__( self, parameterHandler, **kw ) :

		self.__pathWidget = GafferUI.FileSystemPathPlugValueWidget(
			parameterHandler.plug(),
			self._path(),
			pathChooserDialogueKeywords = Gaffer.WeakMethod( self._pathChooserDialogueKeywords ),
		)

		GafferCortexUI.ParameterValueWidget.__init__(

			self,
			self.__pathWidget,
			parameterHandler,
			**kw

		)

	def _path( self ) :

		return Gaffer.FileSystemPath( "/", filter = self._filter() )

	def _filter( self ) :

		return Gaffer.FileSystemPath.createStandardFilter()

	def _pathChooserDialogueKeywords( self ) :

		result = {}

		bookmarksCategory = None
		with contextlib.suppress( KeyError ) :
			bookmarksCategory = self.parameter().userData()["UI"]["bookmarksCategory"].value
		result["bookmarks"] = GafferUI.Bookmarks.acquire(
			# sometimes parameter widgets are used with nodes which are parented to an application,
			# but where the window isn't. and sometimes they're used with nodes with no application,
			# but where the window does belong to an application. so we hedge our bets and use both
			# the widget and the plug to try to find bookmarks for the application.
			( self, self.plug() ),
			# deliberately using FileSystemPath directly rather than using _path().__class__
			# so that file sequences share the same set of bookmarks as files.
			pathType = Gaffer.FileSystemPath,
			category = bookmarksCategory,
		)

		return result

GafferCortexUI.ParameterValueWidget.registerType( IECore.PathParameter, PathParameterValueWidget )

__nodeTypes = (
	GafferCortex.ParameterisedHolderNode,
	GafferCortex.ParameterisedHolderComputeNode,
	GafferCortex.ParameterisedHolderDependencyNode,
	GafferCortex.ParameterisedHolderTaskNode,
)

def __hasExtensions( plug ) :

	handler = plug.node().parameterHandler()
	if not handler :
		return None

	parameter = handler.parameter()
	for p in plug.relativeName( plug.node() ).split( "." )[1:] :
		parameter = parameter[p]

	if not isinstance( parameter, IECore.FileNameParameter ) :
		return None

	return IECore.StringVectorData( parameter.extensions )

for nodeType in __nodeTypes :
	Gaffer.Metadata.registerValue( nodeType, "parameters.*...", "fileSystemPath:extensions", __hasExtensions )
