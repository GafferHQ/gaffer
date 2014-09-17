##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import fnmatch

import Gaffer
import GafferUI
import GafferImageUI
import GafferImage

# ImageNode
def __noduleCreator( plug ) :

	if isinstance( plug, GafferImage.ImagePlug ) :
		return GafferUI.StandardNodule( plug )

	return None

GafferUI.Nodule.registerNodule( GafferImage.ImageNode, fnmatch.translate( "*" ), __noduleCreator )
GafferUI.PlugValueWidget.registerType( GafferImage.ImagePlug, None )

Gaffer.Metadata.registerPlugValue( GafferImage.ImageNode, "enabled", "nodeUI:section", "Node" )

# ImageStats
GafferUI.PlugValueWidget.registerCreator( GafferImage.ImageStats, "channels", GafferImageUI.ChannelMaskPlugValueWidget, inputImagePlug = "in" )
GafferUI.Nodule.registerNodule( GafferImage.ImageStats, "channels", __noduleCreator )

# ChannelDataProcessor
GafferUI.PlugValueWidget.registerCreator( GafferImage.ImageNode, "channels", GafferImageUI.ChannelMaskPlugValueWidget, inputImagePlug = "in" )

# ImageReader
GafferUI.PlugValueWidget.registerCreator(
	GafferImage.ImageReader,
	"fileName",
	lambda plug : GafferUI.PathPlugValueWidget( plug,
		path = Gaffer.FileSystemPath(
			"/",
			filter = Gaffer.FileSystemPath.createStandardFilter(
				extensions = GafferImage.ImageReader.supportedExtensions(),
				extensionsLabel = "Show only image files",
			)
		),
		pathChooserDialogueKeywords = {
			"bookmarks" : GafferUI.Bookmarks.acquire( plug, category = "image" ),
			"leaf" : True,
		},
	)
)

# ImageWriter

GafferUI.PlugValueWidget.registerCreator(
	GafferImage.ImageWriter,
	"fileName",
	lambda plug : GafferUI.PathPlugValueWidget( plug,
		path = Gaffer.FileSystemPath(
			"/",
			filter = Gaffer.FileSystemPath.createStandardFilter(
				extensions = GafferImage.ImageReader.supportedExtensions(),
				extensionsLabel = "Show only image files",
			)
		),
		pathChooserDialogueKeywords = {
			"bookmarks" : GafferUI.Bookmarks.acquire( plug, category = "image" ),
			"leaf" : True,
		},
	)
)
GafferUI.PlugValueWidget.registerCreator( GafferImage.ImageWriter, "channels", GafferImageUI.ChannelMaskPlugValueWidget, inputImagePlug = "in" )
GafferUI.Nodule.registerNodule( GafferImage.ImageWriter, "fileName", lambda plug : None )
GafferUI.Nodule.registerNodule( GafferImage.ImageWriter, "channels", lambda plug : None )
GafferUI.Nodule.registerNodule( GafferImage.ImageWriter, "writeMode", lambda plug : None )
GafferUI.Nodule.registerNodule( GafferImage.ImageWriter, "out", lambda plug : None )

writeModeLabelsAndValues = [ ( "Scanline", 0), ( "Tile", 1 ) ]

GafferUI.PlugValueWidget.registerCreator(
	GafferImage.ImageWriter,
	"writeMode",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = writeModeLabelsAndValues
)

# Constant
GafferUI.PlugValueWidget.registerCreator(
	GafferImage.Constant,
	"format",
	GafferImageUI.FormatPlugValueWidget
)

# OpenColorIO
ocioColorSpaceLabelsAndValues = [ ( "None", "" ) ]
import PyOpenColorIO as OCIO
config = OCIO.GetCurrentConfig()
for cs in config.getColorSpaces() :
	ocioColorSpaceLabelsAndValues.append( ( cs.getName(), cs.getName() ) )

GafferUI.PlugValueWidget.registerCreator(
	GafferImage.OpenColorIO,
	"inputSpace",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = ocioColorSpaceLabelsAndValues
)

GafferUI.PlugValueWidget.registerCreator(
	GafferImage.OpenColorIO,
	"outputSpace",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = ocioColorSpaceLabelsAndValues
)

# Merge
mergeOperationLabelsAndValues = [ ( "Add", 0 ), ( "Atop", 1 ), ( "Divide", 2 ), ( "In", 3 ), ( "Out", 4 ), ( "Mask", 5 ), ( "Matte", 6 ), ( "Multiply", 7 ), ( "Over", 8 ), ( "Subtract", 9 ), ( "Under", 10 ) ]
GafferUI.PlugValueWidget.registerCreator(
	GafferImage.Merge,
	"operation",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = mergeOperationLabelsAndValues
)

# Remove Channels
removeChannelsLabelsAndValues = [ ( "Remove", 0 ), ( "Keep", 1 ) ]
GafferUI.PlugValueWidget.registerCreator(
	GafferImage.RemoveChannels,
	"mode",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = removeChannelsLabelsAndValues
)


