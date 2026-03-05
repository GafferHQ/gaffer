##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import IECore
import IECoreScene

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.CurvesInterpolation,

	"description",
	"""
	Defines how CurvesPrimitive geometry is interpolated, by
	modifying `basis` and `wrap`.
	""",

	plugs = {

		"basis.value" : {

			"description" :
			"""
			The method used to interpolate the vertices of the curves.

			- Linear : Straight lines between vertices.
			- BSpline : Smooth interpolation approximating - but not passing
			  directly through - each vertex. Requires `Pinned` wrap mode to
			  interpolate all the way to the end vertices.
			- CatmullRom : Smooth interpolation passing directly through each
			  vertex. Requires `Pinned` wrap mode to interpolate all the way
			  to the end vertices.
			""",

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			# We only expose the basis types which have a step of 1.
			# We can safely convert between any of these without them
			# invalidating the curve topology.
			"preset:Linear" : IECore.StandardCubicBasis.Linear,
			"preset:BSpline" : IECore.StandardCubicBasis.BSpline,
			"preset:CatmullRom" : IECore.StandardCubicBasis.CatmullRom,

		},

		"wrap.value" : {

			"description" :
			"""
			The treatment of the first and last curve segments.

			- Pinned : Automatically uses "phantom points" to ensure that
			  CatmullRom and BSpline curves interpolate all the way to their
			  endpoints. Equivalent to `NonPeriodic` for all other curve types.
			- Periodic : Wraps the curve around to form a closed loop.
			- NonPeriodic : Neither wraps the curve to produce a loop or introduces
			  phantom endpoints. Generally inferior to the other options.
			""",

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:Pinned" : IECoreScene.CurvesPrimitive.Wrap.Pinned,
			"preset:Periodic" : IECoreScene.CurvesPrimitive.Wrap.Periodic,
			"preset:NonPeriodic" : IECoreScene.CurvesPrimitive.Wrap.NonPeriodic,

		},

		"expandPinned" : {

			"description" :
			"""
			When converting Pinned curves to NonPeriodic, adds the "phantom" vertices
			so that the curves continue to interpolate to their original endpoints.
			""",

			"layout:activator" : lambda plug : plug.parent()["wrap"]["enabled"].getValue() and plug.parent()["wrap"]["value"].getValue() == IECoreScene.CurvesPrimitive.Wrap.NonPeriodic,

		},

	}

)
