##########################################################################
#
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

## Supported plug metadata - used to provide arguments to a
# PathChooserDialogue :
#
# - "path:leaf"
# - "path:valid"
# - "path:bookmarks"
class PathVectorDataPlugValueWidget( GafferUI.PlugValueWidget ) :

	## path should be an instance of Gaffer.Path, optionally with
	# filters applied. It will be used to convert string values to
	# paths for the path uis to edit.
	#
	# \deprecated The pathChooserDialogueKeywords argument will be removed
	# in a future version - use metadata instead.
	def __init__( self, plug, path, pathChooserDialogueKeywords={}, **kw ) :

		self.__dataWidget = GafferUI.PathVectorDataWidget( path=path, pathChooserDialogueKeywords=Gaffer.WeakMethod( self.__pathChooserDialogueKeywords ) )

		GafferUI.PlugValueWidget.__init__( self, self.__dataWidget, plug, **kw )

		self.__dataWidget.dataChangedSignal().connect( Gaffer.WeakMethod( self.__dataChanged ) )
		self.__deprecatedPathChooserDialogueKeywords = pathChooserDialogueKeywords

	def path( self ) :

		return self.__dataWidget.path()

	def _updateFromValues( self, values, exception ) :

		if len( values ) :
			assert( len( values ) == 1 )
			self.__dataWidget.setData( values[0] )

	def _updateFromEditable( self ) :

		self.__dataWidget.setEditable( self._editable() )

	def __dataChanged( self, widget ) :

		assert( widget is self.__dataWidget )

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			with self._blockedUpdateFromValues() :
				self.getPlug().setValue( self.__dataWidget.getData()[0] )

	def __pathChooserDialogueKeywords( self ) :

		result = {}
		result["leaf"] = Gaffer.Metadata.value( self.getPlug(), "path:leaf" )
		result["valid"] = Gaffer.Metadata.value( self.getPlug(), "path:valid" )

		bookmarks = Gaffer.Metadata.value( self.getPlug(), "path:bookmarks" )
		if bookmarks is not None :
			result["bookmarks"] = GafferUI.Bookmarks.acquire( self.getPlug(), type( self.path() ), bookmarks )

		if callable( self.__deprecatedPathChooserDialogueKeywords ) :
			result.update( self.__deprecatedPathChooserDialogueKeywords() )
		else :
			result.update( self.__deprecatedPathChooserDialogueKeywords )

		return result
