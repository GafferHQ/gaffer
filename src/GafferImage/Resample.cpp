//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
//      * Neither the name of Image Engine Design nor the names of
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

#include "GafferImage/Resample.h"

#include "GafferImage/FilterAlgo.h"
#include "GafferImage/Sampler.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "OpenImageIO/filter.h"
#include "OpenImageIO/fmath.h"

#include <iostream>

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// Used as a bitmask to say which filter pass(es) we're computing.
enum Passes
{
	Horizontal = 1,
	Vertical = 2,
	Both = Horizontal | Vertical
};

unsigned requiredPasses( const Resample *resample, const ImagePlug *image, const OIIO::Filter2D *filter )
{
	int debug = resample->debugPlug()->getValue();
	if( debug == Resample::HorizontalPass )
	{
		return Horizontal;
	}
	else if( debug == Resample::SinglePass )
	{
		return Horizontal | Vertical;
	}

	if( image == image->parent<ImageNode>()->outPlug() )
	{
		return filter->separable() ? Vertical : Both;
	}
	return Horizontal;
}

// Rounds min down, and max up, while converting from float to int.
Box2i box2fToBox2i( const Box2f &b )
{
	return Box2i(
		V2i( floor( b.min.x ), floor( b.min.y ) ),
		V2i( ceil( b.max.x ), ceil( b.max.y ) )
	);
}

// Calculates the scale and offset needed to convert from output
// coordinates to input coordinates.
void ratioAndOffset( const M33f &matrix, V2f &ratio, V2f &offset )
{
	ratio = V2f( matrix[0][0], matrix[1][1] );
	offset = -V2f( matrix[2][0], matrix[2][1] ) / ratio;
}

// The radius for the filter is specified in the output space. This
// method returns it as a number of pixels in the input space.
V2i inputFilterRadius( const OIIO::Filter2D *filter, const V2f &inputFilterScale )
{
	return V2i(
		(int)ceilf( filter->width() * inputFilterScale.x * 0.5f ),
		(int)ceilf( filter->height() * inputFilterScale.y * 0.5f )
	);
}

// Returns the input region that will need to be sampled when
// generating a given output tile.
Box2i inputRegion( const V2i &tileOrigin, unsigned passes, const V2f &ratio, const V2f &offset, const OIIO::Filter2D *filter, const V2f &inputFilterScale )
{
	Box2f outputRegion( V2f( tileOrigin ), tileOrigin + V2f( ImagePlug::tileSize() ) );
	V2i filterRadius = inputFilterRadius( filter, inputFilterScale );

	Box2f result = outputRegion;
	if( passes & Horizontal )
	{
		result.min.x = result.min.x / ratio.x + offset.x;
		result.max.x = result.max.x / ratio.x + offset.x;
		if( result.min.x > result.max.x )
		{
			// Correct for negative scaling inverting
			// the relationship between min and max.
			std::swap( result.min.x, result.max.x );
		}
		result.min.x -= filterRadius.x;
		result.max.x += filterRadius.x;
	}
	if( passes & Vertical )
	{
		result.min.y = result.min.y / ratio.y + offset.y;
		result.max.y = result.max.y / ratio.y + offset.y;
		if( result.min.y > result.max.y )
		{
			std::swap( result.min.y, result.max.y );
		}
		result.min.y -= filterRadius.y;
		result.max.y += filterRadius.y;
	}

	return box2fToBox2i( result );
}

// Given a filter name, the current scaling ratio of input size / output size, and the desired filter scale in
// output space, return a filter and the correct filter scale in input space
const OIIO::Filter2D *filterAndScale( const std::string &name, V2f ratio, V2f &inputFilterScale )
{
	ratio.x = fabs( ratio.x );
	ratio.y = fabs( ratio.y );

	const OIIO::Filter2D *result;
	if( name == "" )
	{
		if( ratio.x > 1.0f || ratio.y > 1.0f )
		{
			// Upsizing
			result = FilterAlgo::acquireFilter( "blackman-harris" );
		}
		else
		{
			// Downsizing
			result = FilterAlgo::acquireFilter( "lanczos3" );
		}
	}
	else
	{
		result = FilterAlgo::acquireFilter( name );
	}

	// Convert the filter scale into input space
	inputFilterScale = V2f( 1.0f ) / ratio;

	// Don't allow the filter scale to cover less than 1 pixel in input space
	inputFilterScale = V2f( std::max( 1.0f, inputFilterScale.x ), std::max( 1.0f, inputFilterScale.y ) );

	return result;
}

// Precomputes all the filter weights for a whole row or column of a tile. For separable
// filters these weights can then be reused across all rows/columns in the same tile.
/// \todo The weights computed for a particular tile could also be reused for all
/// tiles in the same tile column or row. We could achieve this by outputting
/// the weights on an internal plug, and using Gaffer's caching to ensure they are
/// only computed once and then reused. At the time of writing, profiles indicate that
/// accessing pixels via the Sampler is the main bottleneck, but once that is optimised
/// perhaps cached filter weights could have a benefit.
void filterWeights( const OIIO::Filter2D *filter, const float inputFilterScale, const int filterRadius, const int x, const float ratio, const float offset, Passes pass, std::vector<float> &weights )
{
	weights.reserve( ( 2 * filterRadius + 1 ) * ImagePlug::tileSize() );

	const float filterCoordinateMult = 1.0f / inputFilterScale;

	float iX; // input pixel position (floating point)
	int iXI; // input pixel position (floored to int)
	float iXF; // fractional part of input pixel position after flooring
	for( int oX = x, eX = x + ImagePlug::tileSize(); oX < eX; ++oX )
	{
		iX = ( oX + 0.5 ) / ratio + offset;
		iXF = OIIO::floorfrac( iX, &iXI );

		int fX; // relative filter position
		for( fX = -filterRadius; fX<= filterRadius; ++fX )
		{
			const float f = filterCoordinateMult * (fX - ( iXF - 0.5f ) );
			const float w = pass == Horizontal ? filter->xfilt( f ) : filter->yfilt( f );
			weights.push_back( w );
		}
	}
}

Box2f transform( const Box2f &b, const M33f &m )
{
	if( b.isEmpty() )
	{
		return b;
	}

	Box2f r;
	r.extendBy( V2f( b.min.x, b.min.y ) * m );
	r.extendBy( V2f( b.max.x, b.min.y ) * m );
	r.extendBy( V2f( b.max.x, b.max.y ) * m );
	r.extendBy( V2f( b.min.x, b.max.y ) * m );
	return r;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Resample
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Resample );

size_t Resample::g_firstPlugIndex = 0;

Resample::Resample( const std::string &name )
	:   FlatImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new M33fPlug( "matrix" ) );
	addChild( new StringPlug( "filter" ) );
	addChild( new V2fPlug( "filterScale", Plug::In, V2f( 1 ), V2f( 0 ) ) );
	addChild( new IntPlug( "boundingMode", Plug::In, Sampler::Black, Sampler::Black, Sampler::Clamp ) );
	addChild( new BoolPlug( "expandDataWindow" ) );
	addChild( new IntPlug( "debug", Plug::In, Off, Off, SinglePass ) );
	addChild( new ImagePlug( "__horizontalPass", Plug::Out ) );

	// We don't ever want to change these, so we make pass-through connections.

	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );

	horizontalPassPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );
	horizontalPassPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	horizontalPassPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	horizontalPassPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );

	// Sampler checks the deep plug, and FlatImageProcessor doesn't handle the deep
	// plug for outputs other than outPlug(), so up a passthrough for deep to avoid
	// needing to implement hash/compute for it
	horizontalPassPlug()->deepPlug()->setInput( inPlug()->deepPlug() );
}

Resample::~Resample()
{
}

Gaffer::M33fPlug *Resample::matrixPlug()
{
	return getChild<M33fPlug>( g_firstPlugIndex );
}

const Gaffer::M33fPlug *Resample::matrixPlug() const
{
	return getChild<M33fPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *Resample::filterPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *Resample::filterPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::V2fPlug *Resample::filterScalePlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::V2fPlug *Resample::filterScalePlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

Gaffer::IntPlug *Resample::boundingModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::IntPlug *Resample::boundingModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

Gaffer::BoolPlug *Resample::expandDataWindowPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::BoolPlug *Resample::expandDataWindowPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

Gaffer::IntPlug *Resample::debugPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::IntPlug *Resample::debugPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

ImagePlug *Resample::horizontalPassPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 6 );
}

const ImagePlug *Resample::horizontalPassPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 6 );
}

void Resample::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageProcessor::affects( input, outputs );

	if(
		input == inPlug()->dataWindowPlug() ||
		input == matrixPlug() ||
		input == expandDataWindowPlug() ||
		input == filterPlug() ||
		input->parent<V2fPlug>() == filterScalePlug() ||
		input == debugPlug()
	)
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( horizontalPassPlug()->dataWindowPlug() );
	}

	if(
		input == inPlug()->dataWindowPlug() ||
		input == matrixPlug() ||
		input == filterPlug() ||
		input->parent<V2fPlug>() == filterScalePlug() ||
		input == inPlug()->channelDataPlug() ||
		input == boundingModePlug() ||
		input == debugPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
		outputs.push_back( horizontalPassPlug()->channelDataPlug() );
	}
}

void Resample::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashDataWindow( parent, context, h );

	inPlug()->dataWindowPlug()->hash( h );
	matrixPlug()->hash( h );
	expandDataWindowPlug()->hash( h );
	filterPlug()->hash( h );
	filterScalePlug()->hash( h );
	debugPlug()->hash( h );
}

Imath::Box2i Resample::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const Box2i srcDataWindow = inPlug()->dataWindowPlug()->getValue();
	if( BufferAlgo::empty( srcDataWindow ) )
	{
		return srcDataWindow;
	}

	// Figure out our data window as a Box2f with fractional
	// pixel values.

	const M33f matrix = matrixPlug()->getValue();
	Box2f dstDataWindow = transform( Box2f( srcDataWindow.min, srcDataWindow.max ), matrix );

	if( expandDataWindowPlug()->getValue() )
	{
		V2f ratio, offset;
		ratioAndOffset( matrix, ratio, offset );

		V2f inputFilterScale;
		const OIIO::Filter2D *filter = filterAndScale( filterPlug()->getValue(), ratio, inputFilterScale );
		inputFilterScale *= filterScalePlug()->getValue();

		const V2f filterRadius = V2f( filter->width(), filter->height() ) * inputFilterScale * 0.5f;

		dstDataWindow.min -= filterRadius * ratio;
		dstDataWindow.max += filterRadius * ratio;
	}

	// Convert that Box2f to a Box2i that fully encloses it.
	// Cheat a little to avoid adding additional pixels when
	// we're really close to the edge. This is primarily to
	// meet user expectations in the Resize node, where it is
	// expected that the dataWindow will exactly match the format.

	const float eps = 1e-4;
	if( ceilf( dstDataWindow.min.x ) - dstDataWindow.min.x < eps )
	{
		dstDataWindow.min.x = ceilf( dstDataWindow.min.x );
	}
	if( dstDataWindow.max.x - floorf( dstDataWindow.max.x ) < eps )
	{
		dstDataWindow.max.x = floorf( dstDataWindow.max.x );
	}
	if( ceilf( dstDataWindow.min.y ) - dstDataWindow.min.y < eps )
	{
		dstDataWindow.min.y = ceilf( dstDataWindow.min.y );
	}
	if( dstDataWindow.max.y - floorf( dstDataWindow.max.y ) < eps )
	{
		dstDataWindow.max.y = floorf( dstDataWindow.max.y );
	}

	Box2i dataWindow = box2fToBox2i( dstDataWindow );

	// If we're outputting the horizontal pass, then replace
	// the vertical range with the original.

	if( parent  == horizontalPassPlug() || debugPlug()->getValue() == HorizontalPass )
	{
		dataWindow.min.y = srcDataWindow.min.y;
		dataWindow.max.y = srcDataWindow.max.y;
	}

	return dataWindow;
}

void Resample::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashChannelData( parent, context, h );

	V2f ratio, offset;
	{
		ImagePlug::GlobalScope c( context );
		ratioAndOffset( matrixPlug()->getValue(), ratio, offset );
	}

	V2f inputFilterScale;
	const OIIO::Filter2D *filter = filterAndScale( filterPlug()->getValue(), ratio, inputFilterScale );
	inputFilterScale *= filterScalePlug()->getValue();

	filterPlug()->hash( h );

	const unsigned passes = requiredPasses( this, parent, filter );
	if( passes & Horizontal )
	{
		h.append( inputFilterScale.x );
		h.append( ratio.x );
		h.append( offset.x );
	}
	if( passes & Vertical )
	{
		h.append( inputFilterScale.y );
		h.append( ratio.y );
		h.append( offset.y );
	}

	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	Sampler sampler(
		passes == Vertical ? horizontalPassPlug() : inPlug(),
		context->get<std::string>( ImagePlug::channelNameContextName ),
		inputRegion( tileOrigin, passes, ratio, offset, filter, inputFilterScale ),
		(Sampler::BoundingMode)boundingModePlug()->getValue()
	);
	sampler.hash( h );

	// Another tile might happen to need to filter over the same input
	// tiles as this one, so we must include the tile origin to make sure
	// each tile has a unique hash.
	h.append( tileOrigin );
}

IECore::ConstFloatVectorDataPtr Resample::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	V2f ratio, offset;
	{
		ImagePlug::GlobalScope c( context );
		ratioAndOffset( matrixPlug()->getValue(), ratio, offset );
	}

	V2f inputFilterScale;
	const OIIO::Filter2D *filter = filterAndScale( filterPlug()->getValue(), ratio, inputFilterScale );
	inputFilterScale *= filterScalePlug()->getValue();

	const unsigned passes = requiredPasses( this, parent, filter );

	Sampler sampler(
		passes == Vertical ? horizontalPassPlug() : inPlug(),
		channelName,
		inputRegion( tileOrigin, passes, ratio, offset, filter, inputFilterScale ),
		(Sampler::BoundingMode)boundingModePlug()->getValue()
	);

	const V2i filterRadius = inputFilterRadius( filter, inputFilterScale );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	FloatVectorDataPtr resultData = new FloatVectorData;
	resultData->writable().resize( ImagePlug::tileSize() * ImagePlug::tileSize() );
	std::vector<float>::iterator pIt = resultData->writable().begin();

	if( passes == Both )
	{
		// When the filter isn't separable we must perform all the
		// filtering in a single pass. This version also provides
		// a reference implementation against which the two-pass
		// version can be validated - use the SinglePass debug mode
		// to force the use of this code path.

		V2i oP; // output pixel position
		V2f iP; // input pixel position (floating point)
		V2i iPI; // input pixel position (floored to int)
		V2f iPF; // fractional part of input pixel position after flooring

		V2f	filterCoordinateMult = V2f(1.0f) / inputFilterScale;

		for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
		{
			iP.y = ( oP.y + 0.5 ) / ratio.y + offset.y;
			iPF.y = OIIO::floorfrac( iP.y, &iPI.y );

			for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
			{
				Canceller::check( context->canceller() );

				iP.x = ( oP.x + 0.5 ) / ratio.x + offset.x;
				iPF.x = OIIO::floorfrac( iP.x, &iPI.x );

				// \todo : When refactoring the filter code, I seem to have introduced a performance
				// regression here: in a worst case test of a 20x20 box filter using the debug parameter
				// to force non-separable, the time was 22 seconds originally, went down to 12 seconds
				// after the Sampler optimization, but is now back up to 14.
				//
				// It seems this may just be due to the extra divide by inputFilterScale above, which is
				// somewhat surprising, but I can reduce this time to 13 seconds by hoisting some
				// multiplies out of this loop, so this code does seem quite sensitive ( assuming my
				// test checks out - I'm not spending much time verifying now that I've realized this
				// code is probably going to need an overhaul anyway ).
				//
				// There seems to be a more important issue here that will need revisiting for performance
				// - this currently has the potential to hit a lot of extra pixels.  Consider a filter
				// with a width of 2.1 in X in input space. Depending on how it lines up, usually 2 or
				// occasionally 3 columns of pixel centers will lie inside this window.  However, currently,
				// we will take 2.1, compute an integer filterRadius of ceil( 2.1 / 2.0 ) == 2, and then
				// access 5 columns from (fP.x - 2) to (fP.x + 2 ).  Once both axes are taken into account,
				// this means that a filter that usually only needs to access 4 input pixels will instead
				// always access 25.  This is a worst case example, but it seems like it would definitely
				// be worth the couple of extra floor/ceils per output pixel to only access pixels where the
				// center is actually within the filter support.  This fix should also be done to the
				// seperable case.  Once that is done, we should probably also hoist the multiply by
				// filterCoordinateMult out of the loop.

				V2i fP; // relative filter position
				float v = 0.0f;
				float totalW = 0.0f;
				for( fP.y = -filterRadius.y; fP.y<= filterRadius.y; ++fP.y )
				{
					for( fP.x = -filterRadius.x; fP.x<= filterRadius.x; ++fP.x )
					{
						const float w = (*filter)(
							filterCoordinateMult.x * (fP.x - ( iPF.x - 0.5f )),
							filterCoordinateMult.y * (fP.y - ( iPF.y - 0.5f ))
						);

						if( w == 0.0f )
						{
							continue;
						}

						v += w * sampler.sample( iPI.x + fP.x, iPI.y + fP.y );
						totalW += w;
					}
				}

				if( totalW != 0.0f )
				{
					*pIt = v / totalW;
				}

				++pIt;
			}
		}
	}
	else if( passes == Horizontal )
	{
		// When the filter is separable we can perform filtering in two
		// passes, one for the horizontal and one for the vertical. We
		// output the horizontal pass on the horizontalPassPlug() so that
		// it is cached for use in the vertical pass. The HorizontalPass
		// debug mode causes this pass to be output directly for inspection.

		// Pixels in the same column share the same filter weights, so
		// we precompute the weights now to avoid repeating work later.
		std::vector<float> weights;
		filterWeights( filter, inputFilterScale.x, filterRadius.x, tileBound.min.x, ratio.x, offset.x, Horizontal, weights );

		V2i oP; // output pixel position
		float iX; // input pixel x coordinate (floating point)
		int iXI; // input pixel position (floored to int)

		for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
		{
			Canceller::check( context->canceller() );

			std::vector<float>::const_iterator wIt = weights.begin();
			for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
			{

				iX = ( oP.x + 0.5 ) / ratio.x + offset.x;
				OIIO::floorfrac( iX, &iXI );

				float v = 0.0f;
				float totalW = 0.0f;

				sampler.visitPixels( Imath::Box2i(
						Imath::V2i( iXI - filterRadius.x, oP.y ),
						Imath::V2i( iXI + filterRadius.x + 1, oP.y + 1 )
					),
					[&wIt, &v, &totalW]( float cur, int x, int y )
					{
						const float w = *wIt++;
						v += w * cur;
						totalW += w;
					}
				);

				if( totalW != 0.0f )
				{
					*pIt = v / totalW;
				}

				++pIt;
			}
		}
	}
	else if( passes == Vertical )
	{
		V2i oP; // output pixel position
		float iY; // input pixel position (floating point)
		int iYI; // input pixel position (floored to int)

		// Pixels in the same row share the same filter weights, so
		// we precompute the weights now to avoid repeating work later.
		std::vector<float> weights;
		filterWeights( filter, inputFilterScale.y, filterRadius.y, tileBound.min.y, ratio.y, offset.y, Vertical, weights );

		for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
		{
			Canceller::check( context->canceller() );

			iY = ( oP.y + 0.5 ) / ratio.y + offset.y;
			OIIO::floorfrac( iY, &iYI );

			for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
			{
				float v = 0.0f;
				float totalW = 0.0f;
				std::vector<float>::const_iterator wIt = weights.begin() + ( oP.y - tileBound.min.y ) * ( filterRadius.y * 2 + 1);
				sampler.visitPixels( Imath::Box2i(
						Imath::V2i( oP.x, iYI - filterRadius.y ),
						Imath::V2i( oP.x + 1, iYI + filterRadius.y + 1 )
					),
					[&wIt, &v, &totalW]( float cur, int x, int y )
					{
						const float w = *wIt++;
						v += w * cur;
						totalW += w;
					}
				);

				if( totalW != 0.0f )
				{
					*pIt = v / totalW;
				}

				++pIt;
			}
		}
	}

	return resultData;
}
