//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2015, Nvizible Ltd. All rights reserved.
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

#include "IECore/BoxOps.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"

#include "GafferImage/ImageAlgo.h"
#include "GafferImage/DeepMerge.h"

#include <optional>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

namespace
{

class MergeContextHandler
{
public:
	MergeContextHandler( const DeepMerge* mergeNode, const Context *context )
		:	m_mode( (DeepMerge::Mode)mergeNode->modePlug()->getValue() )
	{
		if( m_mode == DeepMerge::Mode::Collect )
		{
			m_contextValuesData = mergeNode->contextValuesPlug()->getValue();
			m_contextValues = &m_contextValuesData->readable();
			m_contextVariable = mergeNode->contextVariablePlug()->getValue();
			m_indexContextVariable = mergeNode->indexContextVariablePlug()->getValue();

			m_numContexts = m_contextValues->size();

			m_scope.emplace( context );

			m_context = m_scope->context();
		}
		else
		{
			m_numContexts = 1;
			m_context = context;
		}
	}

	int numContexts()
	{
		return m_numContexts;
	}

	void setContextForIndex( int index )
	{
		if( m_mode == DeepMerge::Mode::Collect )
		{
			m_index = index;
			m_scope->set( m_contextVariable, &( (*m_contextValues)[m_index] ) );
			m_scope->set( m_indexContextVariable, &m_index );
		}
	}

	const Context *context()
	{
		return m_context;
	}

private:

	const DeepMerge::Mode m_mode;
	ConstStringVectorDataPtr m_contextValuesData;
	const std::vector<std::string> *m_contextValues;
	std::string m_contextVariable;
	std::string m_indexContextVariable;

	int m_numContexts;
	const Context *m_context;

	int m_index;

	std::optional<Context::EditableScope> m_scope;
};

} // namespace

GAFFER_NODE_DEFINE_TYPE( DeepMerge );

size_t DeepMerge::g_firstPlugIndex = 0;

DeepMerge::DeepMerge( const std::string &name )
	:	ImageProcessor( name, 2 )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild(
		new IntPlug(
			"mode",         // name
			Plug::In,       // direction
			(int)Mode::Standard, // default
			(int)Mode::Standard, // min
			(int)Mode::Collect   // max
		)
	);

	addChild( new StringVectorDataPlug( "contextValues", Plug::In ) );
	addChild( new StringPlug( "contextVariable", Plug::In, "merge:value" ) );
	addChild( new StringPlug( "indexContextVariable", Plug::In, "merge:index" ) );

	addChild( new IntVectorDataPlug( "__offsetsCache", Gaffer::Plug::Out, new IntVectorData() ) );
}

DeepMerge::~DeepMerge()
{
}

Gaffer::IntPlug *DeepMerge::modePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *DeepMerge::modePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::StringVectorDataPlug *DeepMerge::contextValuesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringVectorDataPlug *DeepMerge::contextValuesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *DeepMerge::contextVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *DeepMerge::contextVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *DeepMerge::indexContextVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *DeepMerge::indexContextVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::IntVectorDataPlug *DeepMerge::offsetsCachePlug()
{
	return getChild<IntVectorDataPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::IntVectorDataPlug *DeepMerge::offsetsCachePlug() const
{
	return getChild<IntVectorDataPlug>( g_firstPlugIndex + 4 );
}


void DeepMerge::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == offsetsCachePlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
		outputs.push_back( outPlug()->sampleOffsetsPlug() );
	}
	else if(
		input == modePlug() || input == contextValuesPlug() ||
		input == contextVariablePlug() || input == indexContextVariablePlug()
	)
	{
		outputs.push_back( offsetsCachePlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->channelNamesPlug() );
		outputs.push_back( outPlug()->viewNamesPlug() );
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( outPlug()->metadataPlug() );
	}
	else if( const ImagePlug *inputImage = input->parent<ImagePlug>() )
	{
		if( inputImage->parent<ArrayPlug>() == inPlugs() )
		{
			if( input == inputImage->channelDataPlug() || input == inputImage->channelNamesPlug() )
			{
				outputs.push_back( outPlug()->channelDataPlug() );
			}

			if( input == inputImage->channelNamesPlug() )
			{
				outputs.push_back( outPlug()->channelNamesPlug() );
			}

			if( input == inputImage->dataWindowPlug() )
			{
				outputs.push_back( outPlug()->dataWindowPlug() );
			}

			if( input == inputImage->dataWindowPlug() ||
				input == inputImage->sampleOffsetsPlug()
			)
			{
				outputs.push_back( offsetsCachePlug() );
			}

			if( input == inputImage->viewNamesPlug() )
			{
				outputs.push_back( outPlug()->channelDataPlug() );
				outputs.push_back( outPlug()->channelNamesPlug() );
				outputs.push_back( outPlug()->dataWindowPlug() );
				outputs.push_back( offsetsCachePlug() );
			}

			if( inputImage == inPlug() )
			{
				if( input == inputImage->viewNamesPlug() )
				{
					outputs.push_back( outPlug()->viewNamesPlug() );
				}
				else if( input == inputImage->formatPlug() )
				{
					outputs.push_back( outPlug()->formatPlug() );
				}
				else if( input == inputImage->metadataPlug() )
				{
					outputs.push_back( outPlug()->metadataPlug() );
				}
			}
		}

	}
}

void DeepMerge::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );

	if( output != offsetsCachePlug() )
	{
		return;
	}

	V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	MergeContextHandler contextHandler( this, context );

	// The layer indices stored in the offsets cache depend on the number of contexts
	h.append( contextHandler.numContexts() );

	for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
	{
		if( !(*it)->getInput<ValuePlug>() )
		{
			continue;
		}

		for( int i = 0; i < contextHandler.numContexts(); i++ )
		{
			contextHandler.setContextForIndex( i );

			if( !ImageAlgo::viewIsValid( context, (*it)->viewNames()->readable() ) )
			{
				continue;
			}

			Box2i dataWindow;
			{
				ImagePlug::GlobalScope c( contextHandler.context() );
				dataWindow = (*it)->dataWindowPlug()->getValue();
			}
			Box2i validBound = BufferAlgo::intersection( tileBound, dataWindow );

			if( BufferAlgo::empty( validBound ) )
			{
				h.append( 0 );
				continue;
			}
			h.append( validBound );

			(*it)->sampleOffsetsPlug()->hash( h );
		}
	}
}

void DeepMerge::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	ImageProcessor::compute( output, context );

	if( output != offsetsCachePlug() )
	{
		return;
	}

	V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	MergeContextHandler contextHandler( this, context );
	const int numContexts = contextHandler.numContexts();

	// Each layer is an input plug evaluated in a particular context. We identify
	// them with a single index : `plugIndex * numContexts + contextIndex`.
	struct InputStruct
	{
		unsigned int layerIndex;
		Box2i boundInTile;
	};
	std::vector<InputStruct> inputs;

	for( unsigned int j = 0; j < inPlugs()->children().size(); j++ )
	{
		const ImagePlug *inP = inPlugs()->getChild<ImagePlug>( j );
		if( !inP || !inP->getInput<ValuePlug>() )
		{
			continue;
		}

		for( int i = 0; i < numContexts; i++ )
		{
			contextHandler.setContextForIndex( i );
			ImagePlug::GlobalScope c( contextHandler.context() );

			if( !ImageAlgo::viewIsValid( context, inP->viewNames()->readable() ) )
			{
				continue;
			}

			Box2i dataWindow = inP->dataWindowPlug()->getValue();
			Box2i validBound = BufferAlgo::intersection( tileBound, dataWindow );

			if( BufferAlgo::empty( validBound ) )
			{
				continue;
			}
			Box2i boundInTile( validBound.min - tileOrigin, validBound.max - tileOrigin );
			inputs.push_back( { j * numContexts + i, boundInTile } );
		}
	}

	unsigned int numInputs = inputs.size();

	IntVectorDataPtr resultData = new IntVectorData();
	std::vector<int> &result = resultData->writable();

	// This internal data structure is a bunch of stuff packed in an int vector.  We want to store all the data
	// necessary to merge N inputs into the channel data.  It starts with N layer indices, for the layers
	// where the inputs are coming from ( some inputs may not be connected, or have empty data windows,
	// and won't be included ).  This is followed N * tilePixels() PAIRs of offset.  Each pair of offsets
	// contains where a sequence of samples starts in the source channelData, and where it ends in the
	// output channelData ( we don't need to store where it starts in the output channelData, since this
	// is just the end of the previous samples ).  This is admittedly a slightly weird format for this
	// internal structure, but it's compact and makes the code to deal with it pretty simple.
	result.resize( ( 1 + 2 * ImagePlug::tilePixels() ) * numInputs, 0 );
	for( unsigned int k = 0; k < numInputs; k++ )
	{
		const int layerIndex = inputs[k].layerIndex;
		result[k] = layerIndex;

		contextHandler.setContextForIndex( layerIndex % numContexts );
		const ImagePlug *inP = inPlugs()->getChild<ImagePlug>( layerIndex / numContexts );
		ConstIntVectorDataPtr sampleOffsetsData = inP->sampleOffsetsPlug()->getValue();
		const std::vector<int> &sampleOffsets = sampleOffsetsData->readable();

		int *offsets = &result[numInputs + 2 * k];

		for( int y = inputs[k].boundInTile.min.y; y < inputs[k].boundInTile.max.y; y++ )
		{
			int prevOffset = 0;
			int minX = inputs[k].boundInTile.min.x;
			int maxX = inputs[k].boundInTile.max.x;

			int pixel = minX + ImagePlug::tileSize() * y;
			if( pixel != 0 )
			{
				prevOffset = sampleOffsets[ pixel - 1 ];
			}

			for( int x = minX; x < maxX; x++ )
			{
				int offset = sampleOffsets[pixel];
				// The position in the current input in written directly
				offsets[ 2 * numInputs * pixel ] = prevOffset;
				// The output offset is initially written as a number of samples
				// per pixel - we accumulate this afterwards to convert to an offset
				offsets[ 2 * numInputs * pixel + 1] = offset - prevOffset;
				prevOffset = offset;
				pixel++;
			}
		}
	}

	// Accumulate the output sample counts into a running offset
	int accum = 0;
	int *offsetPtr = &result[numInputs + 1];
	for( unsigned int o = 0; o < numInputs * ImagePlug::tilePixels(); o++ )
	{
		accum += *offsetPtr;
		*offsetPtr = accum;
		offsetPtr+=2;
	}

	static_cast<IntVectorDataPlug *>( output )->setValue( resultData );
}

void DeepMerge::hashViewNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	MergeContextHandler contextHandler( this, context );

	if( contextHandler.numContexts() == 0 )
	{
		h = inPlug()->viewNamesPlug()->defaultHash();
		return;
	}

	contextHandler.setContextForIndex( 0 );
	h = inPlug()->viewNamesPlug()->hash();
}

IECore::ConstStringVectorDataPtr DeepMerge::computeViewNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	MergeContextHandler contextHandler( this, context );

	if( contextHandler.numContexts() == 0 )
	{
		return inPlug()->viewNamesPlug()->defaultValue();
	}

	contextHandler.setContextForIndex( 0 );
	return inPlug()->viewNamesPlug()->getValue();
}

void DeepMerge::hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	MergeContextHandler contextHandler( this, context );

	if( contextHandler.numContexts() == 0 )
	{
		h = inPlug()->formatPlug()->defaultHash();
		return;
	}

	contextHandler.setContextForIndex( 0 );
	h = inPlug()->formatPlug()->hash();
}

GafferImage::Format DeepMerge::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	MergeContextHandler contextHandler( this, context );

	if( contextHandler.numContexts() == 0 )
	{
		return inPlug()->formatPlug()->defaultValue();
	}

	contextHandler.setContextForIndex( 0 );
	return inPlug()->formatPlug()->getValue();
}

void DeepMerge::hashMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	MergeContextHandler contextHandler( this, context );

	if( contextHandler.numContexts() == 0 )
	{
		h = inPlug()->metadataPlug()->defaultHash();
		return;
	}

	contextHandler.setContextForIndex( 0 );
	h = inPlug()->metadataPlug()->hash();
}

IECore::ConstCompoundDataPtr DeepMerge::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	MergeContextHandler contextHandler( this, context );

	if( contextHandler.numContexts() == 0 )
	{
		return inPlug()->metadataPlug()->defaultValue();
	}

	contextHandler.setContextForIndex( 0 );
	return inPlug()->metadataPlug()->getValue();
}

void DeepMerge::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashDataWindow( output, context, h );

	MergeContextHandler contextHandler( this, context );

	for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
	{
		if( !(*it)->getInput<ValuePlug>() )
		{
			continue;
		}

		for( int i = 0; i < contextHandler.numContexts(); i++ )
		{
			contextHandler.setContextForIndex( i );
			if( ImageAlgo::viewIsValid( context, (*it)->viewNames()->readable() ) )
			{
				(*it)->dataWindowPlug()->hash( h );
			}
		}
	}
}

Imath::Box2i DeepMerge::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Imath::Box2i dataWindow;

	MergeContextHandler contextHandler( this, context );

	for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
	{
		if( !(*it)->getInput<ValuePlug>() )
		{
			continue;
		}

		for( int i = 0; i < contextHandler.numContexts(); i++ )
		{
			contextHandler.setContextForIndex( i );
			if( ImageAlgo::viewIsValid( context, (*it)->viewNames()->readable() ) )
			{
				dataWindow.extendBy( (*it)->dataWindowPlug()->getValue() );
			}
		}
	}

	return dataWindow;
}

void DeepMerge::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelNames( output, context, h );

	MergeContextHandler contextHandler( this, context );

	for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
	{
		if( !(*it)->getInput<ValuePlug>() )
		{
			continue;
		}

		for( int i = 0; i < contextHandler.numContexts(); i++ )
		{
			contextHandler.setContextForIndex( i );
			if( ImageAlgo::viewIsValid( context, (*it)->viewNames()->readable() ) )
			{
				(*it)->channelNamesPlug()->hash( h );
			}
		}
	}
}

IECore::ConstStringVectorDataPtr DeepMerge::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	MergeContextHandler contextHandler( this, context );

	IECore::StringVectorDataPtr outChannelStrVectorData( new IECore::StringVectorData() );
	std::vector<std::string> &outChannels( outChannelStrVectorData->writable() );

	for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
	{
		if( !(*it)->getInput<ValuePlug>() )
		{
			continue;
		}

		for( int i = 0; i < contextHandler.numContexts(); i++ )
		{
			contextHandler.setContextForIndex( i );
			if( ImageAlgo::viewIsValid( context, (*it)->viewNames()->readable() ) )
			{
				IECore::ConstStringVectorDataPtr inChannelStrVectorData((*it)->channelNamesPlug()->getValue() );
				const std::vector<std::string> &inChannels( inChannelStrVectorData->readable() );
				for ( std::vector<std::string>::const_iterator cIt( inChannels.begin() ); cIt != inChannels.end(); ++cIt )
				{
					if ( std::find( outChannels.begin(), outChannels.end(), *cIt ) == outChannels.end() )
					{
						outChannels.push_back( *cIt );
					}
				}
			}
		}
	}

	if ( !outChannels.empty() )
	{
		return outChannelStrVectorData;
	}

	return inPlug()->channelNamesPlug()->defaultValue();
}

void DeepMerge::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( output, context, h );

	const std::string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

	{
		ImagePlug::ChannelDataScope reusedScope( context );
		reusedScope.remove( ImagePlug::channelNameContextName );

		// The offsets cache hash determines which inputs we are pulling for which pixels,
		// which takes into account the input offsets and data windows
		offsetsCachePlug()->hash( h );
	}

	MergeContextHandler contextHandler( this, context );

	for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
	{
		if( !(*it)->getInput<ValuePlug>() )
		{
			continue;
		}

		for( int i = 0; i < contextHandler.numContexts(); i++ )
		{
			contextHandler.setContextForIndex( i );

			if( !ImageAlgo::viewIsValid( context, (*it)->viewNames()->readable() ) )
			{
				continue;
			}

			ConstStringVectorDataPtr channelNamesData = (*it)->channelNames();
			const std::vector<std::string> &channelNames = channelNamesData->readable();
			if( ImageAlgo::channelExists( channelNames, channelName ) )
			{
				(*it)->channelDataPlug()->hash( h );
			}
			else if( channelName == "ZBack" && ImageAlgo::channelExists( channelNames, "Z" ) )
			{
				h.append( (*it)->channelDataHash( "Z", tileOrigin ) );
			}
		}
	}
}

IECore::ConstFloatVectorDataPtr DeepMerge::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstIntVectorDataPtr offsetsCacheData;
	{
		ImagePlug::ChannelDataScope offsetsScope( context );
		offsetsScope.remove( ImagePlug::channelNameContextName );
		offsetsCacheData = offsetsCachePlug()->getValue();
	}

	const std::vector<int> &offsetsCache = offsetsCacheData->readable();
	if( !offsetsCache.size() )
	{
		return ImagePlug::emptyTile();
	}

	FloatVectorDataPtr resultData = new FloatVectorData;
	std::vector<float> &result = resultData->writable();
	result.resize( offsetsCache.back(), 0.0f );

	int numInputs = offsetsCache.size() / ( 1 + 2 * ImagePlug::tilePixels() );

	MergeContextHandler contextHandler( this, context );
	const int numContexts = contextHandler.numContexts();

	// Get a ptr to the channel data of each layer that has the channel
	std::vector< ConstFloatVectorDataPtr > channelDatas( numInputs );
	std::vector< const float* > channelPtrs( numInputs, nullptr );
	for( int j = 0; j < numInputs; j++ )
	{
		const int layerIndex = offsetsCache[j];
		contextHandler.setContextForIndex( layerIndex % numContexts );
		const ImagePlug *inP = inPlugs()->getChild<ImagePlug>( layerIndex / numContexts );
		if( !ImageAlgo::viewIsValid( context, inP->viewNames()->readable() ) )
		{
			continue;
		}

		ConstStringVectorDataPtr channelNamesData = inP->channelNames();
		const std::vector<std::string> &channelNames = channelNamesData->readable();
		if( ImageAlgo::channelExists( channelNames, channelName ) )
		{
			channelDatas[j] = inP->channelDataPlug()->getValue();
		}
		else if( channelName == "ZBack" && ImageAlgo::channelExists( channelNames, "Z" ) )
		{
			// Special case to copy Z to ZBack when combining images where some have ZBack
			// and some don't
			channelDatas[j] = inP->channelData( ImageAlgo::channelNameZ, tileOrigin );
		}
		else
		{
			continue;
		}
		channelPtrs[j] = &channelDatas[j]->readable()[0];
	}

	// Now we can loop through just pasting in the samples from each input to each pixel
	const int *offsets = &offsetsCache[ numInputs ];
	int prevOffset = 0;
	for( int i = 0; i < numInputs * ImagePlug::tilePixels(); i++ )
	{
		int inputOffset = offsets[ 2 * i ];
		int offset = offsets[ 2 * i + 1 ];
		int input = i % numInputs;
		if( channelPtrs[input] && offset != prevOffset )
		{
			memcpy( &result[prevOffset], channelPtrs[input] + inputOffset, sizeof( float ) * ( offset - prevOffset ) );
		}
		prevOffset = offset;
	}

	return resultData;
}

void DeepMerge::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashSampleOffsets( parent, context, h );

	offsetsCachePlug()->hash( h );
}

IECore::ConstIntVectorDataPtr DeepMerge::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IntVectorDataPtr resultData = new IntVectorData;
	vector<int> &result = resultData->writable();
	result.resize( ImagePlug::tilePixels(), 0 );

	ConstIntVectorDataPtr offsetsCacheData = offsetsCachePlug()->getValue();
	if( !offsetsCacheData->readable().size() )
	{
		return ImagePlug::emptyTileSampleOffsets();
	}

	// We can get the final sampleOffsets from the offsets cache just by taking the last offset
	// from each pixel
	int numInputs = offsetsCacheData->readable().size() / ( 1 + 2 * ImagePlug::tilePixels() );

	const int *pixelOffsetPtr = &offsetsCacheData->readable()[ numInputs * 3 - 1 ];

	for( int pixel = 0; pixel < ImagePlug::tilePixels(); pixel++ )
	{
		result[pixel] = *pixelOffsetPtr;
		pixelOffsetPtr += numInputs * 2;
	}

	return resultData;
}

bool DeepMerge::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return true;
}
