##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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
import GafferScene
from GafferUI.i18n import _

__modePresets = {
	"preset:Euler" : GafferScene.Orientation.Mode.Euler,
	"preset:Quaternion" : GafferScene.Orientation.Mode.Quaternion,
	"preset:Axis-Angle" : GafferScene.Orientation.Mode.AxisAngle,
	"preset:Aim" : GafferScene.Orientation.Mode.Aim,
	"preset:Matrix" : GafferScene.Orientation.Mode.Matrix,
}

__eulerOrderPresets = {
	"preset:XYZ" : imath.Eulerf.XYZ,
	"preset:XZY" : imath.Eulerf.XZY,
	"preset:YZX" : imath.Eulerf.YZX,
	"preset:YXZ" : imath.Eulerf.YXZ,
	"preset:ZXY" : imath.Eulerf.ZXY,
	"preset:ZYX" : imath.Eulerf.ZYX,
}

Gaffer.Metadata.registerNode(

	GafferScene.Orientation,

	"description",
	_("""
	Converts between different representations of orientation, stored as
	primitive variables on an object. Supported representations include
	euler angles, quaternions, axis-angle form, aim vectors and matrices.

	Typically used to prepare points for instancing, as the Instancer node
	requires orientation to be provided as a quaternion, but it is often
	more convenient to prepare orientations in another representation.
	"""),

	"layout:activator:inModeIsEuler", lambda node : node["inMode"].getValue() == GafferScene.Orientation.Mode.Euler,
	"layout:activator:inModeIsQuaternion", lambda node : node["inMode"].getValue() in ( GafferScene.Orientation.Mode.Quaternion, GafferScene.Orientation.Mode.QuaternionXYZW ),
	"layout:activator:inModeIsAxisAngle", lambda node : node["inMode"].getValue() == GafferScene.Orientation.Mode.AxisAngle,
	"layout:activator:inModeIsAim", lambda node : node["inMode"].getValue() == GafferScene.Orientation.Mode.Aim,
	"layout:activator:inModeIsMatrix", lambda node : node["inMode"].getValue() == GafferScene.Orientation.Mode.Matrix,

	"layout:activator:outModeIsEuler", lambda node : node["outMode"].getValue() == GafferScene.Orientation.Mode.Euler,
	"layout:activator:outModeIsQuaternion", lambda node : node["outMode"].getValue() == GafferScene.Orientation.Mode.Quaternion,
	"layout:activator:outModeIsAxisAngle", lambda node : node["outMode"].getValue() == GafferScene.Orientation.Mode.AxisAngle,
	"layout:activator:outModeIsAim", lambda node : node["outMode"].getValue() == GafferScene.Orientation.Mode.Aim,
	"layout:activator:outModeIsMatrix", lambda node : node["outMode"].getValue() == GafferScene.Orientation.Mode.Matrix,

	"layout:activator:randomEnabled", lambda node : node["randomEnabled"].getValue(),

	"layout:section:Settings.Input:collapsed", False,
	"layout:section:Settings.Input:summary", lambda node : str( node.Mode.values[node["inMode"].getValue()] ),
	"layout:section:Settings.Random:summary", lambda node : "On" if node["randomEnabled"].getValue() else "Off",
	"layout:section:Settings.Output:summary", lambda node : str( node.Mode.values[node["outMode"].getValue()] ),

	plugs = {

		# Input
		# =====

		"inMode" : {

			"description" :
			_("""
			The method used to define the input orientations.
			"""),

			"layout:section" : "Settings.Input",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

		} | __modePresets | {

			"preset:Quaternion XYZW (Houdini)" : GafferScene.Orientation.Mode.QuaternionXYZW,

		},

		"deleteInputs" : {

			"description" :
			_("""
			Deletes the input primitive variables, so that they are
			not present on the output object.
			"""),

			"label" : _("Delete"),
			"layout:section" : "Settings.Input",
			"layout:index" : -1,

		},

		# Euler
		# -----

		"inEuler" : {

			"description" :
			_("""
			Name of the primitive variable that defines the input orientation
			as euler angles, measured in degrees. This variable should contain
			V3fVectorData.
			"""),

			"label" : _("Euler"),
			"layout:section" : "Settings.Input",
			"layout:visibilityActivator" : "inModeIsEuler",

		},

		"inOrder" : {

			"description" :
			_("""
			The rotation order of the input euler angles.
			"""),

			"label" : _("Order"),
			"layout:section" : "Settings.Input",
			"layout:visibilityActivator" : "inModeIsEuler",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

		} | __eulerOrderPresets,

		# Quaternion
		# ----------

		"inQuaternion" : {

			"description" :
			_("""
			Name of the primitive variable that defines the input orientation
			as quaternions. This variable should contain QuatfVectorData.
			"""),

			"label" : _("Quaternion"),

			"layout:section" : "Settings.Input",
			"layout:visibilityActivator" : "inModeIsQuaternion",

		},

		# Axis Angle
		# ----------

		"inAxis" : {

			"description" :
			_("""
			Name of the primitive variable that defines the axis component of
			the input orientations. This variable should contain V3fVectorData.
			"""),

			"label" : _("Axis"),

			"layout:section" : "Settings.Input",
			"layout:visibilityActivator" : "inModeIsAxisAngle",

		},

		"inAngle" : {

			"description" :
			_("""
			Name of the primitive variable that defines the angle component of
			the input orientations. This variable should contain FloatVectorData.
			"""),

			"label" : _("Angle"),

			"layout:section" : "Settings.Input",
			"layout:visibilityActivator" : "inModeIsAxisAngle",

		},

		# Aim
		# ---

		"inXAxis" : {

			"description" :
			_("""
			Name of the primitive variable that defines the direction in which the
			X axis will be aimed. This variable should contain V3fVectorData.
			"""),

			"label" : _("X Axis"),

			"layout:section" : "Settings.Input",
			"layout:visibilityActivator" : "inModeIsAim",

		},

		"inYAxis" : {

			"description" :
			_("""
			Name of the primitive variable that defines the direction in which the
			Y axis will be aimed. This variable should contain V3fVectorData.
			"""),

			"label" : _("Y Axis"),

			"layout:section" : "Settings.Input",
			"layout:visibilityActivator" : "inModeIsAim",

		},

		"inZAxis" : {

			"description" :
			_("""
			Name of the primitive variable that defines the direction in which the
			Z axis will be aimed. This variable should contain V3fVectorData.
			"""),

			"label" : _("Z Axis"),

			"layout:section" : "Settings.Input",
			"layout:visibilityActivator" : "inModeIsAim",

		},

		# Matrix
		# ------

		"inMatrix" : {

			"description" :
			_("""
			Name of the primitive variable that defines the input orientations as
			a matrix. This variable should contain M33fVectorData.
			"""),

			"label" : _("Matrix"),

			"layout:section" : "Settings.Input",
			"layout:visibilityActivator" : "inModeIsMatrix",

		},

		# Randomisation
		# =============

		"randomEnabled" : {

			"description" :
			_("""
			Enables randomisation of the orientations. Randomisation
			is applied as a pre-transform of the input orientation.
			"""),

			"layout:section" : "Settings.Random",
			"label" : _("Enabled"),

		},

		"randomAxis" : {

			"description" :
			_("""
			A reference axis which the randomisation is specified relative
			to. Typically this would be the primary axis of the model being
			instanced.
			"""),

			"preset:X" : imath.V3f( 1, 0, 0 ),
			"preset:Y" : imath.V3f( 0, 1, 0 ),
			"preset:Z" : imath.V3f( 0, 0, 1 ),

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"presetsPlugValueWidget:allowCustom" : True,

			"layout:section" : "Settings.Random",
			"label" : _("Axis"),
			"layout:activator" : "randomEnabled",

		},

		"randomSpread" : {

			"description" :
			_("""
			Applies a random rotation away from the axis, specified in
			degrees. The maximum spread of 180 degrees gives a uniform
			randomisation over all possible directions.
			"""),

			"layout:section" : "Settings.Random",
			"label" : _("Spread"),
			"layout:activator" : "randomEnabled",

		},

		"randomTwist" : {

			"description" :
			_("""
			Applies a random rotation around the axis, specified in
			degrees.
			"""),

			"layout:section" : "Settings.Random",
			"label" : _("Twist"),
			"layout:activator" : "randomEnabled",

		},

		"randomSpace" : {

			"description" :
			_("""
			The space in which the randomisation is specified. This defines
			how it is combined with the input orientations.

			Local
			:	The randomisation is specified in local space and
				is therefore post-multiplied onto the input orientations.
				When using the Instancer, this is equivalent to randomising
				the prototypes before they are instanced.

			Parent
			:	The transformation is specified in parent space and
				is therefore pre-multiplied onto the input orientations.
				When using the Instancer, this is equivalent to randomising
				the instances after they are positioned.

			"""),

			"layout:section" : "Settings.Random",
			"label" : _("Space"),
			"preset:Local" : GafferScene.Orientation.Space.Local,
			"preset:Parent" : GafferScene.Orientation.Space.Parent,
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

		},

		# Output
		# ======

		"outMode" : {

			"description" :
			_("""
			The method used to define the output orientations. When
			creating orientations for the Instancer, the Quaternion
			mode should be used.
			"""),

			"layout:section" : "Settings.Output",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

		} | __modePresets,

		# Euler
		# -----

		"outEuler" : {

			"description" :
			_("""
			Name of the primitive variable that will be created to store
			the output orientations as euler angles, measured in degrees.
			"""),

			"label" : _("Euler"),
			"layout:section" : "Settings.Output",
			"layout:visibilityActivator" : "outModeIsEuler",

		},

		"outOrder" : {

			"description" :
			_("""
			The rotation order of the output euler angles.
			"""),

			"label" : _("Order"),

			"layout:section" : "Settings.Output",
			"layout:visibilityActivator" : "outModeIsEuler",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

		} | __eulerOrderPresets,

		# Quaternion
		# ----------

		"outQuaternion" : {

			"description" :
			_("""
			Name of the primitive variable that will be created to store
			the output orientations as quaternions.
			"""),

			"label" : _("Quaternion"),
			"layout:section" : "Settings.Output",
			"layout:visibilityActivator" : "outModeIsQuaternion",

		},

		# Axis Angle
		# ----------

		"outAxis" : {

			"description" :
			_("""
			Name of the primitive variable that will be created to store
			the axis component of the output orientation.
			"""),

			"label" : _("Axis"),
			"layout:section" : "Settings.Output",
			"layout:visibilityActivator" : "outModeIsAxisAngle",

		},

		"outAngle" : {

			"description" :
			_("""
			Name of the primitive variable that will be created to store
			the angle component of the output orientation.
			"""),

			"label" : _("Angle"),
			"layout:section" : "Settings.Output",
			"layout:visibilityActivator" : "outModeIsAxisAngle",

		},

		# Aim
		# ---

		"outXAxis" : {

			"description" :
			_("""
			Name of the primitive variable that will be created to store
			the x-axis aim vector of the output orientation.
			"""),

			"label" : _("X Axis"),
			"layout:section" : "Settings.Output",
			"layout:visibilityActivator" : "outModeIsAim",

		},

		"outYAxis" : {

			"description" :
			_("""
			Name of the primitive variable that will be created to store
			the y-axis aim vector of the output orientation.
			"""),

			"label" : _("Y Axis"),
			"layout:section" : "Settings.Output",
			"layout:visibilityActivator" : "outModeIsAim",

		},

		"outZAxis" : {

			"description" :
			_("""
			Name of the primitive variable that will be created to store
			the z-axis aim vector of the output orientation.
			"""),

			"label" : _("Z Axis"),
			"layout:section" : "Settings.Output",
			"layout:visibilityActivator" : "outModeIsAim",

		},

		# Matrix
		# ------

		"outMatrix" : {

			"description" :
			_("""
			Name of the primitive variable that will be created to store
			the output orientations as matrices. The matrices will be
			stored as M33fVectorData.
			"""),

			"label" : _("Matrix"),
			"layout:section" : "Settings.Output",
			"layout:visibilityActivator" : "outModeIsMatrix",

		},

	}

)
