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

#include "GafferImage/DeepRecolor.h"

#include "GafferImage/ImageAlgo.h"

#include "Gaffer/Context.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( DeepRecolor );

size_t DeepRecolor::g_firstPlugIndex = 0;

DeepRecolor::DeepRecolor( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "colorSource" ) );
	addChild( new BoolPlug( "useColorSourceAlpha" ) );

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->deepPlug()->setInput( inPlug()->deepPlug() );
	outPlug()->sampleOffsetsPlug()->setInput( inPlug()->sampleOffsetsPlug() );
}

DeepRecolor::~DeepRecolor()
{
}

GafferImage::ImagePlug *DeepRecolor::colorSourcePlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *DeepRecolor::colorSourcePlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *DeepRecolor::useColorSourceAlphaPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex+1 );
}

const Gaffer::BoolPlug *DeepRecolor::useColorSourceAlphaPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex+1 );
}

void DeepRecolor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == inPlug()->channelDataPlug() ||
		input == inPlug()->channelNamesPlug() ||
		input == inPlug()->sampleOffsetsPlug() ||
		input == colorSourcePlug()->channelDataPlug() ||
		input == colorSourcePlug()->dataWindowPlug() ||
		input == colorSourcePlug()->channelNamesPlug() ||
		input == colorSourcePlug()->deepPlug() ||
		input == useColorSourceAlphaPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}


	if( input == inPlug()->channelNamesPlug() ||
		input == colorSourcePlug()->channelNamesPlug() )
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
	}
}

void DeepRecolor::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const Imath::V2i tileOrigin = context->get<Imath::V2i>( ImagePlug::tileOriginContextName );
	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );

	ImagePlug::ChannelDataScope reusedScope( context );
	reusedScope.remove( ImagePlug::channelNameContextName );
	reusedScope.remove( ImagePlug::tileOriginContextName );

	bool useColorSourceAlpha = useColorSourceAlphaPlug()->getValue();
	ConstStringVectorDataPtr colorSourceChannelNames = colorSourcePlug()->channelNamesPlug()->getValue();
	if(
		channelName == "Z" || channelName == "ZBack" || ( ( !useColorSourceAlpha ) && channelName == "A" ) ||
		!ImageAlgo::channelExists( colorSourceChannelNames->readable(), channelName )
	)
	{
		reusedScope.setTileOrigin( tileOrigin );
		reusedScope.setChannelName( channelName );
		h = inPlug()->channelDataPlug()->hash();
		return;
	}

	ImageProcessor::hashChannelData( output, context, h );

	h.append( useColorSourceAlpha );
	colorSourcePlug()->deepPlug()->hash( h );

	const Imath::Box2i colorSourceDataWindow = colorSourcePlug()->dataWindowPlug()->getValue();
	ConstStringVectorDataPtr inChannelNames = inPlug()->channelNamesPlug()->getValue();

	reusedScope.setTileOrigin( tileOrigin );
	inPlug()->sampleOffsetsPlug()->hash( h );

	reusedScope.setChannelName( "A" );
	if( ImageAlgo::channelExists( inChannelNames->readable(), "A" ) )
	{
		inPlug()->channelDataPlug()->hash( h );
	}
	else
	{
		h.append( true );
	}

	if( ImageAlgo::channelExists( colorSourceChannelNames->readable(), "A" ) )
	{
		colorSourcePlug()->channelDataPlug()->hash( h );
	}
	else
	{
		h.append( true );
	}

	reusedScope.setChannelName( channelName );

	colorSourcePlug()->channelDataPlug()->hash( h );

	const Imath::Box2i boundInTile = BufferAlgo::intersection(
		Imath::Box2i( Imath::V2i( 0 ), Imath::V2i( ImagePlug::tileSize() ) ),
		Imath::Box2i( colorSourceDataWindow.min - tileOrigin, colorSourceDataWindow.max - tileOrigin )
	);

	h.append( boundInTile );
}

IECore::ConstFloatVectorDataPtr DeepRecolor::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ImagePlug::ChannelDataScope reusedScope( context );
	reusedScope.remove( ImagePlug::channelNameContextName );
	reusedScope.remove( ImagePlug::tileOriginContextName );

	bool useColorSourceAlpha = useColorSourceAlphaPlug()->getValue();
	ConstStringVectorDataPtr colorSourceChannelNames = colorSourcePlug()->channelNamesPlug()->getValue();
	if(
		channelName == "Z" || channelName == "ZBack" || ( ( !useColorSourceAlpha ) && channelName == "A" ) ||
		!ImageAlgo::channelExists( colorSourceChannelNames->readable(), channelName )
	)
	{
		reusedScope.setTileOrigin( tileOrigin );
		reusedScope.setChannelName( channelName );
		return inPlug()->channelDataPlug()->getValue();
	}

	if( colorSourcePlug()->deepPlug()->getValue() )
	{
		throw IECore::Exception( "colorSource for DeepRecolor must be Flat" );
	}

	const Imath::Box2i colorSourceDataWindow = colorSourcePlug()->dataWindowPlug()->getValue();
	ConstStringVectorDataPtr inChannelNames = inPlug()->channelNamesPlug()->getValue();

	reusedScope.setTileOrigin( tileOrigin );
	ConstIntVectorDataPtr sampleOffsetsData = inPlug()->sampleOffsetsPlug()->getValue();
	const std::vector<int> &sampleOffsets = sampleOffsetsData->readable();

	FloatVectorDataPtr resultData = new FloatVectorData();
	std::vector<float> &result = resultData->writable();
	result.resize( sampleOffsets.back(), 0.0f );

	const Imath::Box2i boundInTile = BufferAlgo::intersection(
		Imath::Box2i( Imath::V2i( 0 ), Imath::V2i( ImagePlug::tileSize() ) ),
		Imath::Box2i( colorSourceDataWindow.min - tileOrigin, colorSourceDataWindow.max - tileOrigin )
	);

	if( BufferAlgo::empty( boundInTile ) )
	{
		return resultData;
	}

	reusedScope.setChannelName( "A" );
	ConstFloatVectorDataPtr deepAlphaData;
	if( ImageAlgo::channelExists( inChannelNames->readable(), "A" ) )
	{
		if( useColorSourceAlpha && channelName != "A" )
		{
			deepAlphaData = outPlug()->channelDataPlug()->getValue();
		}
		else
		{
			deepAlphaData = inPlug()->channelDataPlug()->getValue();
		}
	}
	else
	{
		return resultData;
	}

	ConstFloatVectorDataPtr colorSourceAlphaData;
	if( ImageAlgo::channelExists( colorSourceChannelNames->readable(), "A" ) )
	{
		colorSourceAlphaData = colorSourcePlug()->channelDataPlug()->getValue();
	}
	else
	{
		colorSourceAlphaData = ImagePlug::whiteTile();
	}

	int scanlineLength = boundInTile.max.x - boundInTile.min.x;

	const std::vector<float> &deepAlpha = deepAlphaData->readable();
	const std::vector<float> &colorSourceAlpha = colorSourceAlphaData->readable();

	if( channelName == "A" )
	{
		// We must be in useColorSourceAlpha mode, otherwise we would have already just returned
		// the source alpha

		for( int y = boundInTile.min.y; y < boundInTile.max.y; y++ )
		{
			int i = y * ImagePlug::tileSize() + boundInTile.min.x;
			int prevOffset = i > 0 ? sampleOffsets[ i - 1 ] : 0;

			for( int j = 0; j < scanlineLength; j++ )
			{
				int offset = sampleOffsets[i];
				if( offset == prevOffset )
				{
					// Don't want to litter the rest of this with special cases for no samples
					i++;
					continue;
				}

				float csAlpha = colorSourceAlpha[i];

				if( csAlpha >= 0.999999f )
				{
					// To reach full opacity, we just need any sample to reach 100% opacity.
					// Just change the last sample, and leave everything else intact
					for( int k = prevOffset; k < offset - 1; k++ )
					{
						result[k] = deepAlpha[k];
					}
					result[offset-1] = 1.0f;
				}
				else if( csAlpha <= 0.0f )
				{
					for( int k = prevOffset; k < offset - 1; k++ )
					{
						result[k] = 0.0f;
					}
				}
				else
				{
					float targetLog = -log1pf( -csAlpha );

					// We don't want to let any alpha values get too close to 1, or else we won't be able to
					// weight them back down ( since we're weighting exponentially )
					float maxContribute = std::max( targetLog, 1000000.0f );

					float accum = 0.0f;
					for( int k = prevOffset; k < offset; k++ )
					{
						accum += std::min( maxContribute, -log1pf( -deepAlpha[k] ) );
					}

					if( accum == 0.0f )
					{
						float newAlpha = -expm1( -targetLog / ( offset - prevOffset ) );
						for( int k = prevOffset; k < offset; k++ )
						{
							result[k] = newAlpha;
						}
					}
					else
					{
						float depthMultiplier = targetLog / accum;

						for( int k = prevOffset; k < offset; k++ )
						{
							result[k] = -expm1( -std::min( maxContribute, -log1pf( -deepAlpha[k] ) ) * depthMultiplier );
						}
					}
				}

				prevOffset = offset;
				i++;
			}
		}
	}
	else
	{
		reusedScope.setChannelName( channelName );

		ConstFloatVectorDataPtr colorSourceChannelData = colorSourcePlug()->channelDataPlug()->getValue();
		const std::vector<float> &colorSourceChannel = colorSourceChannelData->readable();

		for( int y = boundInTile.min.y; y < boundInTile.max.y; y++ )
		{
			int i = y * ImagePlug::tileSize() + boundInTile.min.x;
			int prevOffset = i > 0 ? sampleOffsets[ i - 1 ] : 0;

			for( int j = 0; j < scanlineLength; j++ )
			{
				float csAlpha = colorSourceAlpha[i];
				if( csAlpha == 0.0f )
				{
					csAlpha = 1.0f;
				}
				float unpremult = colorSourceChannel[i] / csAlpha;

				int offset = sampleOffsets[i];
				for( int k = prevOffset; k < offset; k++ )
				{
					result[k] = deepAlpha[k] * unpremult;
				}

				prevOffset = offset;
				i++;
			}
		}
	}

	return resultData;
}

void DeepRecolor::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelNames( output, context, h );

	inPlug()->channelNamesPlug()->hash( h );
	colorSourcePlug()->channelNamesPlug()->hash( h );
}

IECore::ConstStringVectorDataPtr DeepRecolor::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECore::ConstStringVectorDataPtr inChannelsData = inPlug()->channelNamesPlug()->getValue();
	IECore::ConstStringVectorDataPtr colorChannelsData = colorSourcePlug()->channelNamesPlug()->getValue();

	const std::vector< std::string > &inChannels = inChannelsData->readable();

	IECore::StringVectorDataPtr resultData;
	for( const std::string &c : colorChannelsData->readable() )
	{
		if( std::find( inChannels.begin(), inChannels.end(), c ) == inChannels.end() )
		{
			if( !resultData )
			{
				resultData = inChannelsData->copy();
			}
			resultData->writable().push_back( c );
		}
	}

	if( resultData )
	{
		return resultData;
	}
	else
	{
		return inChannelsData;
	}
}
