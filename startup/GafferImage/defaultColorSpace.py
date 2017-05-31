import PyOpenColorIO

import GafferImage

def defaultColorSpace( optionsData ):
	"""
	Default image colorSpace configuration,
	based on file format options.

	@param optionsData: IECore.CompounData CompoundData containing Image specs.
	@retvalue string colorSpace name, valid for current OpenColorIO config.
	"""
		
	config = PyOpenColorIO.GetCurrentConfig()

	colorSpaceMetadataKey = "gaffer:colorSpace"
	# use metadata colorSpace if available
	if "metadata" in optionsData and colorSpaceMetadataKey in optionsData["metadata"]:
		availableColorSpaces =  GafferImage.OpenColorIOTransform.availableColorSpaces()
		metadataColorSpace = optionsData["metadata"][ colorSpaceMetadataKey ].value 
		if metadataColorSpace.lower() in map( str.lower, availableColorSpaces ):
			return metadataColorSpace
		else:
			IECore.warning( "colorSpace {0} from metadata {1} is invalid for current OpenColorIO config".format( metadataColorSpace, colorSpaceMetadataKey ) )

	sceneLinear = config.getColorSpace(PyOpenColorIO.Constants.ROLE_SCENE_LINEAR).getName()
	log = config.getColorSpace(PyOpenColorIO.Constants.ROLE_COMPOSITING_LOG).getName()
	display = config.getColorSpace(PyOpenColorIO.Constants.ROLE_COLOR_PICKING).getName()
 
	colorSpaces = {
		"openexr" : sceneLinear,

		"exr" : sceneLinear,

		"jpg" : display,

		"dpx" : {
			"uint8"  : display,
			"uint16" : display,
			"uint10" : log,
			"uint12" : log,
		},

		"tiff" : {
			"uint8"  : display,
			"uint16" : display,
			"float"  : sceneLinear,
		},

		"tif" : {
			"uint8"  : display,
			"uint16" : display,
			"float"  : sceneLinear,
		},

		"sgi" : {
			"uint8"  : display,
			"uint16" : display,
		},

		"fits" : {
			"uint8"  : display,
			"uint16" : display,
			"uint32" : sceneLinear,
			"float"  : sceneLinear,
			"double" : sceneLinear,
		},
		
	}

	s = colorSpaces.get( optionsData["fileFormat"].value, sceneLinear )
	if isinstance( s, str ) :
		return s
	else :
		return s.get( optionsData["dataType"].value, display )


GafferImage.ImageReader.registerDefaultColorSpace( defaultColorSpace )
GafferImage.ImageWriter.registerDefaultColorSpace( defaultColorSpace )

