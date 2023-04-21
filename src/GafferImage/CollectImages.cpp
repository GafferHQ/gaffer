//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
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

#include "GafferImage/CollectImages.h"

#include "GafferImage/BufferAlgo.h"
#include "GafferImage/ImageAlgo.h"
#include "GafferImage/ImageProcessor.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"

#include "fmt/format.h"

#include <numeric>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo Maybe move this to BufferAlgo.h? It could probably be reused
/// in Offset::computeChannelData() at least.
void copyRegion( const float *fromBuffer, const Box2i &fromWindow, const Box2i &fromRegion, float *toBuffer, const Box2i &toWindow, const V2i &toOrigin )
{
	const int width = fromRegion.max.x - fromRegion.min.x;

	V2i fromP = fromRegion.min;
	V2i toP = toOrigin;
	for( int maxY = fromRegion.max.y; fromP.y < maxY; ++fromP.y, ++toP.y )
	{
		memcpy(
			toBuffer + BufferAlgo::index( toP, toWindow ),
			fromBuffer + BufferAlgo::index( fromP, fromWindow ),
			sizeof( float ) * width
		);
	}
}

void sourceLayerAndChannel( const string &destChannel, const vector<string> &rootLayers, string &srcLayer, string &srcChannel )
{
	for( unsigned int i = 0; i < rootLayers.size(); i++ )
	{
		if(
			destChannel.size() >= rootLayers[i].size() + 2 &&
			destChannel.compare( 0, rootLayers[i].size(), rootLayers[i] ) == 0 &&
			destChannel[rootLayers[i].size()] == '.' )
		{
			srcLayer = rootLayers[i];
			srcChannel = destChannel.substr( rootLayers[i].size() + 1 );

			// Note that if multiple layer names could match this channel, we just take the first one.
			// This would only apply in strange circumstances, and in this case of ambiguity, just taking the
			// first one seems reasonable
			return;
		}
	}

	srcLayer = "";
	srcChannel = destChannel;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// CollectImages
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( CollectImages );

size_t CollectImages::g_firstPlugIndex = 0;

CollectImages::CollectImages( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringVectorDataPlug( "rootLayers", Plug::In, new StringVectorData ) );
	addChild( new StringPlug( "layerVariable", Plug::In, "collect:layerName" ) );
	addChild( new BoolPlug( "mergeMetadata", Plug::In ) );
}

CollectImages::~CollectImages()
{
}

Gaffer::StringVectorDataPlug *CollectImages::rootLayersPlug()
{
	return getChild<Gaffer::StringVectorDataPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::StringVectorDataPlug *CollectImages::rootLayersPlug() const
{
	return getChild<Gaffer::StringVectorDataPlug>( g_firstPlugIndex + 0 );
}

Gaffer::StringPlug *CollectImages::layerVariablePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *CollectImages::layerVariablePlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *CollectImages::mergeMetadataPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *CollectImages::mergeMetadataPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 2 );
}

void CollectImages::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	const ImagePlug *imagePlug = input->parent<ImagePlug>();
	if( imagePlug && imagePlug == inPlug() )
	{
		if( input == imagePlug->dataWindowPlug() )
		{
			outputs.push_back( outPlug()->dataWindowPlug() );
		}

		if( input == imagePlug->channelNamesPlug() )
		{
			outputs.push_back( outPlug()->channelNamesPlug() );
		}

		if( input == imagePlug->channelDataPlug() )
		{
			outputs.push_back( outPlug()->channelDataPlug() );
		}

		if( input == imagePlug->formatPlug() )
		{
			outputs.push_back( outPlug()->formatPlug() );
		}

		if( input == imagePlug->metadataPlug() )
		{
			outputs.push_back( outPlug()->metadataPlug() );
		}

		if( input == imagePlug->sampleOffsetsPlug() )
		{
			outputs.push_back( outPlug()->sampleOffsetsPlug() );
		}

		if( input == imagePlug->deepPlug() )
		{
			outputs.push_back( outPlug()->deepPlug() );
			outputs.push_back( outPlug()->dataWindowPlug() );
			outputs.push_back( outPlug()->channelDataPlug() );
		}
	}
	else if( input == rootLayersPlug() || input == layerVariablePlug() )
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( outPlug()->metadataPlug() );
		outputs.push_back( outPlug()->sampleOffsetsPlug() );
		outputs.push_back( outPlug()->deepPlug() );
	}
	else if( input == mergeMetadataPlug() )
	{
		outputs.push_back( outPlug()->metadataPlug() );
	}

}

void CollectImages::hashViewNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashViewNames( output, context, h );

	const std::string layerVariable = layerVariablePlug()->getValue();

	ConstStringVectorDataPtr rootLayersData = rootLayersPlug()->getValue();
	const vector<string> &rootLayers = rootLayersData->readable();

	Context::EditableScope editScope( context );
	for( unsigned int i = 0; i < rootLayers.size(); i++ )
	{
		editScope.set( layerVariable, &( rootLayers[i] ) );
		inPlug()->viewNamesPlug()->hash( h );
	}
}

IECore::ConstStringVectorDataPtr CollectImages::computeViewNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{

	const std::string layerVariable = layerVariablePlug()->getValue();

	ConstStringVectorDataPtr rootLayersData = rootLayersPlug()->getValue();
	const vector<string> &rootLayers = rootLayersData->readable();

	if( rootLayers.size() == 0 )
	{
		return ImagePlug::defaultViewNames();
	}

	Context::EditableScope editScope( context );
	editScope.set( layerVariable, &( rootLayers[0] ) );
	ConstStringVectorDataPtr firstViewNamesData = inPlug()->viewNamesPlug()->getValue();
	const std::vector<string> &firstViewNames = firstViewNamesData->readable();
	for( unsigned int i = 1; i < rootLayers.size(); i++ )
	{
		editScope.set( layerVariable, &( rootLayers[i] ) );
		ConstStringVectorDataPtr layerViewNamesData = inPlug()->viewNamesPlug()->getValue();
		if( firstViewNames != layerViewNamesData->readable() )
		{
			// Requiring all contexts to have matching view names is quite restrictive, but is the simplest.
			// The most thorough solution might be to union the view names across all contexts, but then
			// computing something like the format plug gets more complex, since you have to search for
			// the first context where it is set.  Perhaps taking the views of the first context could be a
			// reasonable compromise, which I think would just require clearing out the channel names
			// when looking at a view that doesn't existing for that context value

			throw IECore::Exception(
				fmt::format(
					"Root layer \"{}\" does not match views for \"{}\" : <{}> vs <{}>",
					rootLayers[i],
					rootLayers[0],
					std::accumulate( layerViewNamesData->readable().begin(), layerViewNamesData->readable().end(), std::string( " " ) ),
					std::accumulate( firstViewNames.begin(), firstViewNames.end(), std::string( " " ) )
				)
			);
		}
	}

	return firstViewNamesData;
}

void CollectImages::hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ConstStringVectorDataPtr rootLayersData = rootLayersPlug()->getValue();

	if( rootLayersData->readable().size() )
	{
		Context::EditableScope editScope( context );
		editScope.set( layerVariablePlug()->getValue(), &( rootLayersData->readable()[0] ) );
		h = inPlug()->formatPlug()->hash();
	}
	else
	{
		ImageProcessor::hashFormat( parent, context, h );
	}
}

GafferImage::Format CollectImages::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstStringVectorDataPtr rootLayersData = rootLayersPlug()->getValue();

	if( rootLayersData->readable().size() )
	{
		Context::EditableScope editScope( context );
		editScope.set( layerVariablePlug()->getValue(), &( rootLayersData->readable()[0] ) );
		return inPlug()->formatPlug()->getValue();
	}
	else
	{
		return outPlug()->formatPlug()->defaultValue();
	}
}

void CollectImages::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashDeep( parent, context, h );

	const std::string layerVariable = layerVariablePlug()->getValue();

	ConstStringVectorDataPtr rootLayersData = rootLayersPlug()->getValue();

	Context::EditableScope editScope( context );
	for( const auto &i : rootLayersData->readable() )
	{
		editScope.set( layerVariable, &i );
		inPlug()->deepPlug()->hash( h );
	}
}

bool CollectImages::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::optional<bool> outDeep = std::nullopt;
	const std::string layerVariable = layerVariablePlug()->getValue();

	ConstStringVectorDataPtr rootLayersData = rootLayersPlug()->getValue();

	Context::EditableScope editScope( context );
	for( const auto &i : rootLayersData->readable() )
	{
		editScope.set( layerVariable, &i );
		bool curDeep = inPlug()->deepPlug()->getValue();
		if( !outDeep.has_value() )
		{
			outDeep = curDeep;
		}
		else
		{
			if( outDeep.value() != curDeep )
			{
				throw IECore::Exception( "Input to CollectImages must be consistent, but it is sometimes deep." );
			}
		}
	}

	return outDeep.value_or( false );
}

void CollectImages::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashSampleOffsets( parent, context, h );
	ConstStringVectorDataPtr rootLayersData;
	string layerVariable;
	{
		ImagePlug::GlobalScope c( context );
		rootLayersData = rootLayersPlug()->getValue();
		layerVariable = layerVariablePlug()->getValue();
	}

	Context::EditableScope editScope( context );
	for( const auto &i : rootLayersData->readable() )
	{
		editScope.set( layerVariable, &i );
		inPlug()->sampleOffsetsPlug()->hash( h );
	}
}

IECore::ConstIntVectorDataPtr CollectImages::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstStringVectorDataPtr rootLayersData;
	string layerVariable;
	{
		ImagePlug::GlobalScope c( context );
		rootLayersData = rootLayersPlug()->getValue();
		layerVariable = layerVariablePlug()->getValue();
	}

	IECore::ConstIntVectorDataPtr outSampleOffsetsData;
	Context::EditableScope editScope( context );
	for( const auto &i : rootLayersData->readable() )
	{
		editScope.set( layerVariable, &i );
		IECore::ConstIntVectorDataPtr curSampleOffsetsData = inPlug()->sampleOffsetsPlug()->getValue();
		if( !outSampleOffsetsData )
		{
			outSampleOffsetsData = curSampleOffsetsData;
		}
		else
		{
			ImageAlgo::throwIfSampleOffsetsMismatch( outSampleOffsetsData.get(), curSampleOffsetsData.get(), tileOrigin,
				"SampleOffsets on input to CollectImages must match."
			);
		}
	}
	return outSampleOffsetsData;
}

void CollectImages::hashMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ConstStringVectorDataPtr rootLayersData = rootLayersPlug()->getValue();

	if( rootLayersData->readable().size() )
	{
		const string layerVariable = layerVariablePlug()->getValue();

		Context::EditableScope editScope( context );
		if( !mergeMetadataPlug()->getValue() )
		{
			editScope.set( layerVariable, &( rootLayersData->readable()[0] ) );
			h = inPlug()->metadataPlug()->hash();
		}
		else
		{
			ImageProcessor::hashMetadata( parent, context, h );
			for( const auto &i : rootLayersData->readable() )
			{
				editScope.set( layerVariable, &i );
				inPlug()->metadataPlug()->hash( h );
			}
		}
	}
	else
	{
		ImageProcessor::hashMetadata( parent, context, h );
	}
}

IECore::ConstCompoundDataPtr CollectImages::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstStringVectorDataPtr rootLayersData = rootLayersPlug()->getValue();

	if( rootLayersData->readable().size() )
	{
		const string layerVariable = layerVariablePlug()->getValue();

		Context::EditableScope editScope( context );
		if( !mergeMetadataPlug()->getValue() )
		{
			editScope.set( layerVariable, &( rootLayersData->readable()[0] ) );
			return inPlug()->metadataPlug()->getValue();
		}
		else
		{
			IECore::CompoundDataPtr resultData = new CompoundData();
			auto &result = resultData->writable();
			for( const auto &i : rootLayersData->readable() )
			{
				editScope.set( layerVariable, &i );
				IECore::ConstCompoundDataPtr metadata = inPlug()->metadataPlug()->getValue();

				for( const auto &m : metadata->readable() )
				{
					result[m.first] = m.second;
				}
			}
			return resultData;
		}
	}
	else
	{
		return outPlug()->metadataPlug()->defaultValue();
	}
}



void CollectImages::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashDataWindow( output, context, h );

	const std::string layerVariable = layerVariablePlug()->getValue();

	ConstStringVectorDataPtr rootLayersData = rootLayersPlug()->getValue();
	const vector<string> &rootLayers = rootLayersData->readable();

	if( rootLayers.size() == 0 )
	{
		return;
	}

	Context::EditableScope editScope( context );
	editScope.set( layerVariable, &( rootLayers[0] ) );
	inPlug()->deepPlug()->hash( h );
	for( unsigned int i = 0; i < rootLayers.size(); i++ )
	{
		editScope.set( layerVariable, &( rootLayers[i] ) );
		inPlug()->dataWindowPlug()->hash( h );
	}
}

Imath::Box2i CollectImages::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Imath::Box2i dataWindow;

	const std::string layerVariable = layerVariablePlug()->getValue();

	ConstStringVectorDataPtr rootLayersData = rootLayersPlug()->getValue();
	const vector<string> &rootLayers = rootLayersData->readable();

	if( rootLayers.size() == 0 )
	{
		return dataWindow;
	}

	Context::EditableScope editScope( context );
	editScope.set( layerVariable, &( rootLayers[0] ) );
	bool deep = inPlug()->deepPlug()->getValue();
	for( unsigned int i = 0; i < rootLayers.size(); i++ )
	{
		editScope.set( layerVariable, &( rootLayers[i] ) );
		Box2i curDataWindow = inPlug()->dataWindowPlug()->getValue();
		if( i == 0 || !deep )
		{
			dataWindow.extendBy( curDataWindow );
		}
		else
		{
			if( curDataWindow != dataWindow )
			{
				throw IECore::Exception(
					fmt::format(
						"DataWindows on deep input to CollectImages must match. "
						"Received both {},{} -> {},{} and {},{} -> {},{}",
						dataWindow.min.x, dataWindow.min.y, dataWindow.max.x, dataWindow.max.y,
						curDataWindow.min.x, curDataWindow.min.y, curDataWindow.max.x, curDataWindow.max.y
					)
				);
			}
		}
	}

	return dataWindow;
}

void CollectImages::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelNames( output, context, h );

	const std::string layerVariable = layerVariablePlug()->getValue();

	ConstStringVectorDataPtr rootLayersData = rootLayersPlug()->getValue();
	const vector<string> &rootLayers = rootLayersData->readable();

	h.append( &(rootLayers[0]), rootLayers.size() );

	Context::EditableScope editScope( context );
	for( unsigned int i = 0; i < rootLayers.size(); i++ )
	{
		editScope.set( layerVariable, &( rootLayers[i] ) );
		inPlug()->channelNamesPlug()->hash( h );
	}
}

IECore::ConstStringVectorDataPtr CollectImages::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	StringVectorDataPtr channelNamesData = new StringVectorData();
	std::vector<string> &outChannelNames = channelNamesData->writable();

	const std::string layerVariable = layerVariablePlug()->getValue();

	ConstStringVectorDataPtr rootLayersData = rootLayersPlug()->getValue();
	const vector<string> &rootLayers = rootLayersData->readable();

	Context::EditableScope editScope( context );
	for( unsigned int i = 0; i < rootLayers.size(); i++ )
	{
		editScope.set( layerVariable, &( rootLayers[i] ) );
		ConstStringVectorDataPtr layerChannelsData = inPlug()->channelNamesPlug()->getValue();
		const std::vector<string> &layerChannels = layerChannelsData->readable();

		for( unsigned int j = 0; j < layerChannels.size(); j++ )
		{
			std::string curName = GafferImage::ImageAlgo::channelName( rootLayers[i], layerChannels[j] );

			// Duplicate channel names could arise because either:
			// * The user entered the same layer name twice ( just ignore one of them )
			// * A name overlap due to complex hierachical naming:
			//   ie. both a layer named A with a channel named B.R
			//        and a layer named A.B with a channel named R
			//   ( In this complicated and unlikely case, we just take the one listed first in rootLayers )
			if( find( outChannelNames.begin(), outChannelNames.end(), curName ) == outChannelNames.end() )
			{
				outChannelNames.push_back( curName );
			}
		}
	}

	return channelNamesData;
}

void CollectImages::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ConstStringVectorDataPtr rootLayersData;
	string layerVariable;
	{
		ImagePlug::GlobalScope c( context );
		rootLayersData = rootLayersPlug()->getValue();
		layerVariable = layerVariablePlug()->getValue();
	}

	const vector<string> &rootLayers = rootLayersData->readable();

	const std::string &channelName = context->get<string>( ImagePlug::channelNameContextName );
	std::string srcLayer, srcChannel;
	sourceLayerAndChannel( channelName, rootLayers, srcLayer, srcChannel );

	Context::EditableScope editScope( context );
	editScope.set( ImagePlug::channelNameContextName, &srcChannel );
	editScope.set( layerVariable, &srcLayer );

	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	IECore::MurmurHash inputChannelDataHash = inPlug()->channelDataPlug()->hash();

	// We've now gathered all data that depends on the tile/channel, so we can use the same editScope
	// for a global context
	editScope.remove( ImagePlug::channelNameContextName );
	editScope.remove( ImagePlug::tileOriginContextName );
	bool deep = inPlug()->deepPlug()->getValue();
	Box2i inputDataWindow = inPlug()->dataWindowPlug()->getValue();

	const Box2i validBound = BufferAlgo::intersection( tileBound, inputDataWindow );
	if( validBound == tileBound || deep )
	{
		h = inputChannelDataHash;
	}
	else
	{
		ImageProcessor::hashChannelData( parent, context, h );
		if( !BufferAlgo::empty( validBound ) )
		{
			h.append( inputChannelDataHash );
			h.append( BufferAlgo::intersection( inputDataWindow, tileBound ) );
		}
	}
}

IECore::ConstFloatVectorDataPtr CollectImages::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstStringVectorDataPtr rootLayersData;
	string layerVariable;
	{
		ImagePlug::GlobalScope c( context );
		rootLayersData = rootLayersPlug()->getValue();
		layerVariable = layerVariablePlug()->getValue();
	}

	const vector<string> &rootLayers = rootLayersData->readable();

	std::string srcLayer, srcChannel;
	sourceLayerAndChannel( channelName, rootLayers, srcLayer, srcChannel );

	Context::EditableScope editScope( context );
	editScope.set( layerVariable, &srcLayer );

	// First use this EditableScope as a global scope
	editScope.remove( ImagePlug::channelNameContextName );
	editScope.remove( ImagePlug::tileOriginContextName );
	bool deep = inPlug()->deepPlug()->getValue();
	Box2i inputDataWindow = inPlug()->dataWindowPlug()->getValue();

	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i validBound = BufferAlgo::intersection( tileBound, inputDataWindow );
	if( BufferAlgo::empty( validBound ) )
	{
		return ImagePlug::blackTile();
	}

	// Then set up the scope to evaluate the input channel data
	editScope.set( ImagePlug::channelNameContextName, &srcChannel );
	editScope.set( ImagePlug::tileOriginContextName, &tileOrigin );

	ConstFloatVectorDataPtr inputData = inPlug()->channelDataPlug()->getValue();

	if( validBound == tileBound || deep )
	{
		// If we're taking the whole tile, then just return the input tile
		// If we're a deep image, then we're just passing through the sampleOffsets,
		// so we also need to pass through the whole data ( and in the deep case we
		// require all inputs to have matching data windows, so this is fine )
		return inputData;
	}
	else
	{
		FloatVectorDataPtr resultData = new FloatVectorData;
		vector<float> &result = resultData->writable();
		result.resize( ImagePlug::tileSize() * ImagePlug::tileSize(), 0.0f );
		copyRegion(
			&inputData->readable().front(),
			tileBound,
			validBound,
			&result.front(),
			tileBound,
			validBound.min
		);
		return resultData;
	}
}
