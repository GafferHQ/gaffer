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

#include "Gaffer/Context.h"

#include "GafferImage/FlatToDeep.h"
#include "GafferImage/ImageAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

GAFFER_NODE_DEFINE_TYPE( FlatToDeep );

size_t FlatToDeep::g_firstPlugIndex = 0;

FlatToDeep::FlatToDeep( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "zMode", Plug::In, int(ZMode::Constant),
		int(ZMode::Constant), int(ZMode::Channel )
	) );
	addChild( new FloatPlug( "depth" ) );
	addChild( new StringPlug( "zChannel", Plug::In, "Z" ) );

	addChild( new IntPlug( "zBackMode", Plug::In, int(ZBackMode::None),
		int(ZBackMode::None), int(ZBackMode::Channel )
	) );
	addChild( new FloatPlug( "thickness", Plug::In, 0.0f, 0.0f ) );
	addChild( new StringPlug( "zBackChannel", Plug::In, "ZBack" ) );


	// Pass-through the things we don't want to modify.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
}

FlatToDeep::~FlatToDeep()
{
}

IntPlug *FlatToDeep::zModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const IntPlug *FlatToDeep::zModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

FloatPlug *FlatToDeep::depthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const FloatPlug *FlatToDeep::depthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

StringPlug *FlatToDeep::zChannelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const StringPlug *FlatToDeep::zChannelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

IntPlug *FlatToDeep::zBackModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

const IntPlug *FlatToDeep::zBackModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

FloatPlug *FlatToDeep::thicknessPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

const FloatPlug *FlatToDeep::thicknessPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

StringPlug *FlatToDeep::zBackChannelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

const StringPlug *FlatToDeep::zBackChannelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

void FlatToDeep::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if(
		input == inPlug()->channelNamesPlug() ||
		input == zBackModePlug()
	)
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
	}

	if(
		input == inPlug()->channelDataPlug() ||
		input == zModePlug() ||
		input == zChannelPlug() ||
		input == depthPlug() ||
		input == inPlug()->channelNamesPlug() ||
		input == zBackModePlug() ||
		input == zBackChannelPlug() ||
		input == thicknessPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void FlatToDeep::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelNames( output, context, h );
	inPlug()->channelNamesPlug()->hash( h );
	zBackModePlug()->hash( h );
}

IECore::ConstStringVectorDataPtr FlatToDeep::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	StringVectorDataPtr resultData = inPlug()->channelNamesPlug()->getValue()->copy();
	vector<string> &result = resultData->writable();

	if( find( result.begin(), result.end(), "Z" ) == result.end() )
	{
		result.push_back( "Z" );
	}

	if( ZBackMode( zBackModePlug()->getValue() ) != ZBackMode::None &&
		find( result.begin(), result.end(), "ZBack" ) == result.end()
	)
	{
		result.push_back( "ZBack" );
	}

	return resultData;
}

void FlatToDeep::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( output, context, h );
	const std::string channelName = context->get<std::string>( ImagePlug::channelNameContextName );

	if( !( channelName == "Z" || channelName == "ZBack" ) )
	{
		h = inPlug()->channelDataPlug()->hash();
		return;
	}

	ImagePlug::ChannelDataScope reusedScope( context );
	reusedScope.remove( ImagePlug::tileOriginContextName );
	reusedScope.remove( ImagePlug::channelNameContextName );

	ZMode zMode = ZMode( zModePlug()->getValue() );
	const std::string zChannel = zChannelPlug()->getValue();

	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

	if ( channelName == "Z" )
	{
		if( zMode == ZMode::Constant )
		{
			depthPlug()->hash( h );
		}
		else
		{
			ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
			const vector<string> &channelNames = channelNamesData->readable();

			if( find( channelNames.begin(), channelNames.end(), zChannel ) == channelNames.end() )
			{
				throw( IECore::Exception( "FlatToDeep : Cannot find requested Z channel - no channel \""
					+ zChannel + "\" found."
				) );
			}

			reusedScope.setTileOrigin( &tileOrigin );
			reusedScope.setChannelName( &zChannel );
			h = inPlug()->channelDataPlug()->hash();
		}
	}
	else
	{
		ZBackMode zBackMode = ZBackMode( zBackModePlug()->getValue() );
		const std::string zBackChannel = zBackChannelPlug()->getValue();

		if( zMode == ZMode::Constant && zBackMode == ZBackMode::Thickness )
		{
			depthPlug()->hash( h );
			thicknessPlug()->hash( h );
		}
		else
		{
			ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
			const vector<string> &channelNames = channelNamesData->readable();

			if( zBackMode == ZBackMode::Channel )
			{
				if( find( channelNames.begin(), channelNames.end(), zBackChannel ) == channelNames.end() )
				{
					throw( IECore::Exception( "FlatToDeep : Cannot find requested ZBack channel - no channel \""
						+ zBackChannel + "\" found."
					) );
				}
				reusedScope.setTileOrigin( &tileOrigin );
				reusedScope.setChannelName( &zBackChannel );
				h = inPlug()->channelDataPlug()->hash();
			}
			else
			{
				thicknessPlug()->hash( h );

				reusedScope.setTileOrigin( &tileOrigin );
				reusedScope.setChannelName( &zChannel );
				outPlug()->channelDataPlug()->hash(h);
			}
		}
	}
}

IECore::ConstFloatVectorDataPtr FlatToDeep::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( !( channelName == "Z" || channelName == "ZBack" ) )
	{
		return inPlug()->channelDataPlug()->getValue();
	}

	ImagePlug::ChannelDataScope reusedScope( context );
	reusedScope.remove( ImagePlug::tileOriginContextName );
	reusedScope.remove( ImagePlug::channelNameContextName );

	ZMode zMode = ZMode( zModePlug()->getValue() );
	const std::string zChannel = zChannelPlug()->getValue();

	if ( channelName == "Z" )
	{
		if( zMode == ZMode::Constant )
		{
			// Set constant Z
			float depth = depthPlug()->getValue();
			FloatVectorDataPtr resultData = new FloatVectorData;
			resultData->writable().resize( ImagePlug::tilePixels(), depth );

			return resultData;
		}
		else
		{

			ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
			const vector<string> &channelNames = channelNamesData->readable();

			// Pass through Z
			if( find( channelNames.begin(), channelNames.end(), zChannel ) == channelNames.end() )
			{
				throw( IECore::Exception( "FlatToDeep : Cannot find requested Z channel - no channel \""
					+ zChannel + "\" found."
				) );
			}

			reusedScope.setTileOrigin( &tileOrigin );
			reusedScope.setChannelName( &zChannel );
			return inPlug()->channelDataPlug()->getValue();
		}
	}
	else
	{
		ZBackMode zBackMode = ZBackMode( zBackModePlug()->getValue() );
		const std::string zBackChannel = zBackChannelPlug()->getValue();

		if( zMode == ZMode::Constant && zBackMode == ZBackMode::Thickness )
		{
			// Set constant ZBack from depth and thickness
			float depth = depthPlug()->getValue();
			float thickness = thicknessPlug()->getValue();
			FloatVectorDataPtr resultData = new FloatVectorData;
			resultData->writable().resize( ImagePlug::tilePixels(), depth + thickness );

			return resultData;
		}
		else
		{
			ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
			const vector<string> &channelNames = channelNamesData->readable();

			if( zBackMode == ZBackMode::Channel )
			{
				// Pass through ZBack
				if( find( channelNames.begin(), channelNames.end(), zBackChannel ) == channelNames.end() )
				{
					throw( IECore::Exception( "FlatToDeep : Cannot find requested ZBack channel - no channel \""
						+ zBackChannel + "\" found."
					) );
				}

				reusedScope.setTileOrigin( &tileOrigin );
				reusedScope.setChannelName( &zBackChannel );
				return inPlug()->channelDataPlug()->getValue();
			}
			else
			{
				// Compute ZBack by combining incoming Z with thickness
				float thickness = thicknessPlug()->getValue();

				reusedScope.setTileOrigin( &tileOrigin );
				reusedScope.setChannelName( &zChannel );
				FloatVectorDataPtr resultData = outPlug()->channelDataPlug()->getValue()->copy();
				vector<float> &result = resultData->writable();
				for( float &i : result )
				{
					i += thickness;
				}
				return resultData;
			}
		}
	}
}

void FlatToDeep::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashDeep( parent, context, h );
}

bool FlatToDeep::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return true;
}

void FlatToDeep::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = ImagePlug::flatTileSampleOffsets()->IECore::Object::hash();
}

IECore::ConstIntVectorDataPtr FlatToDeep::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::flatTileSampleOffsets();
}

