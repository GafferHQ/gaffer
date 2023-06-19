##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import PyOpenColorIO

import IECore

import Gaffer
import GafferUI
import GafferImage
from . import OpenColorIOTransformUI


def __displayPresetNames( plug ) :

	config = GafferImage.OpenColorIOAlgo.currentConfig()
	return IECore.StringVectorData( [ "None" ] + list( config.getDisplays() ) )

def __displayPresetValues( plug ) :

	config = GafferImage.OpenColorIOAlgo.currentConfig()
	return IECore.StringVectorData( [ "" ] + list( config.getDisplays() ) )

def __viewPresetNames( plug ) :

	config = GafferImage.OpenColorIOAlgo.currentConfig()
	display = plug.parent()["display"].getValue()

	return IECore.StringVectorData( [ "None" ] + list( config.getViews( display ) ) )

def __viewPresetValues( plug ) :

	config = GafferImage.OpenColorIOAlgo.currentConfig()
	display = plug.parent()["display"].getValue()

	return IECore.StringVectorData( [ "" ] + list( config.getViews( display ) ) )

Gaffer.Metadata.registerNode(

	GafferImage.DisplayTransform,

	"description",
	"""
	Applies color transformations provided by
	OpenColorIO via a DisplayTransform file and OCIO FileTransform.
	""",

	plugs = {

		"inputColorSpace" : [

			"description",
			"""
			The colour space of the input image.
			""",

			"presetNames", OpenColorIOTransformUI.colorSpacePresetNames,
			"presetValues", OpenColorIOTransformUI.colorSpacePresetValues,
			"openColorIO:extraPresetNames", IECore.StringVectorData( [ "Working Space" ] ),
			"openColorIO:extraPresetValues", IECore.StringVectorData( [ "" ] ),

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		],

		"display" : [

			"description",
			"""
			The name of the display to use.
			""",

			"presetNames", __displayPresetNames,
			"presetValues", __displayPresetValues,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"view" : [

			"description",
			"""
			The name of the view to use.
			""",

			"presetNames", __viewPresetNames,
			"presetValues", __viewPresetValues,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

	}

)
