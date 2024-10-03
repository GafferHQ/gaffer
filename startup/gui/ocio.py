##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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
import GafferUI
import GafferImage
import GafferImageUI

# Make sure every script has a config plug added to it, and that we update
# the View and Widget display transforms appropriately when the config is changed.

def __scriptAdded( container, script ) :

	GafferImageUI.OpenColorIOConfigPlugUI.connect( script )

application.root()["scripts"].childAddedSignal().connect( __scriptAdded )

Gaffer.Metadata.registerValue( GafferUI.View, "displayTransform.name", "plugValueWidget:type", "GafferImageUI.OpenColorIOConfigPlugUI.DisplayTransformPlugValueWidget" )
Gaffer.Metadata.registerValue( GafferUI.View, "displayTransform.name", "layout:minimumWidth", 150 )

# Add "Roles" submenus to various colorspace plugs. The OCIO UX guidelines suggest we
# shouldn't do this, but they do seem like they might be useful, and historically they
# have been available in Gaffer. They can be disabled by overwriting the metadata in
# a custom config file.

for node, plug in [
	( GafferImage.ColorSpace, "inputSpace" ),
	( GafferImage.ColorSpace, "outputSpace" ),
	( GafferImage.DisplayTransform, "inputColorSpace" ),
	( GafferImage.ImageReader, "colorSpace" ),
	( GafferImage.ImageWriter, "colorSpace" ),
] :
	Gaffer.Metadata.registerValue( node, plug, "openColorIO:includeRoles", True )

# Set up Arnold colour manager with metadata that integrates with our OCIO configs.

with IECore.IgnoredExceptions( ImportError ) :

	import GafferArnold

	Gaffer.Metadata.registerValue( GafferArnold.ArnoldColorManager, "parameters.config", "userDefault", "${ocio:config}" )

	Gaffer.Metadata.registerValue( GafferArnold.ArnoldColorManager, "parameters.config", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
	Gaffer.Metadata.registerValue( GafferArnold.ArnoldColorManager, "parameters.config", "preset:$OCIO", "" )
	Gaffer.Metadata.registerValue( GafferArnold.ArnoldColorManager, "parameters.config", "preset:ACES 1.3 - CG Config", "ocio://cg-config-v1.0.0_aces-v1.3_ocio-v2.1" )
	Gaffer.Metadata.registerValue( GafferArnold.ArnoldColorManager, "parameters.config", "preset:ACES 1.3 - Studio Config", "ocio://studio-config-v1.0.0_aces-v1.3_ocio-v2.1" )
	Gaffer.Metadata.registerValue( GafferArnold.ArnoldColorManager, "parameters.config", "preset:Legacy (Gaffer 1.2)", "${GAFFER_ROOT}/openColorIO/config.ocio" )

	Gaffer.Metadata.registerValue( GafferArnold.ArnoldColorManager, "parameters.config", "presetsPlugValueWidget:allowCustom", True )
	Gaffer.Metadata.registerValue( GafferArnold.ArnoldColorManager, "parameters.config", "presetsPlugValueWidget:customWidgetType", "GafferUI.FileSystemPathPlugValueWidget" )
	Gaffer.Metadata.registerValue( GafferArnold.ArnoldColorManager, "parameters.config", "fileSystemPath:extensions", "ocio" )
	Gaffer.Metadata.registerValue( GafferArnold.ArnoldColorManager, "parameters.config", "path:leaf", True )
	Gaffer.Metadata.registerValue( GafferArnold.ArnoldColorManager, "parameters.config", "path:valid", True )

	Gaffer.Metadata.registerValue( GafferArnold.ArnoldColorManager, "parameters.color_space_linear", "userDefault", "${ocio:workingSpace}" )
	Gaffer.Metadata.registerValue( GafferArnold.ArnoldColorManager, "parameters.color_space_linear", "preset:Working Space", "${ocio:workingSpace}" )

	Gaffer.Metadata.registerValue( GafferArnold.ArnoldColorManager, "parameters.color_space_narrow", "userDefault", "matte_paint" )
