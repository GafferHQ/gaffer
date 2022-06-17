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
import GafferScene

# Compatibility with old tweak plugs with unnecessary stuff serialized
def __tweakPlugAddChild( originalAddChild ) :

	def addChild( self, child ) :
		if child.getName() in [ "name", "enabled", "mode" ] and child.getName() in self.keys():
			pass # Old scripts have serialized addChilds for these non-dynamic plugs
		else:
			return originalAddChild( self, child )

	return addChild

Gaffer.TweakPlug.addChild = __tweakPlugAddChild( Gaffer.TweakPlug.addChild )

# Compatibility for old LightTweaks nodes

class LightTweaks( GafferScene.ShaderTweaks ) :

	def __init__( self, name = "LightTweaks" ) :

		GafferScene.ShaderTweaks.__init__( self, name )
		self["shader"].setValue( "light *:light" )

	def __getitem__( self, key ) :

		if key == "type" :
			key = "shader"

		return GafferScene.ShaderTweaks.__getitem__( self, key )

GafferScene.LightTweaks = LightTweaks
GafferScene.LightTweaks.TweakPlug = Gaffer.TweakPlug
