//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/DeepSampler.h"

#include "GafferImage/ImagePlug.h"
#include "GafferImage/ImageAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( DeepSampler );

size_t DeepSampler::g_firstPlugIndex = 0;

DeepSampler::DeepSampler( const std::string &name )
	:	ComputeNode( name )
{

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ImagePlug( "image" ) );
	addChild( new V2iPlug( "pixel" ) );
	addChild( new AtomicCompoundDataPlug( "pixelData", Plug::Out, new IECore::CompoundData ) );
}

DeepSampler::~DeepSampler()
{
}

ImagePlug *DeepSampler::imagePlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const ImagePlug *DeepSampler::imagePlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::V2iPlug *DeepSampler::pixelPlug()
{
	return getChild<V2iPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::V2iPlug *DeepSampler::pixelPlug() const
{
	return getChild<V2iPlug>( g_firstPlugIndex + 1 );
}

Gaffer::AtomicCompoundDataPlug *DeepSampler::pixelDataPlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::AtomicCompoundDataPlug *DeepSampler::pixelDataPlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 2 );
}

void DeepSampler::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == imagePlug()->dataWindowPlug() ||
		input == imagePlug()->channelDataPlug() ||
		input == imagePlug()->channelNamesPlug() ||
		input->parent<Plug>() == pixelPlug()
	)
	{
		outputs.push_back( pixelDataPlug() );
	}
}

void DeepSampler::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == pixelDataPlug() )
	{
		V2i pixel = pixelPlug()->getValue();
		Box2i dataWindow = imagePlug()->dataWindowPlug()->getValue();
		if( BufferAlgo::contains( dataWindow, pixel ) )
		{
			h.append( pixel );
			ConstStringVectorDataPtr channelNames = imagePlug()->channelNamesPlug()->getValue();

			V2i tileOrigin = ImagePlug::tileOrigin( pixel );

			ImagePlug::ChannelDataScope channelScope( context );
			channelScope.setTileOrigin( tileOrigin );

			imagePlug()->sampleOffsetsPlug()->hash( h );

			for( const auto &i : channelNames->readable() )
			{
				channelScope.setChannelName( i );
				imagePlug()->channelDataPlug()->hash( h );
			}
		}
	}
}

void DeepSampler::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == pixelDataPlug() )
	{
		V2i pixel = pixelPlug()->getValue();
		Box2i dataWindow = imagePlug()->dataWindowPlug()->getValue();

		CompoundDataPtr result = new CompoundData();
		if( BufferAlgo::contains( dataWindow, pixel ) )
		{
			ConstStringVectorDataPtr channelNames = imagePlug()->channelNamesPlug()->getValue();

			V2i tileOrigin = ImagePlug::tileOrigin( pixel );


			ImagePlug::ChannelDataScope channelScope( context );
			channelScope.setTileOrigin( tileOrigin );
			ConstIntVectorDataPtr sampleOffsetsData = imagePlug()->sampleOffsetsPlug()->getValue();

			int pixelIndex = ImagePlug::pixelIndex( pixel, tileOrigin );
			int offset = sampleOffsetsData->readable()[pixelIndex ];
			int prevOffset = pixelIndex > 0 ? sampleOffsetsData->readable()[pixelIndex - 1 ] : 0;
			int pixelSize = offset - prevOffset;

			if( pixelSize > 0 )
			{
				for( const auto &i : channelNames->readable() )
				{
					channelScope.setChannelName( i );
					ConstFloatVectorDataPtr channelData = imagePlug()->channelDataPlug()->getValue();

					FloatVectorDataPtr pixelChannelData = new FloatVectorData();
					pixelChannelData->writable().resize( pixelSize );
					memcpy(
						&pixelChannelData->writable()[0],
						&channelData->readable()[prevOffset],
						sizeof( float ) * pixelSize
					);
					result->writable()[ i ] = pixelChannelData;
				}
			}
		}

		static_cast<AtomicCompoundDataPlug *>( output )->setValue( result );
		return;
	}

	ComputeNode::compute( output, context );
}
