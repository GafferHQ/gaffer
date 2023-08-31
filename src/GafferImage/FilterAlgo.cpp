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


#include "GafferImage/FilterAlgo.h"

#include "IECore/Exception.h"

#include "OpenImageIO/filter.h"

#include "fmt/format.h"

#include <climits>


using namespace Imath;
using namespace GafferImage;
using namespace GafferImage::FilterAlgo;

namespace
{

// OIIO's built in gaussian filter is clipped quite aggressively, so there
// is a significant step to zero at the edge of the filter. This makes it
// unsuitable for use in a gaussian blur - as the filter radius expands to
// include another pixel, it switches on suddenly rather than fades up from
// black. This variant approaches very close to zero at the edge of its
// support, making it more suitable for use in a blur.
class SmoothGaussian2D : public OIIO::Filter2D
{

	public :

		SmoothGaussian2D( float width, float height )
			: Filter2D( width, height ), m_radiusInverse( 2.0f / width, 2.0f / height )
		{
		}

		~SmoothGaussian2D() override
		{
		}

		float operator()( float x, float y ) const override
		{
			return gauss1d( x * m_radiusInverse.x ) * gauss1d( y * m_radiusInverse.y );
		}

		bool separable() const override
		{
			return true;
		}

		float xfilt( float x ) const override
		{
			return gauss1d( x * m_radiusInverse.x );
		}

		float yfilt( float y ) const override
		{
			return gauss1d( y * m_radiusInverse.y );
		}

		OIIO::string_view name() const override
		{
			return "smoothGaussian";
		}

	private :

		static float gauss1d( float x )
		{
			x = fabsf( x );
			return ( x < 1.0f ) ? OIIO::fast_exp( -5.0f * ( x * x ) ) : 0.0f;
		}

		V2f m_radiusInverse;

};

// OIIO's default cubic is a general one with a protected m_a member that can be
// modified.  But when m_a is left at it's default value of 0, it is 0 over half
// of it's width.  By specializing for this case, we get a filter that needs
// half as many support pixels, but gives an identical result.

class FilterCubicSimple2D : public OIIO::Filter2D
{
	public:
		FilterCubicSimple2D( float width, float height )
			: Filter2D( width, height ),
			m_wrad_inv( 2.0f/width ), m_hrad_inv( 2.0f/height )
		{
		}

		~FilterCubicSimple2D( void ) override
		{
		}

		float operator()( float x, float y ) const override
		{
			return cubicSimple( x * m_wrad_inv ) * cubicSimple( y * m_hrad_inv );
		}

		bool separable() const override
		{
			return true;
		}

		float xfilt( float x ) const override
		{
			return cubicSimple( x * m_wrad_inv );
		}

		float yfilt( float y ) const override
		{
			return cubicSimple( y * m_hrad_inv );
		}

		OIIO::string_view name() const override
		{
			return "cubic";
		}
	protected:

		static float cubicSimple( float x )
		{
			x = fabsf (x);
			if (x > 1.0f)
			{
				return 0.0f;
			}

			return x*x*(2.0f * x - 3.0f) + 1.0f;
		}

		float m_wrad_inv, m_hrad_inv;
};


void ensureMinimumParallelogramWidth( V2f &dpdx, V2f &dpdy )
{

	float lx = dpdx.length();
	float ly = dpdy.length();

	if( lx == 0 && ly == 0 )
	{
		dpdx = V2f( 1.0f, 0.0f );
		dpdy = V2f( 0.0f, 1.0f );
		return;
	}

	// Computed normalized dpdx, and replace dpdx with this if it's too short
	V2f dpdxNorm( 0.0f );
	if( lx > 0 )
	{
		dpdxNorm = dpdx / lx;
		if( lx < 1 )
		{
			dpdx = dpdxNorm;
		}
	}

	// Computed normalized dpdy, and replace dpdy with this if it's too short
	V2f dpdyNorm( 0.0f );
	if( ly > 0 )
	{
		dpdyNorm = dpdy / ly;
		if( ly < 1 )
		{
			dpdy = dpdyNorm;
		}
	}

	// Compute signed distance of each vector from the other vector
	V2f dpdxPerpNorm( dpdxNorm.y, -dpdxNorm.x );
	V2f dpdyPerpNorm( dpdyNorm.y, -dpdyNorm.x );
	float dpdxPerpDist = dpdx.dot( dpdyPerpNorm );
	float dpdyPerpDist = dpdy.dot( dpdxPerpNorm );

	// Ensure that minimum width on all axes is >= 1 by checking against the perpendicular direction
	// and intcreasing the width if it's too low
	if( fabs( dpdxPerpDist ) < 1.0f )
	{
		dpdx += dpdyPerpNorm * ( 1.0f - fabs( dpdxPerpDist ) ) * ( dpdxPerpDist > 0 ? 1 : -1 );
	}
	if( fabs( dpdyPerpDist ) < 1.0f )
	{
		dpdy += dpdxPerpNorm * ( 1.0f - fabs( dpdyPerpDist ) ) * ( dpdyPerpDist >= 0 ? 1 : -1 );

		// NOTE: the use of >= here, and > above, is intentional.  It doesn't matter which way the derivative
		// points when we use it for filtering, but if both cases are exactly on the threshold, we want them to
		// pick opposite directions to enlarge in.
		// For example, if dpdx = dpdy = <1, 0>, our output should be <1,1> and <1,-1>.
		// If we output <1,1> and <1,1>, this would still be degenerate.
		// In non-degenerate cases, this makes no difference, because the perpDist values will be non-zero
		// and geometrically must point in different directions.
	}
}

using FilterPair = std::pair<std::string, const OIIO::Filter2D *>;

tbb::spin_rw_mutex g_filtersInitMutex;

std::vector<FilterPair> getAllFilters()
{
	std::vector< FilterPair > filters;
	for( int i = 0, e = OIIO::Filter2D::num_filters();  i < e;  ++i )
	{
		OIIO::FilterDesc fd;
		OIIO::Filter2D::get_filterdesc( i, &fd );

		float width = fd.width;
		if( strcmp( fd.name, "cubic" ) == 0 )
		{
			// Since we know we're not changing the a value from it's default of 0 on this cubic,
			// we can use a simplified version with a smaller support to get identical results
			// much faster
			filters.push_back( FilterPair( fd.name, new FilterCubicSimple2D( 2.0f, 2.0f ) ) );
		}
		else
		{
			filters.push_back( FilterPair( fd.name, OIIO::Filter2D::create( fd.name, width, width ) ) );
		}
	}
	filters.push_back( FilterPair("smoothGaussian", new SmoothGaussian2D( 3.0f, 3.0f ) ) );

	return filters;
}

}

const std::vector<std::string> &GafferImage::FilterAlgo::filterNames()
{
	static std::vector<std::string> names;

	{
		tbb::spin_rw_mutex::scoped_lock lock( g_filtersInitMutex, false );
		if( !names.size() )
		{
			if( lock.upgrade_to_writer() )
			{
				std::vector<FilterPair> filters = getAllFilters();
				for( unsigned int i = 0;  i < filters.size();  ++i )
				{
					names.push_back( filters[i].first );
				}
			}
		}
	}

	return names;
}

const OIIO::Filter2D *GafferImage::FilterAlgo::acquireFilter( const std::string &name )
{
	using FilterMapType = std::map<std::string, const OIIO::Filter2D *>;
	static FilterMapType filterMap;

	{
		tbb::spin_rw_mutex::scoped_lock lock( g_filtersInitMutex, false );
		if( !filterMap.size() )
		{
			if( lock.upgrade_to_writer() )
			{
				std::vector<FilterPair> filters = getAllFilters();
				for( unsigned int i = 0;  i < filters.size();  ++i )
				{
					filterMap[ filters[i].first ] = filters[i].second;
				}
			}
		}
	}

	FilterMapType::const_iterator i = filterMap.find( name );
	if( i != filterMap.end() )
	{
		return i->second;
	}
	else
	{
		throw IECore::Exception( fmt::format( "Unknown filter \"{}\"", name ) );
	}
}

float GafferImage::FilterAlgo::sampleParallelogram( Sampler &sampler, const V2f &p, const V2f &dpdx, const V2f &dpdy, const OIIO::Filter2D *filter )
{
	V2f dpdxCorrected = dpdx;
	V2f dpdyCorrected = dpdy;
	ensureMinimumParallelogramWidth( dpdxCorrected, dpdyCorrected );

	V2f hdpdx = 0.5f * dpdxCorrected * filter->width();
	V2f hdpdy = 0.5f * dpdyCorrected * filter->height();

	// Find bounds of the 4 corners of our filter spot
	Box2f cornerBounds;
	cornerBounds.extendBy( p + hdpdx + hdpdy );
	cornerBounds.extendBy( p - hdpdx + hdpdy );
	cornerBounds.extendBy( p + hdpdx - hdpdy );
	cornerBounds.extendBy( p - hdpdx - hdpdy );

	// Include any pixels where the corner max bound is above the pixel center, and
	// the corner min bound is below the pixel center
	Box2i pixelBounds(
		V2i( (int)ceilf( cornerBounds.min.x - 0.5 ), (int)ceilf( cornerBounds.min.y - 0.5 ) ),
		V2i( (int)floorf( cornerBounds.max.x - 0.5 ) + 1, (int)floorf( cornerBounds.max.y - 0.5 ) + 1 ) );

	// Invert the 2x2 Matrix formed by the derivative vectors so we can go
	// from source pixels into the filter's coordinate system
	float determinant = hdpdx[0] * hdpdy[1] - hdpdx[1] * hdpdy[0];
	V2f filterWidthMult( filter->width(), filter->height() );
	V2f xstep = 0.5f / determinant * V2f( hdpdy[1], -hdpdx[1] ) * filterWidthMult;
	V2f ystep = 0.5f / determinant * V2f( -hdpdy[0], hdpdx[0] ) * filterWidthMult;

	float totalW = 0.0f;
	float v = 0.0f;
	for( int y = pixelBounds.min.y; y < pixelBounds.max.y; y++ )
	{
		for( int x = pixelBounds.min.x; x < pixelBounds.max.x; x++ )
		{
			V2f offset = V2f( x + 0.5f, y + 0.5f ) - p;
			V2f filterPos = offset[0] * xstep + offset[1] * ystep;

			float w = (*filter)( filterPos.x, filterPos.y );

			// \todo : I can't think of any way to keep this around cleanly for testing, since
			// it's right down in this inner loop, but replacing the filter with one value for
			// pixels within the bounding box, and another value for pixels actually touched
			// by the filter, is a good way to check that the bounding box is correct
			//w = w != 0.0f ? 1.0f : 0.1f;

			if( w != 0.0f )
			{
				totalW += w;
				v += w * sampler.sample( x, y );
			}
		}
	}

	if( totalW != 0.0f )
	{
		v /= totalW;
	}

	return v;
}

float GafferImage::FilterAlgo::sampleBox( Sampler &sampler, const V2f &p, float dx, float dy, const OIIO::Filter2D *filter, std::vector<float> &scratchMemory )
{
	float xscale = 1.0f / dx;
	float yscale = 1.0f / dy;

	Box2f bounds = filterSupport( p, dx, dy, filter->width() );

	// Include any pixels where the corner max bound is above the pixel center, and
	// the corner min bound is below the pixel center
	Box2i pixelBounds(
		V2i( (int)ceilf( bounds.min.x - 0.5 ), (int)ceilf( bounds.min.y - 0.5 ) ),
		V2i( (int)floorf( bounds.max.x - 0.5 ) + 1, (int)floorf( bounds.max.y - 0.5 ) + 1 ) );

	float totalW = 0.0f;
	float v = 0.0f;
	if( filter->separable() )
	{
		int xWidth = pixelBounds.max.x - pixelBounds.min.x;

		// \todo - this is an alloca call that risks blowing the stack in an edge case on overly wide image
		// Find a more reliable alternative, hopefully without sacrificing perf
		//float xFilterWeights[ xWidth ];
		//std::vector<float> xFilterWeights( pixelBounds.max.x - pixelBounds.min.x );
		//std::vector<float> xFilterWeights( xWidth );
		scratchMemory.resize( xWidth );
		for( int i = 0; i < xWidth; i++ )
		{
			// Use the scratch memory passed in to hold a row of filter weights
			scratchMemory[i] = filter->xfilt( ( (pixelBounds.min.x + i) + 0.5f - p.x ) * xscale );
		}

		Imath::Box2i visitBounds = pixelBounds;
		for( int y = pixelBounds.min.y; y < pixelBounds.max.y; y++ )
		{
			visitBounds.min.y = y;
			visitBounds.max.y = y + 1;
			float yFilterWeight = filter->yfilt( ( y + 0.5f - p.y ) * yscale );
			sampler.visitPixels(
				visitBounds,
				[ &totalW, &v, &pixelBounds, &scratchMemory, &yFilterWeight ] ( float value, int x, int y )
				{
					float w = scratchMemory[ x - pixelBounds.min.x ] * yFilterWeight;

					// \todo : I can't think of any way to keep this around cleanly for testing, since
					// it's right down in this inner loop, but replacing the filter with one value for
					// pixels within the bounding box, and another value for pixels actually touched
					// by the filter, is a good way to check that the bounding box is correct
					//w = w != 0.0f ? 1.0f : 0.1f;

					totalW += w;
					v += w * value;
				}
			);
		}
	}
	else
	{
		sampler.visitPixels( pixelBounds,
			[ &totalW, &v, &p, &xscale, &yscale, &filter ] ( float value, int x, int y )
			{
				float w = (*filter)( ( x + 0.5f - p.x ) * xscale, ( y + 0.5f - p.y ) * yscale );
				totalW += w;
				v += w * value;
			}
		);
	}

	if( totalW != 0.0f )
	{
		v /= totalW;
	}

	return v;
}
