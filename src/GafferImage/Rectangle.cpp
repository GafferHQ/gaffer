//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, John Haddon. All rights reserved.
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

#include "GafferImage/Rectangle.h"

#include "Gaffer/Transform2DPlug.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// Rounds min down, and max up, while converting from float to int.
Box2i box2fToBox2i( const Box2f &b )
{
	return Box2i(
		V2i( floor( b.min.x ), floor( b.min.y ) ),
		V2i( ceil( b.max.x ), ceil( b.max.y ) )
	);
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

float filteredPulse( float edge0, float edge1, float x, float w )
{
	float x0 = x - w / 2.0;
	float x1 = x + w / 2.0;
	return std::max( 0.0f, ( std::min( x1, edge1 ) - std::max( x0, edge0 ) ) / w );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Rectangle
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Rectangle );

size_t Rectangle::g_firstPlugIndex = 0;

Rectangle::Rectangle( const std::string &name )
	:	Shape( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new Box2fPlug( "area", Plug::In, Box2f( V2f( 0 ), V2f( 100 ) ) ) );
	addChild( new FloatPlug( "lineWidth", Plug::In, 4.0f, 0.0f ) );
	addChild( new FloatPlug( "cornerRadius", Plug::In, 0.0f, 0.0f ) );
	addChild( new Transform2DPlug( "transform" ) );
}

Rectangle::~Rectangle()
{
}

Gaffer::Box2fPlug *Rectangle::areaPlug()
{
	return getChild<Box2fPlug>( g_firstPlugIndex );
}

const Gaffer::Box2fPlug *Rectangle::areaPlug() const
{
	return getChild<Box2fPlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *Rectangle::lineWidthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *Rectangle::lineWidthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

Gaffer::FloatPlug *Rectangle::cornerRadiusPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *Rectangle::cornerRadiusPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

Gaffer::Transform2DPlug *Rectangle::transformPlug()
{
	return getChild<Transform2DPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::Transform2DPlug *Rectangle::transformPlug() const
{
	return getChild<Transform2DPlug>( g_firstPlugIndex + 3 );
}

bool Rectangle::affectsShapeDataWindow( const Gaffer::Plug *input ) const
{
	if( Shape::affectsShapeDataWindow( input ) )
	{
		return true;
	}

	return
		areaPlug()->isAncestorOf( input ) ||
		input == lineWidthPlug() ||
		transformPlug()->isAncestorOf( input )
	;
}

void Rectangle::hashShapeDataWindow( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Shape::hashShapeDataWindow( context, h );

	areaPlug()->hash( h );
	lineWidthPlug()->hash( h );
	transformPlug()->hash( h );
}

Imath::Box2i Rectangle::computeShapeDataWindow( const Gaffer::Context *context ) const
{
	Box2f b;
	b.extendBy( areaPlug()->minPlug()->getValue() );
	b.extendBy( areaPlug()->maxPlug()->getValue() );

	const float lineWidth = lineWidthPlug()->getValue();
	b.min -= V2f( lineWidth / 2.0f );
	b.max += V2f( lineWidth / 2.0f );

	b = transform( b, transformPlug()->matrix() );

	return box2fToBox2i( b );
}

bool Rectangle::affectsShapeChannelData( const Gaffer::Plug *input ) const
{
	if( Shape::affectsShapeChannelData( input ) )
	{
		return true;
	}

	return
		areaPlug()->isAncestorOf( input ) ||
		input == lineWidthPlug() ||
		input == cornerRadiusPlug() ||
		transformPlug()->isAncestorOf( input )
	;
}

void Rectangle::hashShapeChannelData( const Imath::V2i &tileOrigin, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Shape::hashShapeChannelData( tileOrigin, context, h );

	h.append( tileOrigin );
	areaPlug()->hash( h );
	lineWidthPlug()->hash( h );
	cornerRadiusPlug()->hash( h );
	transformPlug()->hash( h );
}

IECore::ConstFloatVectorDataPtr Rectangle::computeShapeChannelData(  const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const
{
	// Get our inputs

	Box2f area;
	area.extendBy( areaPlug()->minPlug()->getValue() );
	area.extendBy( areaPlug()->maxPlug()->getValue() );
	const V2f halfSize = area.size() / 2.0f;

	const float lineWidth = lineWidthPlug()->getValue();

	const M33f transform = transformPlug()->matrix();
	const M33f inverseTransform = transform.inverse();

	float cornerRadius = cornerRadiusPlug()->getValue();
	cornerRadius = std::min( cornerRadius, halfSize.x );
	cornerRadius = std::min( cornerRadius, halfSize.y );
	const V2f radiusCenter = area.max - area.center() - V2f( cornerRadius );

	// Figure out a filter width to use later.
	// See https://renderman.pixar.com/resources/RenderMan_20/basicAntialiasing.html.

	V2f du( 1.0f, 0.0f );
	V2f dv( 0.0f, 1.0f );
	inverseTransform.multDirMatrix( du, du );
	inverseTransform.multDirMatrix( dv, dv );

	const float filterWidth = sqrt( du.cross( dv ) );

	// Prepare data to return

	FloatVectorDataPtr resultData = new FloatVectorData();
	vector<float> &result = resultData->writable();
	result.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	// Generate the pixels. The general idea is to make a signed
	// distance field from the edge of the shape, and then use
	// `filteredPulse()` to draw an antialised line within it.

	V2i pi;
	for( pi.y = tileBound.min.y; pi.y < tileBound.max.y; ++pi.y )
	{
		for( pi.x = tileBound.min.x; pi.x < tileBound.max.x; ++pi.x )
		{
			// Convert from pixel position into
			// the coordinate system of the rectangle.
			V2f p = V2f( pi ) + V2f( 0.5 );
			p *= inverseTransform;

			// Flip into positive quadrant, relative
			// to rectangle center.
			p = V2f(
				fabs( p.x - area.center().x ),
				fabs( p.y - area.center().y )
			);

			// Get signed distance for basic rectangle.
			// We use manhattan distance because it gives
			// square corners.

			const float xd = p.x - area.size().x / 2.0f;
			const float yd = p.y - area.size().y / 2.0f;
			float d = max( xd, yd );

			// Adjust to account for rounded corners if
			// we want them.

			if( cornerRadius > 0 )
			{
				if( p.x > radiusCenter.x && p.y > radiusCenter.y )
				{
					const V2f v = p - radiusCenter;
					d = max( d, v.length() - cornerRadius );
				}
			}

			// Draw line
			result.push_back( filteredPulse( -lineWidth / 2.0f, lineWidth / 2.0f, d, filterWidth ) );
		}
	}

	return resultData;
}
