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

import os

import IECore
import Gaffer
import GafferScene

def __registerShaderPresets( presets ) :

	for name, value in presets :
		Gaffer.Metadata.registerValue( GafferScene.ShaderTweaks, "shader", "preset:" + name, value )

with IECore.IgnoredExceptions( ImportError ) :

	import GafferArnold

	__registerShaderPresets( [

		( "Arnold Surface", "ai:surface" ),
		( "Arnold Displacement", "ai:disp_map" ),
		( "Arnold Light", "ai:light" ),
		( "Arnold Gobo", "ai:lightFilter:gobo" ),
		( "Arnold Decay", "ai:lightFilter:light_decay" ),
		( "Arnold Barndoor", "ai:lightFilter:barndoor" ),
		( "Arnold Blocker", "ai:lightFilter:filter" )

	] )

if os.environ.get( "GAFFERAPPLESEED_HIDE_UI", "" ) != "1" :

	with IECore.IgnoredExceptions( ImportError ) :

		import GafferAppleseed

		__registerShaderPresets( [

			( "Appleseed Light", "as:light" ),

		] )

with IECore.IgnoredExceptions( ImportError ) :

	import GafferOSL

	__registerShaderPresets( [

		( "OSL Surface", "osl:surface" ),
		( "OSL Light", "osl:light" ),

	] )
