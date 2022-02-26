import six

import PyOpenColorIO

import GafferImage

def defaultColorSpace( fileName, fileFormat, dataType, metadata ) :

	config = PyOpenColorIO.GetCurrentConfig()

	linear = config.getColorSpace( PyOpenColorIO.ROLE_SCENE_LINEAR ).getName()
	log = config.getColorSpace( PyOpenColorIO.ROLE_COMPOSITING_LOG ).getName()
	display = config.getColorSpace( PyOpenColorIO.ROLE_COLOR_PICKING ).getName()

	colorSpaces = {

		"bmp" : display,
		"cineon" : log,
		"dds" : display,

		"dpx" : {
			"uint8"  : display,
			"uint16" : display,
			"uint10" : log,
			"uint12" : log,
		},

		"fits" : {
			"uint8"  : display,
			"uint16" : display,
			"uint32" : linear,
			"float"  : linear,
			"double" : linear,
		},

		"ico" : display,
		"iff" : display,
		"jpeg" : display,
		"jpeg2000" : display,
		"openexr" : linear,
		"png" : display,
		"pnm" : display,
		"psd" : display,
		"raw" : linear,
		"rla" : display,
		"sgi" : display,
		"softimage" : display,
		"targa" : display,

		"tiff" : {
			"uint8"  : display,
			"uint16" : display,
			"uint32" : linear,
			"float"  : linear,
		},

		"zfile" : linear,

	}

	s = colorSpaces[fileFormat]
	if isinstance( s, six.string_types ) :
		return s
	else :
		return s[dataType]

GafferImage.ImageReader.setDefaultColorSpaceFunction( defaultColorSpace )
GafferImage.ImageWriter.setDefaultColorSpaceFunction( defaultColorSpace )

