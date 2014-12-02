##########################################################################
#
#  Copyright (c) 2014, Esteban Tovagliari. All rights reserved.
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
import xml.etree.ElementTree as ET

import IECore
import IECoreAppleseed

import Gaffer
import GafferUI
import GafferAppleseed

__inputMetadataTree = None

# call appleseed.cli to generate the file with entities metadata, 
# save it in a temporary directory and parse it.
# this is "protected" because it's used in GafferAppleseedTest.
def _parseEntitiesMetadata():

	global __inputMetadataTree
	if not __inputMetadataTree :
		fname = "/tmp/as_input_metadata.xml"
		os.system( "appleseed.cli --dump-input-metadata > " + fname )
		__inputMetadataTree = ET.parse( fname )

# create node plugs, based on appleseed's entity metadata.
# TODO: find a way to have nicer labels in the UI (metadata["label"]...
def __createPlugs( item, node ) :

	node["__model"].setValue( item.attrib["model"] )

	# some environment models need their radiance color input 
	# replaced by a texture input: latlong map and mirrorball map
	needsTexture = "map" in item.attrib["model"]

	for param in item :
		metadata = {}
		metadata["name"] = param.attrib["name"]

		for param_metadata in param :
			if "value" in param_metadata.attrib :
				try :
					metadata[param_metadata.attrib["name"]] = float( param_metadata.attrib["value"] )
				except :
					metadata[param_metadata.attrib["name"]] = param_metadata.attrib["value"]

		if "type" in metadata :
			paramType = metadata["type"]
			plug = None

			# replace radiance color input by a texture input for models
			# where colors don't make sense, like latlong and mirrorball envs.
			if needsTexture and metadata["name"] == "radiance" :
				plug = Gaffer.StringPlug( name="radiance_map", defaultValue="" )
			# replace color multipliers by float multipliers as it makes more 
			# sense to have them as floats inside Gaffer.
			elif "multiplier" in metadata["name"] and paramType == 'colormap' :
				plug = Gaffer.FloatPlug( name=metadata["name"], defaultValue=1.0 )
			else :
				if paramType == "numeric" :
					plug = Gaffer.FloatPlug( name=metadata["name"], defaultValue=metadata["default"], minValue=metadata["min_value"], maxValue=metadata["max_value"] )
				elif paramType == "colormap" :
					plug = Gaffer.Color3fPlug( name=metadata["name"], defaultValue=IECore.Color3f( 1.0, 1.0, 1.0 ))
				elif paramType == "boolean" :
					plug = Gaffer.BoolPlug( name=metadata["name"], defaultValue=metadata["default"] == "true" )
				elif paramType == "text" :
					plug = Gaffer.FloatPlug( name=metadata["name"], defaultValue=metadata["default"] )
				elif paramType == "entity" :
					plug = Gaffer.StringPlug( name=metadata["name"], defaultValue="" )

			if plug :
				plug.setFlags( Gaffer.Plug.Flags.Dynamic, True )
				node["parameters"].addChild( plug )

def __displayName( model ) :

	displayName = " ".join( [ IECore.CamelCase.toSpaced( x ) for x in model.split( "_" ) ] )
	displayName = displayName.replace(" Light", "" )
	displayName = displayName.replace(" Environment Edf", "" )
	return displayName

# create an AppleseedLight representing model "model".
# this is "protected" because it's used in GafferAppleseedTest.
def _lightCreator( model ) :

	global __inputMetadataTree

	item = None
	for child in __inputMetadataTree.getroot() :
		if child.attrib["model"] == model :
			item = child
			break

	light = GafferAppleseed.AppleseedLight( model )
	__createPlugs( item, light )
	return light

def appendLights( menuDefinition, prefix="/Appleseed" ) :

	global __inputMetadataTree
	_parseEntitiesMetadata()

	for child in __inputMetadataTree.getroot() :
		entity_type = child.attrib["type"]
		if entity_type == "light" or entity_type == "environment_edf" :
			model = child.attrib["model"]
			displayName = __displayName( model )

			if entity_type == "light" :
				menuPath = prefix + "/Light/" + displayName
			else :
				menuPath = prefix + "/Environment/" + displayName

			menuDefinition.append(
				menuPath,
				{
					"command" : GafferUI.NodeMenu.nodeCreatorWrapper( IECore.curry( _lightCreator, model ) ),
					"searchText" : "as" + displayName.replace( " ", "" ),
				}
			)

GafferUI.PlugValueWidget.registerCreator(
	GafferAppleseed.AppleseedLight,
	"parameters.radiance_map",
	lambda plug : GafferUI.PathPlugValueWidget( plug,
		path = Gaffer.FileSystemPath( "/", filter = Gaffer.FileSystemPath.createStandardFilter() ),
		pathChooserDialogueKeywords = {
			"bookmarks" : GafferUI.Bookmarks.acquire( plug, category = "appleseed" ),
			"leaf" : True,
		},
	),
)
