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

const std::string g_nearestString( "nearest" );

// Used as a bitmask to say which filter pass(es) we're computing.
enum Passes
{
	Horizontal = 1,
	Vertical = 2,
	Both = Horizontal | Vertical,

	// Special pass label when we must compute both passes in one, but there is no scaling.
	// This allows a special code path which is up to 6X faster.
	BothOptimized = Both | 4
};

Passes requiredPasses( const Resample *resample, const ImagePlug *image, const OIIO::Filter2D *filter, V2f &ratio )
{
	int debug = resample->debugPlug()->getValue();
	if( debug == Resample::HorizontalPass )
	{
		return Horizontal;
	}
	else if( debug == Resample::SinglePass )
	{
		// For a SinglePass debug mode, we always use Both.
		// Note that we don't use the optimized pass here, even if the ratio is 1 - we want debug to always
		// use the same path.
		return (Passes)( Horizontal | Vertical );
	}

	if( image == image->parent<ImageNode>()->outPlug() )
	{
		if( !filter )
		{
			// For the nearest filter, we use a separate code path that doesn't consider RequiredPasses anyway.
			return Both;
		}
		if( filter->separable() )
		{
			return Vertical;
		}
		else
		{
			// The filter isn't separable, so we must process everything at once. If the ratio has no
			// scaling though, we can use the optimized path.
			return ( ratio == V2f( 1.0 ) ) ? BothOptimized : Both;
		}
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
V2f inputFilterRadius( const OIIO::Filter2D *filter, const V2f &inputFilterScale )
{
	if( !filter )
	{
		return V2f( 0.0f );
	}

	return V2f(
		filter->width() * inputFilterScale.x * 0.5f,
		filter->height() * inputFilterScale.y * 0.5f
	);
}

// Returns the input region that will need to be sampled when
// generating a given output tile.
Box2i inputRegion( const V2i &tileOrigin, unsigned passes, const V2f &ratio, const V2f &offset, const OIIO::Filter2D *filter, const V2f &inputFilterScale )
{
	Box2f outputRegion( V2f( tileOrigin ), tileOrigin + V2f( ImagePlug::tileSize() ) );
	V2f filterRadius = inputFilterRadius( filter, inputFilterScale );
	V2i filterRadiusCeil( ceilf( filterRadius.x ), ceilf( filterRadius.y ) );

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
		result.min.x -= filterRadiusCeil.x;
		result.max.x += filterRadiusCeil.x;
	}
	if( passes & Vertical )
	{
		result.min.y = result.min.y / ratio.y + offset.y;
		result.max.y = result.max.y / ratio.y + offset.y;
		if( result.min.y > result.max.y )
		{
			std::swap( result.min.y, result.max.y );
		}
		result.min.y -= filterRadiusCeil.y;
		result.max.y += filterRadiusCeil.y;
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
	else if( name == g_nearestString )
	{
		inputFilterScale = V2f( 0 );
		return nullptr;
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
void filterWeights1D( const OIIO::Filter2D *filter, const float inputFilterScale, const float filterRadius, const int x, const float ratio, const float offset, Passes pass, std::vector<int> &supportRanges, std::vector<float> &weights )
{
	weights.reserve( ( 2 * ceilf( filterRadius ) + 1 ) * ImagePlug::tileSize() );
	supportRanges.reserve( 2 * ImagePlug::tileSize() );

	const float filterCoordinateMult = 1.0f / inputFilterScale;

	for( int oX = x, eX = x + ImagePlug::tileSize(); oX < eX; ++oX )
	{
		// input pixel position (floating point)
		float iX = ( oX + 0.5 ) / ratio + offset;

		int minX = ceilf( iX - 0.5f - filterRadius );
		int maxX = floorf( iX + 0.5f + filterRadius );

		supportRanges.push_back( minX );
		supportRanges.push_back( maxX );

		for( int fX = minX; fX < maxX; ++fX )
		{
			const float f = filterCoordinateMult * ( float( fX ) + 0.5f - iX );
			// \todo - supportRanges should only include values != 0. Address at same time as
			// moving normalization in here.
			const float w = pass == Horizontal ? filter->xfilt( f ) : filter->yfilt( f );
			weights.push_back( w );
		}
	}
}

// For the inseparable case, we can't always reuse the weights for an adjacent row or column.
// There are a lot of possible scaling factors where the ratio can be represented as a fraction,
// and the weights needed would repeat after a certain number of pixels, and we could compute weights
// for a limited section of pixels, and reuse them in a tiling way.
// That's a bit complicated though, so we're just handling the simplest case currently ( since it is
// a common case ):
// if there is no scaling, then we only need to compute the weights for one pixel, and we can reuse them
// for all pixels. This means we don't loop over output pixels at all here - we just compute the weights
// for one output pixel, and return one 2D support for this pixel - it just gets shifted for each adjacent
// pixel.
void filterWeights2D( const OIIO::Filter2D *filter, const V2f inputFilterScale, const V2f filterRadius, const V2i p,  const V2f offset, Box2i &support, std::vector<float> &weights )
{
	weights.reserve( ( 2 * ceilf( filterRadius.x ) + 1 ) * ( 2 * ceilf( filterRadius.y ) + 1 )  );

	const V2f filterCoordinateMult( 1.0f / inputFilterScale.x, 1.0f / inputFilterScale.y );

	// input pixel position (floating point)
	V2f i = V2f( p ) + V2f( 0.5 ) + offset;

	support = Box2i(
		V2i( ceilf( i.x - 0.5f - filterRadius.x ), ceilf( i.y - 0.5f - filterRadius.y ) ),
		V2i( floorf( i.x + 0.5f + filterRadius.x ), floorf( i.y + 0.5f + filterRadius.y ) )
	);

	for( int fY = support.min.y; fY < support.max.y; ++fY )
	{
		const float fy = filterCoordinateMult.y * ( float( fY ) + 0.5 - i.y );
		for( int fX = support.min.x; fX < support.max.x; ++fX )
		{
			const float fx = filterCoordinateMult.x * ( float( fX ) + 0.5f - i.x );
			const float w = (*filter)( fx, fy );
			weights.push_back( w );
		}
	}
}

// Find the x index of the nearest input pixel for each pixel in this row. Used to implement the fast
// path for the "nearest" filter.
void nearestInputPixelX( const int x, const float ratio, const float offset, std::vector<int> &result )
{
	result.reserve( ImagePlug::tileSize() );

	for( int oX = x, eX = x + ImagePlug::tileSize(); oX < eX; ++oX )
	{
		result.push_back( floorf( ( oX + 0.5f ) / ratio + offset ) );
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
	: FlatImageProcessor( name )
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

		const V2f filterRadius = filter ? V2f( filter->width(), filter->height() ) * inputFilterScale * 0.5f : V2f( 0.0f );

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

	if( parent == horizontalPassPlug() || debugPlug()->getValue() == HorizontalPass )
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

	V2f inputFilterScale;
	const OIIO::Filter2D *filter;

	Sampler::BoundingMode boundingMode;
	{
		ImagePlug::GlobalScope c( context );
		ratioAndOffset( matrixPlug()->getValue(), ratio, offset );

		const std::string filterName = filterPlug()->getValue();
		const V2f filterScale = filterScalePlug()->getValue();

		filter = filterAndScale( filterName, ratio, inputFilterScale );
		inputFilterScale *= filterScale;

		boundingMode = (Sampler::BoundingMode)boundingModePlug()->getValue();
	}

	filterPlug()->hash( h );

	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	Passes passes = requiredPasses( this, parent, filter, ratio );
	Box2i ir = inputRegion( tileOrigin, passes, ratio, offset, filter, inputFilterScale );

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

	if( passes == BothOptimized )
	{
		// Append an extra flag so our hash reflects that we are going to take the optimized path
		h.append( true );
	}

	Sampler sampler(
		passes == Vertical ? horizontalPassPlug() : inPlug(),
		channelName,
		ir,
		boundingMode
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
	V2f inputFilterScale;
	const OIIO::Filter2D *filter;
	Sampler::BoundingMode boundingMode;
	{
		ImagePlug::GlobalScope c( context );
		ratioAndOffset( matrixPlug()->getValue(), ratio, offset );

		const std::string filterName = filterPlug()->getValue();
		const V2f filterScale = filterScalePlug()->getValue();

		filter = filterAndScale( filterName, ratio, inputFilterScale );
		inputFilterScale *= filterScale;

		boundingMode = (Sampler::BoundingMode)boundingModePlug()->getValue();
	}

	Passes passes = requiredPasses( this, parent, filter, ratio );
	Box2i ir = inputRegion( tileOrigin, passes, ratio, offset, filter, inputFilterScale );

	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	Sampler sampler(
		passes == Vertical ? horizontalPassPlug() : inPlug(),
		channelName,
		ir,
		boundingMode
	);

	const V2f filterRadius = inputFilterRadius( filter, inputFilterScale );

	FloatVectorDataPtr resultData = new FloatVectorData;
	std::vector<float> &result = resultData->writable();
	result.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );
	std::vector<float>::iterator pIt = result.begin();

	if( !filter )
	{
		std::vector<int> iPx;
		nearestInputPixelX( tileBound.min.x, ratio.x, offset.x, iPx );

		V2i oP; // output pixel position
		int iPy; // input pixel position Y

		for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
		{
			iPy = floorf( ( oP.y + 0.5f ) / ratio.y + offset.y );
			std::vector<int>::const_iterator iPxIt = iPx.begin();

			Canceller::check( context->canceller() );
			for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
			{
				*pIt = sampler.sample( *iPxIt, iPy );
				++iPxIt;
				++pIt;
			}
		}
	}
	else if( passes == Both )
	{
		// When the filter isn't separable we must perform all the
		// filtering in a single pass. This version also provides
		// a reference implementation against which the two-pass
		// version can be validated - use the SinglePass debug mode
		// to force the use of this code path.

		V2i oP; // output pixel position
		V2f iP; // input pixel position (floating point)

		V2f	filterCoordinateMult = V2f(1.0f) / inputFilterScale;

		for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
		{
			iP.y = ( oP.y + 0.5 ) / ratio.y + offset.y;
			int minY = ceilf( iP.y - 0.5f - filterRadius.y );
			int maxY = floorf( iP.y + 0.5f + filterRadius.y );

			for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
			{
				Canceller::check( context->canceller() );

				iP.x = ( oP.x + 0.5 ) / ratio.x + offset.x;

				int minX = ceilf( iP.x - 0.5f - filterRadius.x );
				int maxX = floorf( iP.x + 0.5f + filterRadius.x );

				float v = 0.0f;
				float totalW = 0.0f;
				sampler.visitPixels(
					Imath::Box2i( Imath::V2i( minX, minY ), Imath::V2i( maxX, maxY ) ),
					[&filter, &filterCoordinateMult, &iP, &v, &totalW]( float cur, int x, int y )
					{
						const float w = (*filter)(
							filterCoordinateMult.x * ( float(x) + 0.5f - iP.x ),
							filterCoordinateMult.y * ( float(y) + 0.5f - iP.y )
						);

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
	else if( passes == BothOptimized )
	{
		Box2i support;
		std::vector<float> weights;
		filterWeights2D( filter, inputFilterScale, filterRadius, tileBound.min, offset, support, weights );

		V2i oP; // output pixel position
		V2i supportOffset;
		for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
		{
			supportOffset.y = oP.y - tileBound.min.y;

			for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
			{
				Canceller::check( context->canceller() );

				supportOffset.x = oP.x - tileBound.min.x;
				std::vector<float>::const_iterator wIt = weights.begin();

				float v = 0.0f;
				float totalW = 0.0f;
				sampler.visitPixels(
					Imath::Box2i( support.min + supportOffset, support.max + supportOffset ),
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
	else if( passes == Horizontal )
	{
		// When the filter is separable we can perform filtering in two
		// passes, one for the horizontal and one for the vertical. We
		// output the horizontal pass on the horizontalPassPlug() so that
		// it is cached for use in the vertical pass. The HorizontalPass
		// debug mode causes this pass to be output directly for inspection.

		// Pixels in the same column share the same support ranges and filter weights, so
		// we precompute the weights now to avoid repeating work later.
		std::vector<int> supportRanges;
		std::vector<float> weights;
		filterWeights1D( filter, inputFilterScale.x, filterRadius.x, tileBound.min.x, ratio.x, offset.x, Horizontal, supportRanges, weights );

		V2i oP; // output pixel position

		for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
		{
			Canceller::check( context->canceller() );

			std::vector<int>::const_iterator supportIt = supportRanges.begin();
			std::vector<float>::const_iterator wIt = weights.begin();
			for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
			{
				float v = 0.0f;
				float totalW = 0.0f;

				sampler.visitPixels( Imath::Box2i(
						Imath::V2i( *supportIt, oP.y ),
						Imath::V2i( *( supportIt + 1 ), oP.y + 1 )
					),
					[&wIt, &v, &totalW]( float cur, int x, int y )
					{
						const float w = *wIt++;
						v += w * cur;
						totalW += w;
					}
				);

				supportIt += 2;

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

		// Pixels in the same row share the same support ranges and filter weights, so
		// we precompute the weights now to avoid repeating work later.
		std::vector<int> supportRanges;
		std::vector<float> weights;
		filterWeights1D( filter, inputFilterScale.y, filterRadius.y, tileBound.min.y, ratio.y, offset.y, Vertical, supportRanges, weights );

		std::vector<int>::const_iterator supportIt = supportRanges.begin();
		std::vector<float>::const_iterator rowWeightsIt = weights.begin();

		for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
		{
			Canceller::check( context->canceller() );

			for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
			{
				float v = 0.0f;
				float totalW = 0.0f;

				std::vector<float>::const_iterator wIt = rowWeightsIt;

				sampler.visitPixels( Imath::Box2i(
						Imath::V2i( oP.x, *supportIt ),
						Imath::V2i( oP.x + 1, *(supportIt + 1) )
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

			rowWeightsIt += (*(supportIt + 1)) - (*supportIt);
			supportIt += 2;
		}
	}

	return resultData;
}
