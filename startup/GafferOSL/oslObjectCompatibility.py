##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import GafferOSL

class __DummyShaderPlug:
	def __init__( self, node ):
		self._node = node

	def setInput( self, plug ):
		if not isinstance( plug.node(), GafferOSL.OSLShader ) or not plug.node()["name"].getValue() == "ObjectProcessing/OutObject":
			raise RuntimeError( "Failed to load deprecated connection from " + plug.fullName() + " to " + self._node.fullName() )

		closurePlug = GafferOSL.ClosurePlug( "closure" )
		self._node["primitiveVariables"].addChild( closurePlug )
		closurePlug.setInput( plug.node()["out"]["out"] )


# Provides backwards compatibility by allowing access to "multiInput" plug
# using its old name of "shader".
def __oslObjectGetItem( originalGetItem ) :

	def getItem( self, key ) :
		if key == "shader":
			return __DummyShaderPlug( self )
		else:
			return originalGetItem( self, key )

	return getItem

GafferOSL.OSLObject.__getitem__ = __oslObjectGetItem( GafferOSL.OSLObject.__getitem__ )
