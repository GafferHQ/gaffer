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

import types

import GafferScene

# The CollectScenes node used to have an ArrayPlug as its "in" plug,
# but only ever used the first input. Now it correctly has a single
# ScenePlug called "in". Here we monkey patch the API so we can silently
# load scripts which were serialised in the bad version.

def __collectScenesInAddChild( self, child ) :

	# Serialisation may have an `addChild()` call to add a second plug
	# to the old ArrayPlug. We just ignore it.
	pass

def __collectScenesGetItem( originalGetItem ) :

	def getItem( self, key ) :

		result = originalGetItem( self, key )
		if key == "in" :
			result.addChild = types.MethodType( __collectScenesInAddChild, result )

		return result

	return getItem

def __collectScenesInGetItem( originalGetItem ) :

	def getItem( self, key ) :

		if not isinstance( self.parent(), GafferScene.CollectScenes ) or self.getName() != "in" :
			return originalGetItem( self, key )

		# We're getting a child of CollectScenes.in.

		if key == "in0" :
			# First element of old ArrayPlug - redirect to self.
			return self
		elif isinstance( key, str ) and key.startswith( "in" ) :
			# Any other element of old ArrayPlug - this should not
			# have been used.
			return None
		else :
			return originalGetItem( self, key )

	return getItem

GafferScene.CollectScenes.__getitem__ = __collectScenesGetItem( GafferScene.CollectScenes.__getitem__ )
GafferScene.ScenePlug.__getitem__ = __collectScenesInGetItem( GafferScene.ScenePlug.__getitem__ )
