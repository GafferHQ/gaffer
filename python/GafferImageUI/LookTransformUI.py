##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#	  * Redistributions of source code must retain the above
#		copyright notice, this list of conditions and the following
#		disclaimer.
#
#	  * Redistributions in binary form must reproduce the above
#		copyright notice, this list of conditions and the following
#		disclaimer in the documentation and/or other materials provided with
#		the distribution.
#
#	  * Neither the name of John Haddon nor the names of
#		any other contributors to this software may be used to endorse or
#		promote products derived from this software without specific prior
#		written permission.
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
import GafferImage
import IECore

Gaffer.Metadata.registerNode(

	GafferImage.LookTransform,

	"description",
	"""
	OpenColorIO LookTransform
	
	A 'look' is a named color transform, intended to modify the look of an
	image in a 'creative' manner (as opposed to a colorspace definition which
	tends to be technically/mathematically defined).
	
	Examples of looks may be a neutral grade, to be applied to film scans
	prior to VFX work, or a per-shot DI grade decided on by the director,
	to be applied just before the viewing transform.
	
	OCIOLooks must be predefined in the OpenColorIO configuration before usage,
	often reference per-shot/sequence LUTs/CCs and are applied in scene linear colorspace.
	
	See the look plug for further syntax details.
	
	See opencolorio.org for look configuration customization examples.
	""",

	plugs={

		"look": [

			"description",
			"""
			Look Syntax:

			Multiple looks are combined with commas: 'neutral, primary'

			Direction is specified with +/- prefixes: '+neutral, -primary'

			Missing look 'fallbacks' specified with |: 'neutral, -primary | -primary'
			""",

			"layout:index", 0,

		],

		"direction": [

			"description", "Specify the look transform direction",

			"preset:Forward", GafferImage.LookTransform.Direction.Forward,
			"preset:Inverse", GafferImage.LookTransform.Direction.Inverse,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"nodule:type", "",

			"layout:index", 1,

		]

	}

)