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

import IECore

import Gaffer

Gaffer.Metadata.registerValue( "attribute:dl:visibility.camera", "label", "Camera" )
Gaffer.Metadata.registerValue( "attribute:dl:visibility.camera", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:dl:visibility.camera",
	"description",
	"""
	Whether or not the object is visible to camera
	rays. To hide an object completely, use the
	`scene:visible` attribute instead.
	""",
)

Gaffer.Metadata.registerValue( "attribute:dl:visibility.diffuse", "label", "Diffuse" )
Gaffer.Metadata.registerValue( "attribute:dl:visibility.diffuse", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:dl:visibility.diffuse",
	"description",
	"""
	Whether or not the object is visible to diffuse
	rays.
	""",
)

Gaffer.Metadata.registerValue( "attribute:dl:visibility.hair", "label", "Hair" )
Gaffer.Metadata.registerValue( "attribute:dl:visibility.hair", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:dl:visibility.hair",
	"description",
	"""
	Whether or not the object is visible to
	hair rays.
	""",
)

Gaffer.Metadata.registerValue( "attribute:dl:visibility.reflection", "label", "Reflection" )
Gaffer.Metadata.registerValue( "attribute:dl:visibility.reflection", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:dl:visibility.reflection",
	"description",
	"""
	Whether or not the object is visible in
	reflections.
	""",
)

Gaffer.Metadata.registerValue( "attribute:dl:visibility.refraction", "label", "Refraction" )
Gaffer.Metadata.registerValue( "attribute:dl:visibility.refraction", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:dl:visibility.refraction",
	"description",
	"""
	Whether or not the object is visible in
	refractions.
	""",
)

Gaffer.Metadata.registerValue( "attribute:dl:visibility.shadow", "label", "Shadow" )
Gaffer.Metadata.registerValue( "attribute:dl:visibility.shadow", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:dl:visibility.shadow",
	"description",
	"""
	Whether or not the object is visible to shadow
	rays - whether it casts shadows or not.
	""",
)

Gaffer.Metadata.registerValue( "attribute:dl:visibility.specular", "label", "Specular" )
Gaffer.Metadata.registerValue( "attribute:dl:visibility.specular", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:dl:visibility.specular",
	"description",
	"""
	Whether or not the object is visible to
	specular rays.
	""",
)

Gaffer.Metadata.registerValue( "attribute:dl:matte", "label", "Matte" )
Gaffer.Metadata.registerValue( "attribute:dl:matte", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:dl:matte",
	"description",
	"""
	Turns the object into a holdout matte.
	This only affects primary (camera) rays.
	""",
)
