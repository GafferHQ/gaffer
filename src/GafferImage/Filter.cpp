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

#include <vector>
#include <string>
#include <map>

#include "boost/format.hpp"
#include "IECore/Exception.h"
#include "GafferImage/Filter.h"

namespace GafferImage
{

Filter::Filter( double radius, double scale )
	: m_radius( radius )
{
	setScale( scale );
}

void Filter::setScale( double scale )
{
	if ( scale > 1. )
	{
		m_scaledRadius = m_radius * scale;
		m_scale = scale;
	}
	else
	{
		m_scaledRadius = m_radius;
		m_scale = 1.;
	}
	m_weights.resize( int( floor( m_scaledRadius*2+1 ) ) );
}

int Filter::construct( double center )
{
	int l, absx;
	l = absx = (int)( center - m_scaledRadius );
	std::vector<double>::iterator it( m_weights.begin() );
	std::vector<double>::iterator end( m_weights.end() );
	while ( it != end )
	{
		*it++ = weight( ( center - l++ - 0.5 ) / m_scale );
	}
	return absx;
}

FilterPtr Filter::create( const std::string &name, double scale )
{
	// Check to see whether the requested Filter is registered and if not, throw an exception.
	std::vector<std::string>::iterator it( filterList().begin() );
	std::vector<std::string>::iterator end( filterList().end() );
	
	while( it != end )
	{
		if ( *it == name )
		{
			// Return a new instance of the Filter
			return (creators()[it - filterList().begin()])( scale );
		}

		it++;
	}

	throw IECore::Exception( (boost::format("Could not find registered filter \"%s\".") % name).str() );
	
	return 0; // We should never get here.
}

// Register all of the filters against their names.
Filter::FilterRegistration<BilinearFilter> BilinearFilter::m_registration( "Bilinear" );
Filter::FilterRegistration<BoxFilter> BoxFilter::m_registration( "Box" );
Filter::FilterRegistration<BSplineFilter> BSplineFilter::m_registration( "BSpline" );
Filter::FilterRegistration<CatmullRomFilter> CatmullRomFilter::m_registration( "CatmullRom" );
Filter::FilterRegistration<CubicFilter> CubicFilter::m_registration( "Cubic" );
Filter::FilterRegistration<HermiteFilter> HermiteFilter::m_registration( "Hermite" );
Filter::FilterRegistration<MitchellFilter> MitchellFilter::m_registration( "Mitchell" );
Filter::FilterRegistration<SincFilter> SincFilter::m_registration( "Sinc" );

}; // namespace GafferImage

