##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import types

import Gaffer
import GafferScene

# In Gaffer 0.55, the single `Parent.child` plug has been replaced
# with a `Parent.children` array plug. This proxy class makes the
# existing `child` plug compatible with serialisations from 0.55, provided
# that only the first element of the array is used.
class __ChildrenPlugProxy( object ) :

	def __init__( self, childPlug ) :

		self.__childPlug = childPlug

	def addChild( self, child ) :

		pass

	def __getitem__( self, key ) :

		return self.__childPlug

def __parentGetItemWrapper( originalGetItem ) :

	def getItem( self, key ) :

		if key == "children" :
			return __ChildrenPlugProxy( self["child"] )

		return originalGetItem( self, key )

	return getItem

GafferScene.Parent.__getitem__ = __parentGetItemWrapper( GafferScene.Parent.__getitem__ )

# In Gaffer 0.55, the `in[0], in[1]` array plug elements were
# replaced with separate `in` and `source` plugs and other plugs
# were renamed. Here we add shims so that we can load files from
# 0.55.

def __copyAttributesInSetInput( self, input ) :

	if isinstance( input, GafferScene.ScenePlug ) :
		self[0].setInput( input )
	else :
		self.__class__.setInput( self, input )

def __copyAttributesGetItemWrapper( originalGetItem ) :

	def getItem( self, key ) :

		if key == "in" :
			result = originalGetItem( self, "in" )
			result.setInput = types.MethodType( __copyAttributesInSetInput, result )
			return result
		elif key == "source" :
			return originalGetItem( self, "in" )[1]
		elif key == "sourceLocation" :
			return originalGetItem( self, "copyFrom" )

		return originalGetItem( self, key )

	return getItem

GafferScene.CopyAttributes.__getitem__ = __copyAttributesGetItemWrapper( GafferScene.CopyAttributes.__getitem__ )

# In Gaffer 0.55, the "names" plug of the CopyOptions node
# is renamed to "options". This shim makes it possible to load
# files from the future.

def __copyOptionsGetItemWrapper( originalGetItem ) :

	def getItem( self, key ) :

		if key == "options" :
			key = "names"

		return originalGetItem( self, key )

	return getItem

GafferScene.CopyOptions.__getitem__ = __copyOptionsGetItemWrapper( GafferScene.CopyOptions.__getitem__ )
