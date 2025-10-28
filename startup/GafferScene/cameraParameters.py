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

	"camera:parameter:projection" : {

		"defaultValue" : "orthographic",
		"label" : "Projection",

	},

	"camera:parameter:fieldOfView" : {

		"defaultValue" : 50.0,
		"minValue" : 0.0,
		"maxValue" : 180.0,
		"label" : "Field Of View",

	},

	"camera:parameter:apertureAspectRatio" : {

		"defaultValue" : 1.0,
		"minValue" : 0.0,
		"label" : "Aperture Aspect Ratio",

	},

	"camera:parameter:aperture" : {

		"defaultValue" : imath.V2f( 2 ),
		"label" : "Aperture",

	},

	"camera:parameter:focalLength" : {

		"defaultValue" : 1.0,
		"minValue" : 0.0,
		"label" : "Focal Length",

	},

	"camera:parameter:apertureOffset" : {

		"defaultValue" : imath.V2f( 0 ),
		"label" : "Aperture Offset",

	},

	"camera:parameter:fStop" : {

		"defaultValue" : 0.0,
		"minValue" : 0.0,
		"label" : "F Stop",
		"layout:section" : "Depth of Field",

	},

	"camera:parameter:focalLengthWorldScale" : {

		"defaultValue" : 0.1,
		"minValue" : 0.0,
		"label" : "Focal Length World Scale",
		"layout:section" : "Depth of Field",

	},

	"camera:parameter:focusDistance" : {

		"defaultValue" : 1.0,
		"label" : "Focus Distance",
		"layout:section" : "Depth of Field",

	},

	"camera:parameter:clippingPlanes" : {

		"defaultValue" : imath.V2f( 0.01, 100000 ),
		"label" : "Clipping Planes",

	},

	"camera:parameter:filmFit" : {

		"defaultValue" : 0,
		"label" : "Film Fit",
		"layout:section" : "Render Overrides",

	},

	"camera:parameter:shutter" : {

		"defaultValue" : imath.V2f( -0.5, 0.5 ),
		"label" : "Shutter",
		"layout:section" : "Render Overrides",

	},

	"camera:parameter:resolution" : {

		"defaultValue" : imath.V2i( 1024 ),
		"label" : "Resolution",
		"layout:section" : "Render Overrides",

	},

	"camera:parameter:pixelAspectRatio" : {

		"defaultValue" : 1.0,
		"label" : "Pixel Aspect Ratio",
		"layout:section" : "Render Overrides",

	},

	"camera:parameter:resolutionMultiplier" : {

		"defaultValue" : 1.0,
		"label" : "Resolution Multiplier",
		"layout:section" : "Render Overrides",

	},

	"camera:parameter:overscan" : {

		"defaultValue" : False,
		"label" : "Overscan",
		"layout:section" : "Render Overrides",

	},

	"camera:parameter:overscanLeft" : {

		"defaultValue" : 0.0,
		"label" : "Overscan Left",
		"layout:section" : "Render Overrides",

	},

	"camera:parameter:overscanRight" : {

		"defaultValue" : 0.0,
		"label" : "Overscan Right",
		"layout:section" : "Render Overrides",

	},

	"camera:parameter:overscanTop" : {

		"defaultValue" : 0.0,
		"label" : "Overscan Top",
		"layout:section" : "Render Overrides",

	},

	"camera:parameter:overscanBottom" : {

		"defaultValue" : 0.0,
		"label" : "Overscan Bottom",
		"layout:section" : "Render Overrides",

	},

	"camera:parameter:cropWindow" : {

		"defaultValue" : imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ),
		"label" : "Crop Window",
		"layout:section" : "Render Overrides",

	},

	"camera:parameter:depthOfField" : {

		"defaultValue" : False,
		"label" : "Depth Of Field",
		"layout:section" : "Render Overrides",

	},

} )
