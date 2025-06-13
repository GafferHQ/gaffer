##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

class __OptionsPlugProxy( object ) :

	__renames = {
		"renderCamera" : "render:camera",
		"filmFit" : "render:filmFit",
		"renderResolution" : "render:resolution",
		"pixelAspectRatio" : "render:pixelAspectRatio",
		"resolutionMultiplier" : "render:resolutionMultiplier",
		"renderCropWindow" : "render:cropWindow",
		"overscan" : "render:overscan",
		"overscanTop" : "render:overscanTop",
		"overscanBottom" : "render:overscanBottom",
		"overscanLeft" : "render:overscanLeft",
		"overscanRight" : "render:overscanRight",
		"depthOfField" : "render:depthOfField",
		"defaultRenderer" : "render:defaultRenderer",
		"includedPurposes" : "render:includedPurposes",
		"inclusions" : "render:inclusions",
		"exclusions" : "render:exclusions",
		"additionalLights" : "render:additionalLights",
		"transformBlur" : "render:transformBlur",
		"deformationBlur" : "render:deformationBlur",
		"shutter" : "render:shutter",
		"performanceMonitor" : "render:performanceMonitor",
	}

	def __init__( self, optionsPlug ) :

		self.__optionsPlug = optionsPlug

	def __getitem__( self, key ) :

		return self.__optionsPlug[self.__renames.get( key, key )]

def __optionsGetItem( originalGetItem ) :

	def getItem( self, key ) :

		result = originalGetItem( self, key )
		if key == "options" :
			scriptNode = self.ancestor( Gaffer.ScriptNode )
			if scriptNode is not None and scriptNode.isExecuting() :
				return __OptionsPlugProxy( result )

		return result

	return getItem

GafferScene.StandardOptions.__getitem__ = __optionsGetItem( GafferScene.StandardOptions.__getitem__ )
