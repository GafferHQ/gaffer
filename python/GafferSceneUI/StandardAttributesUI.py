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
import GafferScene

def __attributesSummary( plug ) :

	info = []
	if plug["visibility"]["enabled"].getValue() :
		info.append( "Visible" if plug["visibility"]["value"].getValue() else "Invisible" )
	if plug["doubleSided"]["enabled"].getValue() :
		info.append( "Double Sided" if plug["doubleSided"]["value"].getValue() else "Single Sided" )
			
	return ", ".join( info )

def __motionBlurSummary( plug ) :

	info = []
	for motionType in "transform", "deformation" :
		onOffEnabled = plug[motionType+"Blur"]["enabled"].getValue()
		segmentsEnabled = plug[motionType+"BlurSegments"]["enabled"].getValue()
		if onOffEnabled or segmentsEnabled :
			items = []
			if onOffEnabled :
				items.append( "On" if plug[motionType+"Blur"]["value"].getValue() else "Off" )
			if segmentsEnabled :
				items.append( "%d Segments" % plug[motionType+"BlurSegments"]["value"].getValue() )
			info.append( motionType.capitalize() + " : " + "/".join( items ) )
		
	return ", ".join( info )
	
GafferUI.PlugValueWidget.registerCreator(
	
	GafferScene.StandardAttributes.staticTypeId(),
	"attributes",
	GafferUI.SectionedCompoundDataPlugValueWidget,
	sections = (
	
		{
			"label" : "Attributes",
			"summary" : __attributesSummary,
			"namesAndLabels" : (
				( "scene:visible", "Visibility" ),
				( "doubleSided", "Double Sided" ),
			),
		},
		
		{
			"label" : "Motion Blur",
			"summary" : __motionBlurSummary,
			"namesAndLabels" : (
				( "gaffer:transformBlur", "Transform" ),
				( "gaffer:transformBlurSegments", "Transform Segments" ),
				( "gaffer:deformationBlur", "Deformation" ),
				( "gaffer:deformationBlurSegments", "Deformation Segments" ),
			),
		},
		
	),

)
