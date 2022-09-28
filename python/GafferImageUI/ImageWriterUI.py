##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import GafferUI
import GafferImageUI
import GafferImage
from . import OpenColorIOTransformUI

layoutVariableDesc = """
			Special context variables available for setting layout plugs:

			* `${imageWriter:viewName}` : The current view
			* `${imageWriter:channelName}` : The current channel name
			* `${imageWriter:layerName}` : The prefix of the channel name
			* `${imageWriter:baseName}` : The suffix of the channel name
			* `${imageWriter:standardPartName}` : Like the layerName, but set to "rgba" instead of empty for the main layer
			* `${imageWriter:nukeViewName}` : Like viewName, but set to "main" when there is no current view
			* `${imageWriter:nukeLayerName}` : Like layerName, but set to "depth" for "Z", and "other" for custom channels of the main layer
			* `${imageWriter:nukeBaseName}` : Like baseName, but set to "red", "green", "blue", "alpha" instead of RGBA for layers other than the main layer.
			* `${imageWriter:nukePartName}` : Like standardPartName, but set to "depth" for "Z", and "other" for custom channels of the main layer
			* `${imageWriter:singlePartViewName}` : The current view, or "" if this is the first view. This should be used to compose channel names for single-part multi-view EXR files.

"""

def __extension( parent ) :

	fileNamePlug = parent["fileName"]
	fileName = fileNamePlug.getValue()
	ext = os.path.splitext( fileName )[1]
	if ext :
		return ext.lower()[1:]
	return "" if fileNamePlug.isSetToDefault() else "unknown"

Gaffer.Metadata.registerNode(

	GafferImage.ImageWriter,

	"description",
	"""
	Writes image files to disk using OpenImageIO. All file
	types supported by OpenImageIO are supported by the
	ImageWriter.
	""",

	"layout:activator:dpx", lambda p : __extension( p ) in ( "dpx", "unknown" ),
	"layout:activator:field3d", lambda p : __extension( p ) in ( "f3d", "unknown" ),
	"layout:activator:fits", lambda p : __extension( p ) in ( "fits", "unknown" ),
	"layout:activator:iff", lambda p : __extension( p ) in ( "iff", "unknown" ),
	"layout:activator:jpeg", lambda p : __extension( p ) in ( "jpg", "jpe", "jpeg", "jif", "jfif", "jfi", "unknown" ),
	"layout:activator:jpeg2000", lambda p : __extension( p ) in ( "jp2", "j2k", "unknown" ),
	"layout:activator:openexr", lambda p : __extension( p ) in ( "exr", "unknown" ),
	"layout:activator:png", lambda p : __extension( p ) in ( "png", "unknown" ),
	"layout:activator:rla", lambda p : __extension( p ) in ( "rla", "unknown" ),
	"layout:activator:sgi", lambda p : __extension( p ) in ( "sgi", "rgb", "rgba", "bw", "int", "inta", "unknown" ),
	"layout:activator:targa", lambda p : __extension( p ) in ( "tga", "unknown" ),
	"layout:activator:tiff", lambda p : __extension( p ) in ( "tif", "tiff", "unknown" ),
	"layout:activator:webp", lambda p : __extension( p ) in ( "webp", "unknown" ),

	plugs = {

		"in" : [

			"description",
			"""
			The image to be written to disk.
			""",

			"nodule:type", "GafferUI::StandardNodule",

		],

		"fileName" : [

			"description",
			"""
			The name of the file to be written. File sequences with
			arbitrary padding may be specified using the '#' character
			as a placeholder for the frame numbers.
			""",

			"path:leaf", True,
			"path:bookmarks", "image",
			"fileSystemPath:extensions", " ".join( GafferImage.ImageReader.supportedExtensions() ),
			"fileSystemPath:extensionsLabel", "Show only image files",
			"fileSystemPath:includeSequences", True,

		],

		"channels" : [

			"description",
			"""
			The names of the channels to be written to the file.
			Names should be separated by spaces and may contain any
			of Gaffer's standard wildcards.
			""",

			"plugValueWidget:type", "GafferImageUI.ChannelMaskPlugValueWidget",

		],

		"colorSpace" : [

			"description",
			"""
			The colour space of the output image, used to convert the input image
			from the scene linear colorspace defined by the OpenColorIO config.
			The default behaviour is to automatically determine the colorspace by
			calling the function registered with `ImageWriter::setDefaultColorSpaceFunction()`.
			""",

			"presetNames", OpenColorIOTransformUI.colorSpacePresetNames,
			"presetValues", OpenColorIOTransformUI.colorSpacePresetValues,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		],

		"layout" : [

			"description",
			"""
			Controls where channels are placed in the file, including how they are named.
			"Single part" writes all channels to the same part ( all interleaved ).
			"Part per layer" writes a separate part for each layer, so they may be loaded
			independently for better performance, and is the default.  "Part per view" is
			a compromise, where layers are not separated, but views are separated, so that
			stereo files can use independent data windows.

			There is also the option to use a layout that matches Nuke's default
			behaviour, but does not conform to the EXR specification. The Nuke presets
			match "Part per Layer", "Part per View", and "Single Part" respectively, but with
			the following deviations from the specification :

			* The layer name is omitted from the channel name
			* Custom channels from the main layer are placed in a part named other
			* The channel Z from the main layer is placed in a part named depth
			* The RGBA channels from secondary layers are renamed to red, green, blue, and alpha
			* When writing single part stereo, the view name comes before the layer name

			You may also pick "custom", and set up your own layout.  This allows for things
			like a mixed layout that is partially EXR spec compliant, and partially Nuke.  Or
			you could use a expression to group some layers together in the same part.

			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"presetsPlugValueWidget:allowCustom", True,

		],
		"layout.partName" : [

			"description",
			"""
			Specifies the name to be stored in EXR's part name metadata.

			If different channels are given different part names, then a multipart
			file is produced.
			""" + layoutVariableDesc,

			# The presets for this are useful in testing and scripting when the UI isn't loaded,
			# so we register them in src/GafferImage/ImageWriter.cpp

		],
		"layout.channelName" : [

			"description",
			"""
			Specifies the channel name to be given to EXR.  To match the standard, this should just
			be exactly the Gaffer channel name.  But some other software like Nuke omits the layer prefix,
			and assumes that the part name will be prefixed to the channel.
			""" + layoutVariableDesc,

			# The presets for this are useful in testing and scripting when the UI isn't loaded,
			# so we register them in src/GafferImage/ImageWriter.cpp

		],

		"matchDataWindows" : [
			"description",
			"""
			For multi-view images, sets the data windows to be the same for all views, by expanding them
			all to include the union of all views.  Wastes disk space and processing time, but is
			required by Nuke for multi-view images.
			"""
		],

		"out" : [

			"description",
			"""
			A pass-through of the input image.
			""",

		],

		"dpx" : [

			"description",
			"""
			Format options specific to DPX files.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.DPX",
			"layout:visibilityActivator", "dpx",

		],

		"dpx.dataType" : [

			"description",
			"""
			The data type to be written to the DPX file.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:8-bit", "uint8",
			"preset:10-bit", "uint10",
			"preset:12-bit", "uint12",
			"preset:16-bit", "uint16",

		],

		"field3d" : [

			"description",
			"""
			Format options specific to Field3D files.
			""",

			"nodule:type", "",
			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.Field3D",
			"layout:visibilityActivator", "field3d",

		],

		"field3d.mode" : [

			"description",
			"""
			The write mode for the Field3D file - scanline or tiled data.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Scanline", GafferImage.ImageWriter.Mode.Scanline,
			"preset:Tile", GafferImage.ImageWriter.Mode.Tile,

		],

		"field3d.dataType" : [

			"description",
			"""
			The data type to be written to the Field3D file.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Half", "half",
			"preset:Float", "float",
			"preset:Double", "double",

		],

		"fits" : [

			"description",
			"""
			Format options specific to FITS files.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.FITS",
			"layout:visibilityActivator", "fits",

		],

		"fits.dataType" : [

			"description",
			"""
			The data type to be written to the FITS file.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:8-bit", "uint8",
			"preset:16-bit", "uint16",
			"preset:32-bit", "uint32",
			"preset:Float", "float",
			"preset:Double", "double",

		],

		"iff" : [

			"description",
			"""
			Format options specific to IFF files.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.IFF",
			"layout:visibilityActivator", "iff",

		],

		"iff.mode" : [

			"description",
			"""
			The write mode for the IFF file - scanline or tiled data.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Scanline", GafferImage.ImageWriter.Mode.Scanline,
			"preset:Tile", GafferImage.ImageWriter.Mode.Tile,

		],

		"jpeg" : [

			"description",
			"""
			Format options specific to Jpeg files.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.Jpeg",
			"layout:visibilityActivator", "jpeg",

		],

		"jpeg.compressionQuality" : [

			"description",
			"""
			The compression quality for the Jpeg file to be written.
			A value between 0 (low quality, high compression) and
			100 (high quality, low compression).
			""",

		],

		"jpeg.chromaSubSampling" : [

			"description",
			"""
			The chroma sub sampling used to write the jpeg file.
			Note that the file will be stored as YCbCr instead of RGB.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Default (4:2:0)", "",
			"preset:4:4:4", "4:4:4",
			"preset:4:2:2", "4:2:2",
			"preset:4:2:0", "4:2:0",
			"preset:4:1:1", "4:1:1",
		],

		"jpeg2000" : [

			"description",
			"""
			Format options specific to Jpeg2000 files.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.Jpeg2000",
			"layout:visibilityActivator", "jpeg2000",

		],

		"jpeg2000.dataType" : [

			"description",
			"""
			The data type to be written to the Jpeg2000 file.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:8-bit", "uint8",
			"preset:16-bit", "uint16",

		],

		"openexr" : [

			"description",
			"""
			Format options specific to OpenEXR files.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.OpenEXR",
			"layout:visibilityActivator", "openexr",

			"layout:activator:compressionIsDWA", lambda plug : plug["compression"].getValue() in ( "dwaa", "dwab" ),

		],

		"openexr.mode" : [

			"description",
			"""
			The write mode for the OpenEXR file - scanline or tiled data.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Scanline", GafferImage.ImageWriter.Mode.Scanline,
			"preset:Tile", GafferImage.ImageWriter.Mode.Tile,

		],

		"openexr.compression" : [

			"description",
			"""
			The compression method to use when writing the OpenEXR file.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:None", "none",
			"preset:Zip", "zip",
			"preset:Zip Scanline", "zips",
			"preset:RLE", "rle",
			"preset:Piz", "piz",
			"preset:PXR24", "pxr24",
			"preset:B44", "b44",
			"preset:B44A", "b44a",
			"preset:DWAA", "dwaa",
			"preset:DWAB", "dwab",

		],

		"openexr.dwaCompressionLevel" : [

			"description",
			"""
			The compression level used when writing files with DWAA or DWAB compression.
			Higher values decrease file size at the expense of image quality.
			""",

			"layout:activator", "compressionIsDWA",

		],

		"openexr.dataType" : [

			"description",
			"""
			The data type to be written to the OpenEXR file.  If you want to use different
			data types for different channels, you can drive this with an expression or spreadsheet,
			which may use the same context variables as the layout plugs ( the useful ones are
			`${imageWriter:channelName}`, `${imageWriter:layerName}` and `${imageWriter:baseName}`,
			for the whole channel name, and for the prefix and suffix respectively ).
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Float", "float",
			"preset:Half Float", "half",

			"ui:spreadsheet:selectorValue", "${imageWriter:channelName}",

		],

		"openexr.depthDataType" : [

			"description",
			"""
			Overriding the data type for depth channels is useful because many of the things depth is used
			for require greater precision.  This is a simple override which sets Z and ZBack to float precision.
			If you want to do something more complex, set this to `Use Default`, and connect an expression or
			spreadsheet to the `Data Type` plug.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Override to Float", "float",
			"preset:Use Default", "",

		],

		"png" : [

			"description",
			"""
			Format options specific to PNG files.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.PNG",
			"layout:visibilityActivator", "png",

		],

		"png.compression" : [

			"description",
			"""
			The compression method to use when writing the PNG file.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Default", "default",
			"preset:Filtered", "filtered",
			"preset:Huffman", "huffman",
			"preset:RLE", "rle",
			"preset:Fixed", "fixed",

		],

		"png.compressionLevel" : [

			"description",
			"""
			The compression level of the PNG file. This is a value between
			0 (no compression) and 9 (most compression).
			""",

		],

		"rla" : [

			"description",
			"""
			Format options specific to RLA files.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.RLA",
			"layout:visibilityActivator", "rla",

		],

		"rla.dataType" : [

			"description",
			"""
			The data type to be written to the RLA file.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:8-bit", "uint8",
			"preset:16-bit", "uint16",
			"preset:Float", "float",

		],

		"sgi" : [

			"description",
			"""
			Format options specific to SGI files.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.SGI",
			"layout:visibilityActivator", "sgi",

		],

		"sgi.dataType" : [

			"description",
			"""
			The data type to be written to the SGI file.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:8-bit", "uint8",
			"preset:16-bit", "uint16",

		],

		"targa" : [

			"description",
			"""
			Format options specific to Targa files.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.Targa",
			"layout:visibilityActivator", "targa",

		],

		"targa.compression" : [

			"description",
			"""
			The compression method to use when writing the Targa file.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:None", "none",
			"preset:RLE", "rle",

		],

		"tiff" : [

			"description",
			"""
			Format options specific to TIFF files.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.TIFF",
			"layout:visibilityActivator", "tiff",

		],

		"tiff.mode" : [

			"description",
			"""
			The write mode for the TIFF file - scanline or tiled data.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Scanline", GafferImage.ImageWriter.Mode.Scanline,
			"preset:Tile", GafferImage.ImageWriter.Mode.Tile,

		],

		"tiff.compression" : [

			"description",
			"""
			The compression method to use when writing the TIFF file.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:None", "none",
			"preset:LZW", "lzw",
			"preset:Zip", "zip",
			"preset:Pack Bits", "packbits",

		],

		"tiff.dataType" : [

			"description",
			"""
			The data type to be written to the TIFF file.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:8-bit", "uint8",
			"preset:16-bit", "uint16",
			"preset:Float", "float",

		],

		"webp" : [

			"description",
			"""
			Format options specific to WebP files.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.WebP",
			"layout:visibilityActivator", "webp",

		],

		"webp.compressionQuality" : [

			"description",
			"""
			The compression quality for the WebP file to be written.
			A value between 0 (low quality, high compression) and
			100 (high quality, low compression).
			""",

		],


	}

)
