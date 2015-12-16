//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/Mix.h"

#include "GafferImage/ImageAlgo.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"

#include "IECore/BoxOps.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Mix );

size_t Mix::g_firstPlugIndex = 0;

Mix::Mix( const std::string &name )
	:	FlatImageProcessor( name, 2, 2 )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "mask", Gaffer::Plug::In ) );

	addChild( new FloatPlug( "mix", Plug::In, 1.0f, 0.0f, 1.0f ) );

	addChild( new StringPlug( "maskChannel", Plug::In, "A") );

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
}

Mix::~Mix()
{
}

GafferImage::ImagePlug *Mix::maskPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *Mix::maskPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *Mix::mixPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *Mix::mixPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *Mix::maskChannelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *Mix::maskChannelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

void Mix::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageProcessor::affects( input, outputs );

	if( input == maskChannelPlug() || input == mixPlug() || input == maskPlug()->channelDataPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );

		// The data window and channel names are only affected by the mix
		// because of the pass through if mix is 0, or mix is 1 and mask is unconnected
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->channelNamesPlug() );
	}
	else if( const ImagePlug *inputImage = input->parent<ImagePlug>() )
	{
		if( inputImage->parent<ArrayPlug>() == inPlugs() )
		{
			outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
		}
	}
}

void Mix::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const float mix = mixPlug()->getValue();
	if( mix == 0.0f )
	{
		h = inPlugs()->getChild< ImagePlug>( 0 )->dataWindowPlug()->hash();
		return;
	}
	else if( mix == 1.0f && !maskPlug()->getInput<ValuePlug>() )
	{
		h = inPlugs()->getChild< ImagePlug >( 1 )->dataWindowPlug()->hash();
		return;
	}

	FlatImageProcessor::hashDataWindow( output, context, h );

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		(*it)->dataWindowPlug()->hash( h );
	}
}

Imath::Box2i Mix::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const float mix = mixPlug()->getValue();
	if( mix == 0.0f )
	{
		return inPlugs()->getChild< ImagePlug>( 0 )->dataWindowPlug()->getValue();
	}
	else if( mix == 1.0f && !maskPlug()->getInput<ValuePlug>() )
	{
		return inPlugs()->getChild< ImagePlug >( 1 )->dataWindowPlug()->getValue();
	}

	Imath::Box2i dataWindow;
	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		// We don't need to check that the plug is connected here as unconnected plugs don't have data windows.
		dataWindow.extendBy( (*it)->dataWindowPlug()->getValue() );
	}

	return dataWindow;
}

void Mix::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const float mix = mixPlug()->getValue();
	if( mix == 0.0f )
	{
		h = inPlugs()->getChild< ImagePlug>( 0 )->channelNamesPlug()->hash();
		return;
	}
	else if( mix == 1.0f && !maskPlug()->getInput<ValuePlug>() )
	{
		h = inPlugs()->getChild< ImagePlug >( 1 )->channelNamesPlug()->hash();
		return;
	}

	FlatImageProcessor::hashChannelNames( output, context, h );

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
		{
			(*it)->channelNamesPlug()->hash( h );
		}
	}
}

IECore::ConstStringVectorDataPtr Mix::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const float mix = mixPlug()->getValue();
	if( mix == 0.0f )
	{
		return inPlugs()->getChild< ImagePlug>( 0 )->channelNamesPlug()->getValue();
	}
	else if( mix == 1.0f && !maskPlug()->getInput<ValuePlug>() )
	{
		return inPlugs()->getChild< ImagePlug >( 1 )->channelNamesPlug()->getValue();
	}

	IECore::StringVectorDataPtr outChannelStrVectorData( new IECore::StringVectorData() );
	std::vector<std::string> &outChannels( outChannelStrVectorData->writable() );

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
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

	if ( !outChannels.empty() )
	{
		return outChannelStrVectorData;
	}

	return inPlug()->channelNamesPlug()->defaultValue();
}

void Mix::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const float mix = mixPlug()->getValue();

	if( mix == 0.0f )
	{
		h = inPlugs()->getChild< ImagePlug >( 0 )->channelDataPlug()->hash();
		return;
	}
	else if( mix == 1.0f && !maskPlug()->getInput<ValuePlug>() )
	{
		h = inPlugs()->getChild< ImagePlug >( 1 )->channelDataPlug()->hash();
		return;
	}

	FlatImageProcessor::hashChannelData( output, context, h );
	h.append( mix );

	const std::string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );


	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( !(*it)->getInput<ValuePlug>() )
		{
			continue;
		}

		IECore::ConstStringVectorDataPtr channelNamesData;
		Box2i dataWindow;
		{
			ImagePlug::GlobalScope c( Context::current() );
			channelNamesData = (*it)->channelNamesPlug()->getValue();
			dataWindow = (*it)->dataWindowPlug()->getValue();
		}

		const std::vector<std::string> &channelNames = channelNamesData->readable();

		if( ImageAlgo::channelExists( channelNames, channelName ) )
		{
			(*it)->channelDataPlug()->hash( h );
		}


		// The hash of the channel data we include above represents just the data in
		// the tile itself, and takes no account of the possibility that parts of the
		// tile may be outside of the data window. This simplifies the implementation of
		// nodes like Constant (where all tiles are identical, even the edge tiles) and
		// Crop (which does no processing of tiles at all). For most nodes this doesn't
		// matter, because they don't change the data window, or they use a Sampler to
		// deal with invalid pixels. But because our data window is the union of all
		// input data windows, we may be using/revealing the invalid parts of a tile. We
		// deal with this in computeChannelData() by treating the invalid parts as black,
		// and must therefore hash in the valid bound here to take that into account.
		const Box2i validBound = boxIntersection( tileBound, dataWindow );
		h.append( validBound );
	}

	IECore::ConstStringVectorDataPtr maskChannelNamesData;
	Box2i maskDataWindow;
	{
		ImagePlug::GlobalScope c( Context::current() );
		maskChannelNamesData = maskPlug()->channelNamesPlug()->getValue();
		maskDataWindow = maskPlug()->dataWindowPlug()->getValue();
	}


	const std::string &maskChannel = maskChannelPlug()->getValue();
	if( maskPlug()->getInput<ValuePlug>() && ImageAlgo::channelExists( maskChannelNamesData->readable(), maskChannel ) )
	{
		h.append( maskPlug()->channelDataHash( maskChannel, tileOrigin ) );
	}

	const Box2i maskValidBound = boxIntersection( tileBound, maskDataWindow );
	h.append( maskValidBound );
}

IECore::ConstFloatVectorDataPtr Mix::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{

	const float mix = mixPlug()->getValue();

	if( mix == 0.0f )
	{
		return inPlugs()->getChild< ImagePlug>( 0 )->channelDataPlug()->getValue();
	}
	else if( mix == 1.0f && !maskPlug()->getInput<ValuePlug>() )
	{
		return inPlugs()->getChild< ImagePlug >( 1 )->channelDataPlug()->getValue();
	}

	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	IECore::ConstStringVectorDataPtr maskChannelNamesData;
	Box2i maskDataWindow;
	{
		ImagePlug::GlobalScope c( Context::current() );
		maskChannelNamesData = maskPlug()->channelNamesPlug()->getValue();
		maskDataWindow = maskPlug()->dataWindowPlug()->getValue();
	}

	const std::string &maskChannel = maskChannelPlug()->getValue();
	ConstFloatVectorDataPtr maskData = nullptr;
	Box2i maskValidBound;
	if( maskPlug()->getInput<ValuePlug>() && ImageAlgo::channelExists( maskChannelNamesData->readable(), maskChannel ) )
	{
		maskData = maskPlug()->channelData( maskChannel, tileOrigin );
		maskValidBound = boxIntersection( tileBound, maskDataWindow );
	}

	ConstFloatVectorDataPtr channelData[2];
	Box2i validBound[2];

	int i = 0;
	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it,++i )
	{
		IECore::ConstStringVectorDataPtr channelNamesData;
		Box2i dataWindow;
		{
			ImagePlug::GlobalScope c( Context::current() );
			channelNamesData = (*it)->channelNamesPlug()->getValue();
			dataWindow = (*it)->dataWindowPlug()->getValue();
		}

		const std::vector<std::string> &channelNames = channelNamesData->readable();


		if( ImageAlgo::channelExists( channelNames, channelName ) )
		{
			channelData[i] = (*it)->channelDataPlug()->getValue();
			validBound[i] = boxIntersection( tileBound, dataWindow );
		}
		else
		{
			channelData[i] = nullptr;
			validBound[i] = Box2i();
		}

	}


	FloatVectorDataPtr resultData = ImagePlug::blackTile()->copy();
	float *R = &resultData->writable().front();
	const float *A = channelData[0] ? &channelData[0]->readable().front() : nullptr;
	const float *B = channelData[1] ? &channelData[1]->readable().front() : nullptr;
	const float *M = maskData ? &maskData->readable().front() : nullptr;

	for( int y = tileBound.min.y; y < tileBound.max.y; ++y )
	{
		const bool yValidIn0 = y >= validBound[0].min.y && y < validBound[0].max.y;
		const bool yValidIn1 = y >= validBound[1].min.y && y < validBound[1].max.y;
		const bool yValidMask = y >= maskValidBound.min.y && y < maskValidBound.max.y;

		for( int x = tileBound.min.x; x < tileBound.max.x; ++x )
		{
			float a = 0;
			if( yValidIn0 && x >= validBound[0].min.x && x < validBound[0].max.x )
			{
				a = *A;
			}

			float b = 0;
			if( yValidIn1 && x >= validBound[1].min.x && x < validBound[1].max.x )
			{
				b = *B;
			}

			float m = mix;
			if( yValidMask && x >= maskValidBound.min.x && x < maskValidBound.max.x )
			{
				m *= std::max( 0.0f, std::min( 1.0f, *M ) );
			}

			*R = a * ( 1 - m ) + b * m;

			++R; ++A; ++B; ++M;
		}
	}

	return resultData;
}

void Mix::hashDeepState( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const float mix = mixPlug()->getValue();

	if( mix == 0.0f )
	{
		// If the mix is 0, we are totally a pass-through, and we don't even check if the image is deep
		h = inPlugs()->getChild< ImagePlug >( 0 )->deepStatePlug()->hash();
	}
	else if( mix == 1.0f && !maskPlug()->getInput<ValuePlug>() )
	{
		// If the mix is 1, and there is no mask, we are totally a pass-through,
		// and we don't even check if the image is deep
		h = inPlugs()->getChild< ImagePlug >( 1 )->deepStatePlug()->hash();
	}
	else
	{
		// This changes the hash so that our compute is called, and we can check if the deep state is valid
		FlatImageProcessor::hashDeepState( parent, context, h );
	}
}

// TODO - need to override computeDeepState
