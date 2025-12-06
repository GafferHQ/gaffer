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

import IECore

Gaffer.Metadata.registerValues( {

	"camera:parameter:shutter_type" : {

		"defaultValue" : "box",
		"label" : "Shutter Type",
		"layout:section" : "Arnold",

		"presetNames" : IECore.StringVectorData( [ "Box", "Triangle", "Curve" ] ),
		"presetValues" : IECore.StringVectorData( [ "box", "triangle", "curve" ] ),

	},

	"camera:parameter:shutter_curve" : {

		"defaultValue" : IECore.RampffData(),
		"label" : "Shutter Curve",
		"layout:section" : "Arnold",

	},

	"camera:parameter:rolling_shutter" : {

		"defaultValue" : "off",
		"label" : "Rolling Shutter",
		"layout:section" : "Arnold",

		"presetNames" : IECore.StringVectorData( [ "Off", "Top", "Bottom", "Left", "Right" ] ),
		"presetValues" : IECore.StringVectorData( [ "off", "top", "bottom", "left", "right" ] ),

	},

	"camera:parameter:rolling_shutter_duration" : {

		"defaultValue" : 0.0,
		"minValue" : 0.0,
		"maxValue" : 1.0,
		"label" : "Rolling Shutter Duration",
		"layout:section" : "Arnold",

	},

	"camera:parameter:aperture_blades" : {

		"defaultValue" : 6,
		"minValue" : 0,
		"maxValue" : 40,
		"label" : "Aperture Blades",
		"layout:section" : "Arnold",

	},

	"camera:parameter:aperture_blade_curvature" : {

		"defaultValue" : 0.0,
		"minValue" : -20.0,
		"maxValue" : 20.0,
		"label" : "Aperture Blade Curvature",
		"layout:section" : "Arnold",

	},

	"camera:parameter:aperture_rotation" : {

		"defaultValue" : 0.0,
		"minValue" : 0.0,
		"maxValue" : 360.0,
		"label" : "Aperture Rotation",
		"layout:section" : "Arnold",

	},

} )
