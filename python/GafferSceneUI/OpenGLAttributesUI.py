##########################################################################
#  
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

GafferUI.PlugValueWidget.registerCreator(
	
	GafferScene.OpenGLAttributes.staticTypeId(),
	"attributes",
	GafferUI.SectionedCompoundDataPlugValueWidget,
	sections = (
	
		(
			"Drawing",
			(
				( "gl:primitive:solid", "Shaded" ),
				
				( "gl:primitive:wireframe", "Wireframe" ),
				( "gl:primitive:wireframeColor", "Wireframe Color" ),
				( "gl:primitive:wireframeWidth", "Wireframe Width" ),
				
				( "gl:primitive:outline", "Outline" ),
				( "gl:primitive:outlineColor", "Outline Color" ),
				( "gl:primitive:outlineWidth", "Outline Width" ),
				
				( "gl:primitive:points", "Points" ),
				( "gl:primitive:pointColor", "Point Color" ),
				( "gl:primitive:pointWidth", "Point Width" ),
				
				( "gl:primitive:bound", "Bound" ),
				( "gl:primitive:boundColor", "Bound Color" ),
				
			),
		),
		
		(
			"Points Primitives",
			(
				( "gl:pointsPrimitive:useGLPoints", "Use GL Points" ),
				( "gl:pointsPrimitive:glPointWidth", "GL Point Width" ),
			),
		),
		
		(
			"Curves Primitives",
			(
				( "gl:curvesPrimitive:useGLLines", "Use GL Lines" ),
				( "gl:curvesPrimitive:glLineWidth", "GL Line Width" ),
				( "gl:curvesPrimitive:ignoreBasis", "Ignore Basis" ),
			),
		),
		
	),	
	
)

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.OpenGLAttributes.staticTypeId(),
	"attributes.pointsPrimitiveUseGLPoints.value",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "For GL Points", "forGLPoints" ),
		( "For Particles And Disks", "forParticlesAndDisks" ),
		( "For All", "forAll" ),
	),
)
