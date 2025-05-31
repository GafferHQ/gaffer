##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

Gaffer.Metadata.registerValues( {

	"attribute:dl:visibility.camera" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible to camera
		rays. To hide an object completely, use the
		`scene:visible` attribute instead.
		""",
		"label", "Camera",
		"layout:section", "Visibility",

	],

	"attribute:dl:visibility.diffuse" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible to diffuse
		rays.
		""",
		"label", "Diffuse",
		"layout:section", "Visibility",

	],

	"attribute:dl:visibility.hair" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible to
		hair rays.
		""",
		"label", "Hair",
		"layout:section", "Visibility",

	],

	"attribute:dl:visibility.reflection" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible in
		reflections.
		""",
		"label", "Reflection",
		"layout:section", "Visibility",

	],

	"attribute:dl:visibility.refraction" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible in
		refractions.
		""",
		"label", "Refraction",
		"layout:section", "Visibility",

	],

	"attribute:dl:visibility.shadow" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible to shadow
		rays - whether it casts shadows or not.
		""",
		"label", "Shadow",
		"layout:section", "Visibility",

	],

	"attribute:dl:visibility.specular" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible to
		specular rays.
		""",
		"label", "Specular",
		"layout:section", "Visibility",

	],

	"attribute:dl:matte" : [

		"defaultValue", False,
		"description",
		"""
		Turns the object into a holdout matte.
		This only affects primary (camera) rays.
		""",
		"label", "Matte",
		"layout:section", "Shading",

	],

} )
