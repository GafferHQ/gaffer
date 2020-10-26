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

#include "GafferImage/Merge.h"

#include "GafferImage/ImageAlgo.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"

#include "IECore/BoxOps.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

namespace
{

float opAdd( float A, float B, float a, float b){ return A + B; }
float opAtop( float A, float B, float a, float b){ return A*b + B*(1.-a); }
float opDivide( float A, float B, float a, float b){ return A / B; }
float opIn( float A, float B, float a, float b){ return A*b; }
float opOut( float A, float B, float a, float b){ return A*(1.-b); }
float opMask( float A, float B, float a, float b){ return B*a; }
float opMatte( float A, float B, float a, float b){ return A*a + B*(1.-a); }
float opMultiply( float A, float B, float a, float b){ return A * B; }
float opOver( float A, float B, float a, float b){ return A + B*(1.-a); }
float opSubtract( float A, float B, float a, float b){ return A - B; }
float opDifference( float A, float B, float a, float b){ return fabs( A - B ); }
float opUnder( float A, float B, float a, float b){ return A*(1.-b) + B; }
float opMin( float A, float B, float a, float b){ return std::min( A, B ); }
float opMax( float A, float B, float a, float b){ return std::max( A, B ); }

} // namespace

GAFFER_NODE_DEFINE_TYPE( Merge );

size_t Merge::g_firstPlugIndex = 0;

Merge::Merge( const std::string &name )
	:	FlatImageProcessor( name, 2 )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild(
		new IntPlug(
			"operation", // name
			Plug::In,    // direction
			Add,         // default
			Add,         // min
			Max          // the maximum value in the enum, which just happens to currently be named "Max"
		)
	);

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
}

Merge::~Merge()
{
}

Gaffer::IntPlug *Merge::operationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Merge::operationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

void Merge::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageProcessor::affects( input, outputs );

	if( input == operationPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( const ImagePlug *inputImage = input->parent<ImagePlug>() )
	{
		if( inputImage->parent<ArrayPlug>() == inPlugs() )
		{
			outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
		}
	}
}

void Merge::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashDataWindow( output, context, h );

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
		{
			(*it)->dataWindowPlug()->hash( h );
		}
	}
}

Imath::Box2i Merge::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Imath::Box2i dataWindow;
	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		// We don't need to check that the plug is connected here as unconnected plugs don't have data windows.
		dataWindow.extendBy( (*it)->dataWindowPlug()->getValue() );
	}

	return dataWindow;
}

void Merge::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashChannelNames( output, context, h );

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
		{
			(*it)->channelNamesPlug()->hash( h );
		}
	}
}

IECore::ConstStringVectorDataPtr Merge::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
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

void Merge::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashChannelData( output, context, h );

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
			ImagePlug::GlobalScope c( context );
			channelNamesData = (*it)->channelNamesPlug()->getValue();
			dataWindow = (*it)->dataWindowPlug()->getValue();
		}

		const Box2i validBound = boxIntersection( tileBound, dataWindow );
		if( BufferAlgo::empty( validBound ) )
		{
			h.append( 0 );
		}
		else
		{
			const std::vector<std::string> &channelNames = channelNamesData->readable();

			if( ImageAlgo::channelExists( channelNames, channelName ) )
			{
				(*it)->channelDataPlug()->hash( h );
			}

			if( ImageAlgo::channelExists( channelNames, "A" ) )
			{
				h.append( (*it)->channelDataHash( "A", tileOrigin ) );
			}
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
		h.append( validBound );
	}

	operationPlug()->hash( h );
}

IECore::ConstFloatVectorDataPtr Merge::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	switch( operationPlug()->getValue() )
	{
		case Add :
			return merge( opAdd, channelName, tileOrigin);
		case Atop :
			return merge( opAtop, channelName, tileOrigin);
		case Divide :
			return merge( opDivide, channelName, tileOrigin);
		case In :
			return merge( opIn, channelName, tileOrigin);
		case Out :
			return merge( opOut, channelName, tileOrigin);
		case Mask :
			return merge( opMask, channelName, tileOrigin);
		case Matte :
			return merge( opMatte, channelName, tileOrigin);
		case Multiply :
			return merge( opMultiply, channelName, tileOrigin);
		case Over :
			return merge( opOver, channelName, tileOrigin);
		case Subtract :
			return merge( opSubtract, channelName, tileOrigin);
		case Difference :
			return merge( opDifference, channelName, tileOrigin);
		case Under :
			return merge( opUnder, channelName, tileOrigin);
		case Min :
			return merge( opMin, channelName, tileOrigin);
		case Max :
			return merge( opMax, channelName, tileOrigin);
	}

	throw Exception( "Merge::computeChannelData : Invalid operation mode." );
}

template<typename F>
IECore::ConstFloatVectorDataPtr Merge::merge( F f, const std::string &channelName, const Imath::V2i &tileOrigin ) const
{
	FloatVectorDataPtr resultData = nullptr;
	// Temporary buffer for computing the alpha of intermediate composited layers.
	FloatVectorDataPtr resultAlphaData = nullptr;

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

		ConstFloatVectorDataPtr channelData;
		ConstFloatVectorDataPtr alphaData;

		const Box2i validBound = boxIntersection( tileBound, dataWindow );

		if( ImageAlgo::channelExists( channelNames, channelName ) && !BufferAlgo::empty( validBound ) )
		{
			channelData = (*it)->channelDataPlug()->getValue();
		}
		else
		{
			channelData = ImagePlug::blackTile();
		}

		if( ImageAlgo::channelExists( channelNames, "A" ) && !BufferAlgo::empty( validBound ) )
		{
			alphaData = (*it)->channelData( "A", tileOrigin );
		}
		else
		{
			alphaData = ImagePlug::blackTile();
		}

		if( (int)alphaData->readable().size() != ImagePlug::tilePixels()  )
		{
			throw IECore::Exception( "Merge::computeChannelData : Cannot process deep data." );
		}
		if( (int)channelData->readable().size() != ImagePlug::tilePixels() )
		{
			throw IECore::Exception( "Merge::computeChannelData : Cannot process deep data." );
		}

		if( !resultData )
		{
			// The first connected layer, with which we must initialise our result.
			// There's no guarantee that this layer actually covers the full data
			// window though (the data window could have been expanded by the upper
			// layers) so we must take care to mask out any invalid areas of the input.
			/// \todo I'm not convinced this is correct - if we have no connection
			/// to in[0] then should that not be treated as being a black image, so
			/// we should unconditionally initaliase with in[0] and then always use
			/// the operation for in[1:], even if in[0] is disconnected. In other
			/// words, shouldn't multiplying a white constant over an unconnected
			/// in[0] produce black?
			resultData = channelData->copy();
			resultAlphaData = alphaData->copy();
			float *B = &resultData->writable().front();
			float *b = &resultAlphaData->writable().front();
			for( int y = tileBound.min.y; y < tileBound.max.y; ++y )
			{
				const bool yValid = y >= validBound.min.y && y < validBound.max.y;
				for( int x = tileBound.min.x; x < tileBound.max.x; ++x )
				{
					if( !yValid || x < validBound.min.x || x >= validBound.max.x )
					{
						*B = *b = 0.0f;
					}
					++B; ++b;
				}
			}
		}
		else
		{
			// A higher layer (A) which must be composited over the result (B).
			const float *A = &channelData->readable().front();
			float *B = &resultData->writable().front();
			const float *a = &alphaData->readable().front();
			float *b = &resultAlphaData->writable().front();

			for( int y = tileBound.min.y; y < tileBound.max.y; ++y )
			{
				const bool yValid = y >= validBound.min.y && y < validBound.max.y;
				for( int x = tileBound.min.x; x < tileBound.max.x; ++x )
				{
					const bool valid = yValid && x >= validBound.min.x && x < validBound.max.x;

					*B = f( valid ? *A : 0.0f, *B, valid ? *a : 0.0f, *b );
					*b = f( valid ? *a : 0.0f, *b, valid ? *a : 0.0f, *b );

					++A; ++B; ++a; ++b;
				}
			}
		}
	}

	return resultData;
}
