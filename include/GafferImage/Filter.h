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

#include "IECore/RefCounted.h"
#include "IECore/InternedString.h"

#define _USE_MATH_DEFINES
#include "math.h"
	
namespace GafferImage
{

IE_CORE_FORWARDDECLARE( Filter );

/// Interpolation class for filtering an image.
///
/// The filter class represents a 1D convolution of radius().
/// For simplicity we only implement separable kernels.
/// We do the following to convolve a 2D image (I) by 1D kernel (g):
/// C(x,y) = g*I = (g2 *y (g1 *x I))(x,y)
/// Where *x and *y denotes convolution in the x and y directions.
///
/// A good overview of image sampling and the variety of filters is:
/// "Reconstruction Filters in Computer Graphics", by Don P.Mitchell,
/// Arun N.Netravali, AT&T Bell Laboratories.
class Filter : public IECore::RefCounted
{

public :
	
	/// Constructor	
	/// @param radius Half the width of the kernel at a scale of 1.
	/// @param scale Scales the size and weights of the kernel for values > 1. This is used when sampling an area of pixels. 
	Filter( double radius, double scale = 1. );
		
	virtual ~Filter(){};

	/// Resizes the kernel to a new scale.
	void setScale( double scale );

	/// Returns the current scale of the kernel.
	inline double getScale() const { return m_scale; }
	
	/// Accessors of the kernel weights.
	inline double operator[]( int idx ) const
	{
		return m_weights[idx];
	};

	/// Returns a reference to the list of weights.
	inline const std::vector<double> &weights() const
	{
		return m_weights;
	}

	/// Returns the width of the filter.
	inline int width() const
	{
		return m_weights.size();
	};

	/// Builds the kernel of weights.
	/// This method is should be called to initialize the filter.
	/// It does this by making sucessive calls to weight() to
	/// populate the vector of weights.
	/// @param center The position of the center of the filter kernel.
	/// @return Returns the index of the first pixel sample.
	int construct( double center );

	// Returns a weight for a delta in the range of -m_scaledRadius to m_scaledRadius.
	virtual double weight( double delta ) const = 0;

	//! @name Filter Registry
	/// A set of methods to query the available Filters and create them.
	//////////////////////////////////////////////////////////////
	//@{
	/// Instantiates a new Filter and initialises it to the desired scale.
	/// @param filterName The name of the filter within the registry.
	/// @param scale The scale to create the filter at.
	static FilterPtr create( const std::string &filterName, double scale = 1. );

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

	typedef FilterPtr (*CreatorFn)( double scale );

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
			/// Returns a new instance of the Filter class.
			static FilterPtr creator( double scale = 1. )
			{
				return new T( scale );
			}
	};

	const double m_radius;
	double m_scale;
	double m_scaledRadius;
	std::vector<double> m_weights;

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

};

IE_CORE_DECLAREPTR(Filter);

class BoxFilter : public Filter
{

public:

	BoxFilter( double scale = 1. )
		: Filter( .5, scale )
	{
	}
	
	double weight( double delta ) const
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

	BilinearFilter( double scale = 1. )
		: Filter( 1, scale )
	{}

	double weight( double delta ) const
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

	SincFilter( double scale = 1. )
		: Filter( 8, scale )
	{}

	double weight( double delta ) const
	{
		delta = fabs(delta);
		if ( delta < m_radius )
		{
			if ( delta )
			{
				return sinc(delta) * sinc( delta / m_radius );
			}
		}
		return 0;
	}

private:

	double sinc( double x ) const
	{
		if ( x != 0. )
		{
			x *= M_PI;
			return sin(x) / x;
		}
		return 1.;
	}

	/// Register this filter so that it can be created using the Filter::create method.
	static FilterRegistration<SincFilter> m_registration;

};

class HermiteFilter : public Filter
{

public:

	HermiteFilter( double scale = 1. )
		: Filter( 1, scale )
	{}

	double weight( double delta ) const
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

class SplineFilter : public Filter
{

public:

	SplineFilter( double B, double C, double scale = 1. )
		: Filter( 2, scale ),
		m_B( B ),
		m_C( C )
	{
	}

	double weight( double delta ) const
	{
		delta = fabs(delta);
		double delta2 = delta*delta;

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

	const double m_B;
	const double m_C;

};

class MitchellFilter : public SplineFilter
{

public:

	MitchellFilter( double scale = 1. )
		: SplineFilter( 1/3, 1/3, scale )
	{}

private:

	/// Register this filter so that it can be created using the Filter::create method.
	static FilterRegistration<MitchellFilter> m_registration;

};

class BSplineFilter : public SplineFilter
{

public:

	BSplineFilter( double scale = 1. )
		: SplineFilter( 1., 0., scale )
	{}

private:

	/// Register this filter so that it can be created using the Filter::create method.
	static FilterRegistration<BSplineFilter> m_registration;

};

class CatmullRomFilter : public SplineFilter
{

public:

	CatmullRomFilter( double scale = 1. )
		: SplineFilter( 0, .5, scale )
	{}

private:

	/// Register this filter so that it can be created using the Filter::create method.
	static FilterRegistration<CatmullRomFilter> m_registration;

};

class CubicFilter : public Filter
{

public:

	CubicFilter( double scale = 1. )
		: Filter( 3., scale )
	{
	}

	double weight( double delta ) const 
	{
		delta = fabs( delta );
		double delta2 = delta*delta;

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

