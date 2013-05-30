//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2013, Luke Goddard. All rights reserved.
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
//      * Neither the name Image Engine Design nor the names of
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

#ifndef GAFFERIMAGE_FILTER_H
#define GAFFERIMAGE_FILTER_H

#include <vector>
#include <string>

#include "tbb/mutex.h"
#include "boost/weak_ptr.hpp"

#include "GafferImage/TypeIds.h"

#include "IECore/RunTimeTyped.h"
#include "IECore/InternedString.h"
#include "IECore/Lookup.h"

#define _USE_MATH_DEFINES
#include "math.h"
	
namespace GafferImage
{

IE_CORE_FORWARDDECLARE( Filter );

/// Interpolation class for filtering an image.
///
/// The filter class represents a 1D separable kernel which 
/// provides methods for convolution with a set of pixel samples.
/// We can convolve a 2D image (I) by 1D kernel (g) by:
/// C(x,y) = g*I = (g2 *y (g1 *x I))(x,y)
/// Where *x and *y denotes convolution in the x and y directions.
/// 
/// A good overview of image sampling and the variety of filters is:
/// "Reconstruction Filters in Computer Graphics", by Don P.Mitchell,
/// Arun N.Netravali, AT&T Bell Laboratories.
class Filter : public IECore::RunTimeTyped
{

public :
	
	IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Filter, FilterTypeId, RunTimeTyped );
	
	/// Constructor	
	/// @param radius Half the width of the kernel at a scale of 1.
	/// @param scale Scales the size and weights of the kernel for values > 1. This is used when sampling an area of pixels. 
	Filter( float radius, float scale = 1. );
		
	virtual ~Filter(){};

	//! @name Accessors
	/// A set of methods to access the members of the filter.
	//////////////////////////////////////////////////////////////
	//@{
	/// Resizes the kernel to a new scale.
	void setScale( float scale );
	/// Returns the current scale of the kernel.
	inline float getScale() const { return m_scale; }
	//@}
	//! @name Filter Convolution
	/// A set of methods that create a simple interface to allow the
	/// filter to be convolved with a discreet array (such as a set of pixels).
	//////////////////////////////////////////////////////////////
	//@{
	/// Returns the width of the filter in pixels.
	inline int width() const
	{
		return int( m_scaledRadius*2. + 1. );
	};
	/// Returns the weight of a pixel to be convolved with the filter
	/// given the center of the filter and the position of the pixel to be sampled.  
	/// @param center The center of the kernel.
	/// @param samplePosition The position of the sample to return the weight for.
	//  @return The weight of the sample.
	inline float weight( float center, int samplePosition ) const
	{
		float t = ( center - samplePosition - .5 ) / m_scale;
		return (*m_lut)( fabs( t ) );
	}
	/// Returns the position of the first sample influenced by the kernel.
	/// Use this function to get the index of the first pixel to convolve
	/// the filter with.
	/// "Center" must be positive.
	inline int tap( float center ) const
	{
		return int( center - m_scaledRadius );
	}
	//@}

	//! @name Filter Registry
	/// A set of methods to query the available Filters and create them.
	//////////////////////////////////////////////////////////////
	//@{
	/// Instantiates a new Filter and initialises it to the desired scale.
	/// @param filterName The name of the filter within the registry.
	/// @param scale The scale to create the filter at.
	static FilterPtr create( const std::string &filterName, float scale = 1. );

	/// Returns a vector of the available filters.
	static const std::vector<std::string> &filters()
	{
		return filterList();
	}
	//@}
	
	/// Returns the default filter.
	static const IECore::InternedString &defaultFilter()
	{
		static const IECore::InternedString g_defaultFilter( "Bilinear" );
		return g_defaultFilter;
	}

protected :

	// Returns a weight for a delta in the range of 0 to m_radius.
	virtual float weight( float delta ) const = 0;

	typedef FilterPtr (*CreatorFn)( float scale );

	template<class T>
	struct FilterRegistration
	{
		public:
			/// Registers the Filter
			FilterRegistration<T>( std::string name )
			{
				Filter::filterList().push_back( name );
				Filter::creators().push_back( creator );
			}

		private:

			static float calculateLutWeight( float value )
			{
				T filter;
				if (value >= filter.m_radius ) return 0;
				return filter.weight( value );
			}

			/// Returns a new instance of the Filter class and initializes it's LUT if it does not exist or just grabs a shared_ptr to one if it does.
			static FilterPtr creator( float scale = 1. )
			{
				T* filter = new T( scale );
				const std::string &filterName( filter->typeName() );
				
				tbb::mutex::scoped_lock lock;
				lock.acquire( lutMutex() );
				std::map< std::string, boost::weak_ptr<IECore::Lookupff> > &lutMap( Filter::lutMap() );
				boost::shared_ptr<IECore::Lookupff> lutPtr( lutMap[filterName].lock() );
				if ( !lutPtr )
				{
					lutPtr.reset( new IECore::Lookupff( calculateLutWeight, 0.f, filter->m_radius, 256 ) );
					lutMap[filterName] = lutPtr;
				}
				lock.release();

				filter->m_lut = lutPtr;
				return FilterPtr( filter );
			}

			static tbb::mutex& lutMutex()
			{
				static tbb::mutex g_mutex;
				return g_mutex;
			}
	};

	const float m_radius;
	float m_scale;
	float m_scaledRadius;

private:

	/// Registration mechanism for Filter classes.
	/// We keep a vector of the names so that we can maintain an order. 
	static std::vector< CreatorFn >& creators()
	{
		static std::vector< CreatorFn > g_creators;
		return g_creators;
	}
	
	static std::vector< std::string >& filterList()
	{
		static std::vector< std::string > g_filters;
		return g_filters;
	}
	
	static std::map< std::string, boost::weak_ptr<IECore::Lookupff> > &lutMap()
	{
		static std::map< std::string, boost::weak_ptr<IECore::Lookupff> > l;
		return l;
	}
	
	boost::shared_ptr<IECore::Lookupff> m_lut;

};

IE_CORE_DECLAREPTR(Filter);

class BoxFilter : public Filter
{

public:
	
	IE_CORE_DECLARERUNTIMETYPEDEXTENSION( BoxFilter, BoxFilterTypeId, Filter );

	BoxFilter( float scale = 1. )
		: Filter( .5, scale )
	{
	}
	
	float weight( float delta ) const
	{
		delta = fabs(delta);
		return ( delta <= 0.5 );
	}

private:

	/// Register this filter so that it can be created using the Filter::create method.
	static FilterRegistration<BoxFilter> m_registration;

};

class BilinearFilter : public Filter
{

public:

	IE_CORE_DECLARERUNTIMETYPEDEXTENSION( BilinearFilter, BilinearFilterTypeId, Filter );
	
	BilinearFilter( float scale = 1. )
		: Filter( 1, scale )
	{}

	float weight( float delta ) const
	{
		delta = fabs(delta);
		if ( delta < 1. )
		{
			return 1. - delta;
		}
		return 0.;
	}

private:

	/// Register this filter so that it can be created using the Filter::create method.
	static FilterRegistration<BilinearFilter> m_registration;

};

class SincFilter : public Filter
{

public:
	
	IE_CORE_DECLARERUNTIMETYPEDEXTENSION( SincFilter, SincFilterTypeId, Filter );

	SincFilter( float scale = 1. )
		: Filter( 2., scale )
	{}

	float weight( float delta ) const
	{
		delta = fabs(delta);
		if ( delta > m_radius )
		{
			return 0.;
		}
		if ( delta < 10e-6 )
		{
			return 1.;
		}

		const float PI = M_PI;
		return sin( PI*delta ) / ( PI*delta );
	}

private:

	/// Register this filter so that it can be created using the Filter::create method.
	static FilterRegistration<SincFilter> m_registration;

};

class HermiteFilter : public Filter
{

public:
	
	IE_CORE_DECLARERUNTIMETYPEDEXTENSION( HermiteFilter, HermiteFilterTypeId, Filter );

	HermiteFilter( float scale = 1. )
		: Filter( 1, scale )
	{}

	float weight( float delta ) const
	{
		delta = fabs(delta);
		if ( delta < 1 )
		{
			return ( ( 2. * delta - 3. ) * delta * delta + 1. );
		}
		return 0.;
	}

private:

	/// Register this filter so that it can be created using the Filter::create method.
	static FilterRegistration<HermiteFilter> m_registration;

};

class LanczosFilter : public Filter
{

public:
	
	IE_CORE_DECLARERUNTIMETYPEDEXTENSION( LanczosFilter, LanczosFilterTypeId, Filter );

	LanczosFilter( float scale = 1. )
		: Filter( 3., scale )
	{}

	float weight( float delta ) const
	{
		delta = fabs(delta);
		
		if ( delta > m_radius )
		{
			return 0.;
		}
		if ( delta < 10e-6 )
		{
			return 1.;
		}
		
		const float PI = M_PI;
		return ( m_radius * (1./PI) * (1./PI) ) / ( delta*delta) * sin( PI * delta ) * sin( PI*delta * (1./m_radius) );
	}

private:

	/// Register this filter so that it can be created using the Filter::create method.
	static FilterRegistration<LanczosFilter> m_registration;

};

class SplineFilter : public Filter
{

public:

	IE_CORE_DECLARERUNTIMETYPEDEXTENSION( SplineFilter, SplineFilterTypeId, Filter );
	
	SplineFilter( float B, float C, float scale = 1. )
		: Filter( 2, scale ),
		m_B( B ),
		m_C( C )
	{
	}

	float weight( float delta ) const
	{
		delta = fabs(delta);
		float delta2 = delta*delta;

		if ( delta < 1. )
		{
			delta = (((12. - 9.*m_B - 6.*m_C)*(delta*delta2)) + ((- 18. + 12.*m_B + 6.*m_C)*delta2) + (6. - 2.*m_B));
			return delta / 6.;
		}

		if ( delta < 2. )
		{
			delta = (((- m_B - 6.*m_C)*(delta*delta2)) + ((6.*m_B + 30.*m_C)*delta2) + ((- 12.*m_B - 48.*m_C)*delta) + (8.*m_B + 24.*m_C));
			return delta / 6.;
		}

		return 0.;
	}

private:

	const float m_B;
	const float m_C;

};

class MitchellFilter : public SplineFilter
{

public:
	
	IE_CORE_DECLARERUNTIMETYPEDEXTENSION( MitchellFilter, MitchellFilterTypeId, SplineFilter );

	MitchellFilter( float scale = 1. )
		: SplineFilter( 1./3., 1./3., scale )
	{}

private:

	/// Register this filter so that it can be created using the Filter::create method.
	static FilterRegistration<MitchellFilter> m_registration;

};

class BSplineFilter : public SplineFilter
{

public:
	
	IE_CORE_DECLARERUNTIMETYPEDEXTENSION( BSplineFilter, BSplineFilterTypeId, SplineFilter );

	BSplineFilter( float scale = 1. )
		: SplineFilter( 1., 0., scale )
	{}

private:

	/// Register this filter so that it can be created using the Filter::create method.
	static FilterRegistration<BSplineFilter> m_registration;

};

class CatmullRomFilter : public SplineFilter
{

public:

	IE_CORE_DECLARERUNTIMETYPEDEXTENSION( CatmullRomFilter, CatmullRomFilterTypeId, SplineFilter );
	
	CatmullRomFilter( float scale = 1. )
		: SplineFilter( 0., .5, scale )
	{}

private:

	/// Register this filter so that it can be created using the Filter::create method.
	static FilterRegistration<CatmullRomFilter> m_registration;

};

class CubicFilter : public Filter
{

public:

	IE_CORE_DECLARERUNTIMETYPEDEXTENSION( CubicFilter, CubicFilterTypeId, Filter );
	
	CubicFilter( float scale = 1. )
		: Filter( 3., scale )
	{
	}

	float weight( float delta ) const 
	{
		delta = fabs( delta );
		float delta2 = delta*delta;

		if ( delta <= 1. )
		{
			return ((4./3.)*delta2*delta - (7./3.)*delta2 + 1.);
		}

		if ( delta <= 2. )
		{
			return (- (7./12.)*delta2*delta + 3*delta2 - (59./12.)*delta + 2.5);
		}

		if ( delta <= 3. )
		{
			return ((1./12.)*delta2*delta - (2./3.)*delta2 + 1.75f*delta - 1.5);
		}

		return 0;
	}

private:

	/// Register this filter so that it can be created using the Filter::create method.
	static FilterRegistration<CubicFilter> m_registration;

};

}; // namespace GafferImage

#endif

