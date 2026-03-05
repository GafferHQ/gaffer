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

	GafferScene.CurvesTweaks,

	# "description",
	# """
	# Changes between polygon and subdivision representations
	# for mesh objects, and optionally recalculates vertex
	# normals for polygon meshes.

	# Note that currently the Gaffer viewport does not display
	# subdivision meshes with smoothing, so the results of using
	# this node will not be seen until a render is performed.
	# """,

	plugs = {

		"wrap.value" : {

			# "description" :
			# """
			# The interpolation type to apply to the mesh.
			# """,

			# "preset:Unchanged" : "",
			# "preset:Polygon" : "linear",
			# "preset:Subdivision Surface" : "catmullClark",

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:NonPeriodic" : IECoreScene.CurvesPrimitive.Wrap.NonPeriodic,
			"preset:Periodic" : IECoreScene.CurvesPrimitive.Wrap.Periodic,
			"preset:Pinned" : IECoreScene.CurvesPrimitive.Wrap.Pinned,

		},

		"expandPinned" : {

			"layout:activator" : lambda plug : plug.parent()["wrap"]["enabled"].getValue() and plug.parent()["wrap"]["value"].getValue() == IECoreScene.CurvesPrimitive.Wrap.NonPeriodic,

		},

		"basis.value" : {

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:Linear" : IECore.StandardCubicBasis.Linear,
			"preset:BSpline" : IECore.StandardCubicBasis.BSpline,
			"preset:CatmullRom" : IECore.StandardCubicBasis.CatmullRom,

		},

	}

)
