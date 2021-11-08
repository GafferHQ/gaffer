//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2012, John Haddon. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#include "GafferArnold/Private/IECoreArnold/ParameterAlgo.h"

#include "IECoreImage/DisplayDriver.h"

#include "IECore/BoxAlgo.h"
#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

#include "ai_drivers.h"
#include "ai_metadata.h"
#include "ai_plugins.h"
#include "ai_universe.h"
#include "ai_version.h"

#include <stdio.h>

using namespace Imath;
using namespace IECore;
using namespace IECoreImage;
using namespace IECoreArnold;

namespace
{

const AtString g_driverTypeArnoldString("driverType");
const AtString g_pixelAspectRatioArnoldString("pixel_aspect_ratio");

// Stores a Cortex DisplayDriver and the parameters
// used to create it. This forms the private data
// accessed via AiNodeGetLocalData.
struct LocalData
{

	LocalData()
		:	numOutputs( 0 )
	{
	}

	DisplayDriverPtr displayDriver;
	ConstCompoundDataPtr displayDriverParameters;
	int numOutputs;

	void imageClose()
	{
		if( !displayDriver )
		{
			return;
		}

		try
		{
			displayDriver->imageClose();
		}
		catch( const std::exception &e )
		{
			// We have to catch and report exceptions because letting them out into pure c land
			// just causes aborts.
			msg( Msg::Error, "ieOutputDriver:driverClose", e.what() );
		}
		displayDriver = nullptr;
	}

};

void driverParameters( AtList *params, AtNodeEntry *nentry )
{
	AiParameterStr( g_driverTypeArnoldString, "" );

	// we need to specify this metadata to keep MtoA happy.
	AiMetaDataSetStr( nentry, nullptr, "maya.attr_prefix", "" );
	AiMetaDataSetStr( nentry, nullptr, "maya.translator", "ie" );
}

void driverInitialize( AtNode *node )
{
	AiDriverInitialize( node, true );
	AiNodeSetLocalData( node, new LocalData );
}

void driverUpdate( AtNode *node )
{
}

bool driverSupportsPixelType( const AtNode *node, uint8_t pixelType )
{
	switch( pixelType )
	{
		case AI_TYPE_RGB :
		case AI_TYPE_RGBA :
		case AI_TYPE_FLOAT :
		case AI_TYPE_VECTOR :
			return true;
		default:
			return false;
	}
}

const char **driverExtension()
{
	return nullptr;
}

void driverOpen( AtNode *node, struct AtOutputIterator *iterator, AtBBox2 displayWindow, AtBBox2 dataWindow, int bucketSize )
{
	LocalData *localData = (LocalData *)AiNodeGetLocalData( node );
	localData->numOutputs = 0;

	std::vector<std::string> channelNames;

	CompoundDataPtr parameters = new CompoundData();
	ParameterAlgo::getParameters( node, parameters->writable() );

	const char *name = nullptr;
	int pixelType = 0;
	while( AiOutputIteratorGetNext( iterator, &name, &pixelType, nullptr ) )
	{
		std::string namePrefix;
		if( strcmp( name, "RGB" ) && strcmp( name, "RGBA" ) )
		{
			namePrefix = std::string( name ) + ".";
		}

		const StringData *layerName = parameters->member< StringData >( "layerName" );
		if( layerName && layerName->readable() != "" )
		{
			namePrefix = layerName->readable() + ".";
		}

		switch( pixelType )
		{
			case AI_TYPE_RGB :
			case AI_TYPE_VECTOR :
				channelNames.push_back( namePrefix + "R" );
				channelNames.push_back( namePrefix + "G" );
				channelNames.push_back( namePrefix + "B" );
				break;
			case AI_TYPE_RGBA :
				channelNames.push_back( namePrefix + "R" );
				channelNames.push_back( namePrefix + "G" );
				channelNames.push_back( namePrefix + "B" );
				channelNames.push_back( namePrefix + "A" );
				break;
			case AI_TYPE_FLOAT :
				// no need for prefix because it's not a compound type
				channelNames.push_back( name );
				break;
		}
		localData->numOutputs += 1;
	}

	/// \todo Make Convert.h
	Box2i cortexDisplayWindow(
		V2i( displayWindow.minx, displayWindow.miny ),
		V2i( displayWindow.maxx, displayWindow.maxy )
	);

	Box2i cortexDataWindow(
		V2i( dataWindow.minx, dataWindow.miny ),
		V2i( dataWindow.maxx, dataWindow.maxy )
	);

	// IECore::DisplayDriver lacks any official mechanism for passing
	// the pixel aspect ratio, so for now we just pass it via the
	// parameters. We should probably move GafferImage::Format to
	// IECoreImage::Format and then use that in place of the display
	// window.
	parameters->writable()["pixelAspect"] = new FloatData(
		AiNodeGetFlt( AiUniverseGetOptions( AiNodeGetUniverse( node ) ), g_pixelAspectRatioArnoldString )
	);

	const std::string driverType = AiNodeGetStr( node, g_driverTypeArnoldString ).c_str();

	// We reuse the previous driver if we can - this allows us to use
	// the same driver for every stage of a progressive render.
	if( localData->displayDriver )
	{
		if(
			localData->displayDriver->typeName() == driverType &&
			localData->displayDriver->displayWindow() == cortexDisplayWindow &&
			localData->displayDriver->dataWindow() == cortexDataWindow &&
			localData->displayDriver->channelNames() == channelNames &&
			localData->displayDriverParameters->isEqualTo( parameters.get() )
		)
		{
			// Can reuse
			return;
		}
		else
		{
			// Can't reuse, so must close before making a new one.
			localData->imageClose();
		}
	}

	// Couldn't reuse a driver, so create one from scratch.
	try
	{
		localData->displayDriver = IECoreImage::DisplayDriver::create( driverType, cortexDisplayWindow, cortexDataWindow, channelNames, parameters );
		localData->displayDriverParameters = parameters;
	}
	catch( const std::exception &e )
	{
		// We have to catch and report exceptions because letting them out into pure c land
		// just causes aborts.
		msg( Msg::Error, "ieOutputDriver:driverOpen", e.what() );
	}
}

bool driverNeedsBucket( AtNode *node, int x, int y, int sx, int sy, uint16_t tId )
{
	return true;
}

void driverPrepareBucket( AtNode *node, int x, int y, int sx, int sy, uint16_t tId )
{
}

void driverProcessBucket( AtNode *node, struct AtOutputIterator *iterator, struct AtAOVSampleIterator *sample_iterator, int x, int y, int sx, int sy, uint16_t tId )
{
}

void driverWriteBucket( AtNode *node, struct AtOutputIterator *iterator, struct AtAOVSampleIterator *sampleIterator, int x, int y, int sx, int sy )
{
	LocalData *localData = (LocalData *)AiNodeGetLocalData( node );
	if( !localData->displayDriver )
	{
		return;
	}

	const int numOutputChannels = localData->displayDriver->channelNames().size();

	const float *imageData;
	std::vector<float> interleavedData;
	if( localData->numOutputs == 1 )
	{
		// Data already has the layout we need.
		const void *bucketData;
		AiOutputIteratorGetNext( iterator, nullptr, nullptr, &bucketData );
		imageData = (float *)bucketData;
	}
	else
	{
		// We need to interleave multiple outputs
		// into a single block for the display driver.
		interleavedData.resize( sx * sy * numOutputChannels );

		int pixelType = 0;
		const void *bucketData;
		int outChannelOffset = 0;
		while( AiOutputIteratorGetNext( iterator, nullptr, &pixelType, &bucketData ) )
		{
			int numChannels = 0;
			switch( pixelType )
			{
				case AI_TYPE_RGB :
				case AI_TYPE_VECTOR :
					numChannels = 3;
					break;
				case AI_TYPE_RGBA :
					numChannels = 4;
					break;
				case AI_TYPE_FLOAT :
					numChannels = 1;
					break;
			}

			for( int c = 0; c < numChannels; c++ )
			{
				float *in = (float *)(bucketData) + c;
				float *out = &(interleavedData[0]) + outChannelOffset;
				for( int j = 0; j < sy; j++ )
				{
					for( int i = 0; i < sx; i++ )
					{
						*out = *in;
						out += numOutputChannels;
						in += numChannels;
					}
				}
				outChannelOffset += 1;
			}
		}

		imageData = &interleavedData[0];
	}

	Box2i bucketBox(
		V2i( x, y ),
		V2i( x + sx - 1, y + sy - 1 )
	);

	try
	{
		localData->displayDriver->imageData( bucketBox, imageData, sx * sy * numOutputChannels );
	}
	catch( const std::exception &e )
	{
		// we have to catch and report exceptions because letting them out into pure c land
		// just causes aborts.
		msg( Msg::Error, "ieOutputDriver:driverWriteBucket", e.what() );
	}
}

void driverClose( AtNode *node, struct AtOutputIterator *iterator )
{
	LocalData *localData = (LocalData *)AiNodeGetLocalData( node );
	// We only close the display immediately if it doesn't accept
	// repeated data (progressive renders). This is so we can reuse it in
	// driverOpen if it appears that a progressive render is taking place.
	if( localData->displayDriver && !localData->displayDriver->acceptsRepeatedData() )
	{
		localData->imageClose();
	}
}

void driverFinish( AtNode *node )
{
	LocalData *localData = (LocalData *)AiNodeGetLocalData( node );
	// Perform any pending close we may have deferred in driverClose().
	localData->imageClose();
	delete localData;
}

} // namespace

AI_EXPORT_LIB bool NodeLoader( int i, AtNodeLib *node )
{
	if( i==0 )
	{
		static AtCommonMethods commonMethods = {
			nullptr, // Whole plugin init
			nullptr, // Whole plugin cleanup
			driverParameters,
			driverInitialize,
			driverUpdate,
			driverFinish
		};
		static AtDriverNodeMethods driverMethods = {
			driverSupportsPixelType,
			driverExtension,
			driverOpen,
			driverNeedsBucket,
			driverPrepareBucket,
			driverProcessBucket,
			driverWriteBucket,
			driverClose
		};
		static AtNodeMethods nodeMethods = {
			&commonMethods,
			&driverMethods
		};

		node->node_type = AI_NODE_DRIVER;
		node->output_type = AI_TYPE_NONE;
		node->name = "ieDisplay";
		node->methods = &nodeMethods;
		sprintf( node->version, AI_VERSION );

		return true;
	}

	return false;
}
