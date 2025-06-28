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

import imath

import Gaffer

Gaffer.Metadata.registerValues( {

	"parameter:camera:projection" : [

		"defaultValue", "orthographic",
		"label", "Projection",

	],

	"parameter:camera:fieldOfView" : [

		"defaultValue", 50.0,
		"minValue", 0.0,
		"maxValue", 180.0,
		"label", "Field Of View",

	],

	"parameter:camera:apertureAspectRatio" : [

		"defaultValue", 1.0,
		"minValue", 0.0,
		"label", "Aperture Aspect Ratio",

	],

	"parameter:camera:aperture" : [

		"defaultValue", imath.V2f( 2 ),
		"label", "Aperture",

	],

	"parameter:camera:focalLength" : [

		"defaultValue", 1.0,
		"minValue", 0.0,
		"label", "Focal Length",

	],

	"parameter:camera:apertureOffset" : [

		"defaultValue", imath.V2f( 0 ),
		"label", "Aperture Offset",

	],

	"parameter:camera:fStop" : [

		"defaultValue", 0.0,
		"minValue", 0.0,
		"label", "F Stop",
		"layout:section", "Depth of Field",

	],

	"parameter:camera:focalLengthWorldScale" : [

		"defaultValue", 0.1,
		"minValue", 0.0,
		"label", "Focal Length World Scale",
		"layout:section", "Depth of Field",

	],

	"parameter:camera:focusDistance" : [

		"defaultValue", 1.0,
		"label", "Focus Distance",
		"layout:section", "Depth of Field",

	],

	"parameter:camera:clippingPlanes" : [

		"defaultValue", imath.V2f( 0.01, 100000 ),
		"label", "Clipping Planes",

	],

	"parameter:camera:filmFit" : [

		"defaultValue", 0,
		"label", "Film Fit",
		"layout:section", "Render Overrides",

	],

	"parameter:camera:shutter" : [

		"defaultValue", imath.V2f( -0.5, 0.5 ),
		"label", "Shutter",
		"layout:section", "Render Overrides",

	],

	"parameter:camera:resolution" : [

		"defaultValue", imath.V2i( 1024 ),
		"label", "Resolution",
		"layout:section", "Render Overrides",

	],

	"parameter:camera:pixelAspectRatio" : [

		"defaultValue", 1.0,
		"label", "Pixel Aspect Ratio",
		"layout:section", "Render Overrides",

	],

	"parameter:camera:resolutionMultiplier" : [

		"defaultValue", 1.0,
		"label", "Resolution Multiplier",
		"layout:section", "Render Overrides",

	],

	"parameter:camera:overscan" : [

		"defaultValue", False,
		"label", "Overscan",
		"layout:section", "Render Overrides",

	],

	"parameter:camera:overscanLeft" : [

		"defaultValue", 0.0,
		"label", "Overscan Left",
		"layout:section", "Render Overrides",

	],

	"parameter:camera:overscanRight" : [

		"defaultValue", 0.0,
		"label", "Overscan Right",
		"layout:section", "Render Overrides",

	],

	"parameter:camera:overscanTop" : [

		"defaultValue", 0.0,
		"label", "Overscan Top",
		"layout:section", "Render Overrides",

	],

	"parameter:camera:overscanBottom" : [

		"defaultValue", 0.0,
		"label", "Overscan Bottom",
		"layout:section", "Render Overrides",

	],

	"parameter:camera:cropWindow" : [

		"defaultValue", imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ),
		"label", "Crop Window",
		"layout:section", "Render Overrides",

	],

	"parameter:camera:depthOfField" : [

		"defaultValue", False,
		"label", "Depth Of Field",
		"layout:section", "Render Overrides",

	],

} )
