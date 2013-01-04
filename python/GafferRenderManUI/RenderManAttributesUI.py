##########################################################################
#  
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import GafferUI
import GafferRenderMan

GafferUI.PlugValueWidget.registerCreator(
	
	GafferRenderMan.RenderManAttributes.staticTypeId(),
	"attributes",
	GafferUI.SectionedCompoundDataPlugValueWidget,
	sections = (
		
		(
			"Visibility",
			(
				( "ri:visibility:camera", "Camera" ),
				( "ri:shade:camerahitmode", "Camera Mode" ),
				
				( "ri:visibility:transmission", "Transmission" ),
				( "ri:shade:transmissionhitmode", "Transmission Mode" ),
				
				( "ri:visibility:diffuse", "Diffuse" ),
				( "ri:shade:diffusehitmode", "Diffuse Mode" ),
				
				( "ri:visibility:specular", "Specular" ),
				( "ri:shade:specularhitmode", "Specular Mode" ),
				
				( "ri:visibility:photon", "Photon" ),
				( "ri:shade:photonhitmode", "Photon Mode" ),
			),
		),
		
	),	
	
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManAttributes.staticTypeId(),
	"attributes.cameraHitMode.value",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "Shader", "shader" ),
		( "Primitive", "primitive" ),
	),
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManAttributes.staticTypeId(),
	"attributes.transmissionHitMode.value",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "Shader", "shader" ),
		( "Primitive", "primitive" ),
	),
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManAttributes.staticTypeId(),
	"attributes.diffuseHitMode.value",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "Shader", "shader" ),
		( "Primitive", "primitive" ),
	),
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManAttributes.staticTypeId(),
	"attributes.specularHitMode.value",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "Shader", "shader" ),
		( "Primitive", "primitive" ),
	),
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManAttributes.staticTypeId(),
	"attributes.photonHitMode.value",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "Shader", "shader" ),
		( "Primitive", "primitive" ),
	),
)
