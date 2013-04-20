//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Luke Goddard. All rights reserved.
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

#ifndef GAFFERIMAGE_FITLER_H
#define GAFFERIMAGE_FILTER_H

namespace GafferImage
{

/// Interpolation class for filtering an image.
///
/// The filter class represents a 1D convolution of width().
/// For simplicity we only implement separable kerenels.
/// We do the following to convolve a 2D image (I) by 1D kernel (g):
/// C(x,y) = g*I = (g2 *y (g1 *x I))(x,y)
/// Where *x and *y denotes convolution in the x and y directions.
class Filter
{

public :

	Filter( int width, float scale = 1. )
		: m_scale( scale )
	{
		m_width = int( round( double( width ) * scale ) );
		
		if ( ( width % 2 == 0 ) != ( m_width % 2 == 0 ) )
		{
			m_width += 1;
		}

		m_weights.resize( m_width );
	}
	
	virtual ~Filter(){};

	/// Accessors of the kernel weights.
	float operator[]( int idx ) const
	{
		return m_weights[idx];
	};

	const float *weights() const
	{
		return &m_weights[0];
	}

	/// Returns the width of the filter.
	inline int width() const
	{
		return m_width;
	};

	/// Builds the kernel of weights.
	/// This method is called to initialize the filter. It should resize the 
	/// m_weights vector, calculate and populate it with the weights.
	/// @param x A shift of the interpolation function in the range of -1 to 1.
	/// @return Returns the index of the first pixel sample.
	virtual int construct( float x ) = 0;

protected :

	int m_width;
	float m_scale;
	std::vector<float> m_weights;
};

class SineFilter : public Filter
{

public :

	SineFilter( float scale = 1. )
		: Filter( 9, scale )
	{
	};

	int construct( float x )
	{
		x -= .5f;
		
		float absX = floorf( x );
		float delta = x - absX;
		float sum = .0f;
		const int radius = ( m_width-1 )/2;
		float *w = &m_weights[0];
		
		for ( int i = -radius; i <= radius; ++i )
		{
			float c = (3.14159265359f / m_scale) * float(i) - delta;
			if ( c != 0.0 )
			{
				c = sin(c) / c;
			}
			else
			{
				c = 1.0;
			}

			sum += *w++ = c;
		}

		// Normalize the weights.
		for (int i = 0; i < m_width; ++i)
		{
			m_weights[i] /= sum;
		}

		return static_cast<int>( absX - radius );
	}

};

class ImpulseFilter : public Filter
{

public :

	ImpulseFilter( float scale = 1.f )
		: Filter( 1, 1. )
	{
		m_weights[0] = 1.;
	}

	int construct( float x )
	{
		float absX = floorf( x-.5 );
		return static_cast<int>( absX );
	}

};

class BilinearFilter : public Filter
{

public :

	BilinearFilter( float scale = 1.f )
		: Filter( 3, scale )
	{
	}
	
	int construct( float x )
	{
		x -= .5;
		float absX = floorf( x );
		float delta = 1.-(x-absX);
	
		// The width of this kernel should always be odd.
		assert( m_width % 2 != 0 );
		
		float *w = &m_weights[0];
		int hw = ( m_width - 1 ) / 2;
		float sum = 0.;
		for ( int i = -hw; i <= hw; ++i )
		{
			sum += *w++ = std::max( 0.f, 1.f-float( fabs(float(i) + delta + .5) / m_scale ) );
		}
		
		w = &m_weights[0];
		float *END = w+m_width;
		while( w != END )
		{
			*w++ /= sum;
		}

		return static_cast<int>( absX-hw+1 );
	}
};

}; // namespace GafferImage

#endif

