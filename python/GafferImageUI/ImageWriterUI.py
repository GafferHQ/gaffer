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

import IECore

import Gaffer
import GafferUI
import GafferImageUI
import GafferImage

Gaffer.Metadata.registerNode(

	GafferImage.ImageWriter,

	"description",
	"""
	Writes image files to disk using OpenImageIO. All file
	types supported by OpenImageIO are supported by the
	ImageWriter.
	""",


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

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"pathPlugValueWidget:leaf", True,
			"pathPlugValueWidget:bookmarks", "image",
			"fileSystemPathPlugValueWidget:extensions", IECore.StringVectorData( GafferImage.ImageReader.supportedExtensions() ),
			"fileSystemPathPlugValueWidget:extensionsLabel", "Show only image files",
			"fileSystemPathPlugValueWidget:includeSequences", True,

		],

		"channels" : [

			"description",
			"""
			The channels to be written to the file.
			""",

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

		],

		"jpeg.compressionQuality" : [

			"description",
			"""
			The compression quality for the Jpeg file to be written.
			A value between 0 (low quality, high compression) and
			100 (high quality, low compression).
			""",

		],

		"jpeg2000" : [

			"description",
			"""
			Format options specific to Jpeg2000 files.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.Jpeg2000",

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

		],

		"openexr.dataType" : [

			"description",
			"""
			The data type to be written to the OpenEXR file.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Float", "float",
			"preset:Half Float", "half",

		],

		"png" : [

			"description",
			"""
			Format options specific to PNG files.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Settings.PNG",

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
