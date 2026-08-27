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

import os

import IECore

import Gaffer
import GafferSceneUI

# Register attribute columns for all attributes we have metadata for.
## \todo Potentially the AttributeEditor should just do this itself automatically.

for target in Gaffer.Metadata.targetsWithMetadata( "attribute:*", "defaultValue" ) :

	if target == "attribute:scene:visible" :
		# This attribute is represented by a dedicated VisibilityColumn
		# so doesn't require registration.
		continue

	category = Gaffer.Metadata.value( target, "category" )
	if not category :
		continue

	section = Gaffer.Metadata.value( target, "layout:section" )
	if section :
		# AttributeEditor doesn't support nested sections, so just take
		# the top-level section.
		section = section.partition( "." )[0]

	GafferSceneUI.AttributeEditor.registerAttribute(
		category, target[10:], section, Gaffer.Metadata.value( target, "label" )
	)

# Register `tabGroup` presets to allow the user to switch between the categories.
## \todo Potentially the AttributeEditor should just do this itself automatically.
# For now the manual registration is somewhat useful in that it allows us to avoid
# exposing renderers that aren't available.
## \todo Consider renaming the `tabGroup` plug to `category`.

Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "preset:Standard", "Standard" )
Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "userDefault", "Standard" )

Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "preset:USD", "USD" )

with IECore.IgnoredExceptions( ImportError ) :
	import GafferArnold
	Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "preset:Arnold", "Arnold" )

if os.environ.get( "CYCLES_ROOT" ) and os.environ.get( "GAFFERCYCLES_HIDE_UI", "" ) != "1" :
	Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "preset:Cycles", "Cycles" )

with IECore.IgnoredExceptions( ImportError ) :
	import GafferDelight
	Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "preset:3Delight", "3Delight" )

if os.environ.get( "GAFFERRENDERMAN_HIDE_UI", "" ) != "1" :

	with IECore.IgnoredExceptions( ImportError ) :
		import GafferRenderMan
		Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "preset:RenderMan", "RenderMan" )

Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "preset:OpenGL", "OpenGL" )
