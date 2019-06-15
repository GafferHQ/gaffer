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

import Gaffer
import GafferOSL

class __DummyShaderPlug( object ):
	def __init__( self, node ):
		self.__node = node

	def setInput( self, plug ):
		if isinstance( self.__node, GafferOSL.OSLImage ):
			parentPlug = self.__node["channels"]
		else:
			parentPlug = self.__node["primitiveVariables"]

		if not "legacyClosure" in parentPlug:
			parentPlug.addChild(
				Gaffer.NameValuePlug( "", GafferOSL.ClosurePlug( "closure", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ), True, "legacyClosure" )
			)

		parentPlug["legacyClosure"]["value"].setInput( plug )


# Provides backwards compatibility by allowing access to closure plug
# using its old name of "shader".
def __oslReplaceShaderGetItem( originalGetItem ) :

	def getItem( self, key ) :
		if key == "shader":
			return __DummyShaderPlug( self )
		else:
			return originalGetItem( self, key )

	return getItem

GafferOSL.OSLObject.__getitem__ = __oslReplaceShaderGetItem( GafferOSL.OSLObject.__getitem__ )
GafferOSL.OSLImage.__getitem__ = __oslReplaceShaderGetItem( GafferOSL.OSLImage.__getitem__ )

def __oslShaderGetItem( originalGetItem ) :

	def getItem( self, key ) :
		if key != "out":
			return originalGetItem( self, key )

		if originalGetItem( self, "name" ).getValue() not in [ "ObjectProcessing/OutObject", "ImageProcessing/OutImage" ]:
			return originalGetItem( self, key )

		scriptNode = self.ancestor( Gaffer.ScriptNode )
		if not scriptNode or not scriptNode.isExecuting():
			return originalGetItem( self, key )

		parentNode = self.ancestor( Gaffer.Node )
		gafferVersion = None
		while parentNode :
			gafferVersion = (
				Gaffer.Metadata.value( parentNode, "serialiser:milestoneVersion" ),
				Gaffer.Metadata.value( parentNode, "serialiser:majorVersion" ),
				Gaffer.Metadata.value( parentNode, "serialiser:minorVersion" ),
				Gaffer.Metadata.value( parentNode, "serialiser:patchVersion" )
			)

			# only use the information if we have valid information from the node
			if not filter( lambda x : x is None, gafferVersion ) :
				break

			gafferVersion = None
			parentNode = parentNode.ancestor( Gaffer.Node )

		if gafferVersion is not None and gafferVersion < ( 0, 54, 0, 0 ) :
			return originalGetItem( self, "out" )["out"]

		return originalGetItem( self, "out" )

	return getItem

GafferOSL.OSLShader.__getitem__ = __oslShaderGetItem( GafferOSL.OSLShader.__getitem__ )
