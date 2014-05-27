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

## \todo This is getting used in a few places now - maybe put it in one
# place? Maybe a static method on NumericWidget?
def __floatToString( f ) :

	return ( "%.4f" % f ).rstrip( '0' ).rstrip( '.' )

def __cameraSummary( plug ) :

	info = []
	if plug["renderCamera"]["enabled"].getValue() :
		info.append( plug["renderCamera"]["value"].getValue() )
	if plug["renderResolution"]["enabled"].getValue() :
		resolution = plug["renderResolution"]["value"].getValue()
		info.append( "%dx%d" % ( resolution[0], resolution[1] ) )
	if plug["renderCropWindow"]["enabled"].getValue() :
		crop = plug["renderCropWindow"]["value"].getValue()
		info.append( "Crop %s,%s-%s,%s" % tuple( __floatToString( x ) for x in ( crop.min.x, crop.min.y, crop.max.x, crop.max.y ) ) )

	return ", ".join( info )
	
def __motionBlurSummary( plug ) :

	info = []
	if plug["cameraBlur"]["enabled"].getValue() :
		info.append( "Camera " + ( "On" if plug["cameraBlur"]["value"].getValue() else "Off" ) )
	if plug["transformBlur"]["enabled"].getValue() :
		info.append( "Transform " + ( "On" if plug["transformBlur"]["value"].getValue() else "Off" ) )
	if plug["deformationBlur"]["enabled"].getValue() :
		info.append( "Deformation " + ( "On" if plug["deformationBlur"]["value"].getValue() else "Off" ) )
	if plug["shutter"]["enabled"].getValue() :
		info.append( "Shutter " + str( plug["shutter"]["value"].getValue() ) )
		
	return ", ".join( info )	

GafferUI.PlugValueWidget.registerCreator(
	
	GafferScene.StandardOptions.staticTypeId(),
	"options",
	GafferUI.SectionedCompoundDataPlugValueWidget,
	sections = (
		
		{
			"label" : "Camera",
			"summary" : __cameraSummary,
			"namesAndLabels" : (
				( "render:camera", "Camera" ),
				( "render:resolution", "Resolution" ),
				( "render:cropWindow", "Crop Window" ),
			),
		},
		
		{
			"label" : "Motion Blur",
			"summary" : __motionBlurSummary,
			"namesAndLabels" : (
				( "render:cameraBlur", "Camera" ),
				( "render:transformBlur", "Transform" ),
				( "render:deformationBlur", "Deformation" ),
				( "render:shutter", "Shutter" ),
			),
		},
		
	),
	
)

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.StandardOptions.staticTypeId(),
	"options.renderCamera.value",
	lambda plug : GafferUI.PathPlugValueWidget(
		plug,
		path = GafferScene.ScenePath( plug.node()["in"], plug.node().scriptNode().context(), "/" ),
	),
)
