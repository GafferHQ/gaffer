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
import GafferScene

class __STPlugProxy( object ) :

	def __init__( self, uvSetPlug, coordinate ) :

		self.__uvSetPlug = uvSetPlug
		self.__coordinate = coordinate

	def setValue( self, value ) :

		if value == self.__coordinate :
			self.__uvSetPlug.setValue( "uv" )
		elif value.endswith( "_" + self.__coordinate ) :
			self.__uvSetPlug.setValue( value[:-2] )
		else :
			IECore.msg( IECore.Msg.Level.Warning, "__STPlugProxy.setValue", "Unable to remap value \"{}\"".format( value ) )

# Provides backwards compatibility by converting from old sName/tName
# plugs to uvSet plugs.
def __mapNodeGetItem( originalGetItem ) :

	def getItem( self, key ) :

		if key == "sName" :
			return __STPlugProxy( self["uvSet"], "s" )
		elif key == "tName" :
			return __STPlugProxy( self["uvSet"], "t" )
		else :
			return originalGetItem( self, key )

	return getItem

GafferScene.MapProjection.__getitem__ = __mapNodeGetItem( GafferScene.MapProjection.__getitem__ )
GafferScene.MapOffset.__getitem__ = __mapNodeGetItem( GafferScene.MapOffset.__getitem__ )
