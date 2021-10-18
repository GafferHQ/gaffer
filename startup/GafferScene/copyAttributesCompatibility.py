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

import GafferScene

# The CopyAttributes node used to have a fixed length ArrayPlug as its "in" plug,
# but now has separate "in" and "source" plugs. Here we monkey patch the API so
# we can silently load scripts which were serialised in the old version.

def __copyAttributesGetItem( originalGetItem ) :

	def getItem( self, key ) :

		key = "sourceLocation" if key == "copyFrom" else key
		return originalGetItem( self, key )

	return getItem

def __copyAttributesInGetItem( originalGetItem ) :

	def getItem( self, key ) :

		if not isinstance( self.parent(), GafferScene.CopyAttributes ) or self.getName() != "in" :
			return originalGetItem( self, key )

		# We're getting a child of CopyAttributes.in.

		if key in ( "in0", ) :
			# First element of old ArrayPlug - redirect to self.
			return self
		elif key in ( "in1", ) :
			# Second element of old ArrayPlug - redirect to source.
			return self.parent()["source"]
		else:
			return originalGetItem( self, key )

		return originalGetItem( self, key )

	return getItem

GafferScene.CopyAttributes.__getitem__ = __copyAttributesGetItem( GafferScene.CopyAttributes.__getitem__ )
GafferScene.ScenePlug.__getitem__ = __copyAttributesInGetItem( GafferScene.ScenePlug.__getitem__ )
