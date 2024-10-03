//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Constraint.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/CurvesPrimitive.h"
#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/PointsPrimitive.h"

#include "fmt/format.h"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <limits>

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

template< typename Indexer >
bool convexPolygon( const Indexer vertices, const int n )
{
	assert( n >= 3 );

	if( n == 3 )
	{
		return true;
	}

	int c[ 2 ] = { 0, 0 };

	for( int i = 0; i < n; ++i )
	{
		const int ip = ( i + n - 1 ) % n;
		const int in = ( i     + 1 ) % n;

		const Imath::V2f vi = vertices( i );

		const float Av = ( vi - vertices( ip ) ) % ( vertices( in ) - vi );

		// NOTE : colinear edges are ok

		if( Av == 0.f )
		{
			c[ 0 ] += 1;
			c[ 1 ] += 1;
		}
		else
		{
			c[ std::signbit( Av ) ? 0 : 1 ] += 1;
		}
	}

	return
		( c[ 0 ] == n ) ||
		( c[ 1 ] == n );
}

template< typename Indexer >
bool ptInPolygon( const Indexer vertices, const Imath::V2f v, const int n )
{
	bool result = false;
	for( int i = 0; i < n; ++i )
	{
		const Imath::V2f v0 = vertices( i );
		const Imath::V2f v1 = vertices( ( i + 1 ) % n );

		// NOTE: Algorithm 3.5, "Collision Detection in Interactive 3d Environments", Gino Van Den Bergen
		//       with modifications to include end points and points on axis aligned edges.

		if( v0 == v )
		{
			return true; // NOTE : end point
		}
		else if(
			( ( v0.y == v1.y ) && ( v.y == v0.y ) && ( ( v0.x >= v.x ) != ( v1.x >= v.x ) ) ) ||
			( ( v0.x == v1.x ) && ( v.x == v0.x ) && ( ( v0.y >= v.y ) != ( v1.y >= v.y ) ) ) )
		{
			return true; // NOTE : axis aligned edge
		}
		else if( ( v0.y >= v.y ) != ( v1.y >= v.y ) )
		{
			// Edge crosses horizontal line `y == v.y`

			if( ( v0.x >= v.x ) != ( v1.x >= v.x ) )
			{
				// Edge crosses vertical line `x == v.x`

				if( v0.x + ( v.y - v0.y ) * ( v1.x - v0.x ) / ( v1.y - v0.y ) >= v.x )
				{
					// Edge crosses the ray `y == v.y, x >= v.x`

					result = !result;
				}
			}
			else if( v0.x >= v.x )
			{
				// Edge crosses the ray `y == v.y, x >= v.x`

				result = !result;
			}
		}
	}

	return result;
}

template< typename PIndexer, typename UVIndexer >
Imath::V3f interpolateConvexPolygon( const PIndexer points, const UVIndexer uvs, const Imath::V2f uv, const int n )
{
	// NOTE : compute vertex and edge triangle areas
	//
	//        Av[ i ] is 2 * area of the triangle formed by the vertices v(i-1), v(i) and v(i+1)
	//        Ae[ i ] is 2 * area of the triangle formed by the vertices v(i), v(i+1) and uv

	std::unique_ptr< float[] > Av( new float[ n ] );
	std::unique_ptr< float[] > Ae( new float[ n ] );

	for( int i = 0; i < n; ++i )
	{
		const Imath::V2f vi = uvs( i );

		// NOTE : avoid zero length edges by skipping past adjacent duplicate uv vertices
		//        in both directions, c is the number of times the duplicate vertex occurs
		//        in a consecutive run including the current vertex (vi). It is important
		//        that only adjacent duplicated vertices are included. The computed vertex
		//        area is weighted by the reciprocal of c to average the influence of the
		//        positions corresponding to the duplicated uv vertices.

		float c = 1.f;

		Imath::V2f vp;
		for( int j = 1; j < n; ++j )
		{
			vp = uvs( ( i + n - j ) % n );
			if( vp != vi ) break;
			c += 1.f;
		}

		Imath::V2f vn;
		for( int j = 1; j < n; ++j )
		{
			vn = uvs( ( i + j ) % n );
			if( vn != vi ) break;
			c += 1.f;
		}

		Av[ i ] = ( vi - vp ) % ( vn - vi );
		Ae[ i ] = ( vn - vi ) % ( uv - vn );

		// NOTE : sign of vertex area depends on winding.

		if( std::signbit( Av[ i ] ) )
		{
			Av[ i ] = -( Av[ i ] );
			Ae[ i ] = -( Ae[ i ] );
		}

		// NOTE : clamp edge area to minimum of zero to prevent negative weights

		Ae[ i ] = std::max( Ae[ i ], 0.f );

		// NOTE : this clamp is done in two steps to prevent underflow to zero

		Av[ i ] = std::max( Av[ i ], c * std::numeric_limits< float >::min() );
		Av[ i ] /= c;

		// NOTE : uv is considered on an edge when the edge area is below threshold in which
		//        case lerp between average of all positions corresponding to end vertices

		if(
			( Ae[ i ] < std::sqrt( std::numeric_limits< float >::min() ) ) &&
			( ( ( uv - vi ) ^ ( uv - vn ) ) < std::numeric_limits< float >::min() ) )
		{
			const float l2 = ( vn - vi ).length2();
			const float t = std::min( std::max(
				( l2 > ( 2.f * std::numeric_limits< float >::min() ) )
					? std::sqrt( ( uv - vn ).length2() / l2 ) : 0.f, 0.f ), 1.f );

			Imath::V3f pv( 0.f );
			Imath::V3f pn( 0.f );

			float pvc = 0.f;
			float pnc = 0.f;

			for( int j = 0; j < n; ++j )
			{
				if( uvs( j ) == vi )
				{
					pv += points( j );
					pvc += 1.f;
				}
				if( uvs( j ) == vn )
				{
					pn += points( j );
					pnc += 1.f;
				}
			}

			assert( pvc != 0.f );
			assert( pnc != 0.f );

			return
				( pv / pvc ) * (       t ) +
				( pn / pnc ) * ( 1.0 - t );
		}
	}

	// NOTE : uv is not on any edges or coincident with any vertices use wachspress coordinates
	//        the factor of 2 in the denominator cancels out during normalisation

	float ws = 0.f;
	Imath::V3f p( 0.f );

	for( int i = 0; i < n; ++i )
	{
		const Imath::V2f vi = uvs( i );

		int ip = 0;
		for( int j = 1; j < n; ++j )
		{
			ip = ( i + n - j ) % n;
			if( uvs( ip ) != vi )
				break;
		}

		const float Ad = Ae[ ip ] * Ae[ i ];

		if( Ad != 0.f )
		{
			const float w = Av[ i ] / Ad;
			p += points( i ) * w;
			ws += w;
		}
	}

	if( ws != 0.f )
	{
		p /= ws;
	}

	return p;
}

template< typename PIndexer, typename UVIndexer >
Imath::V3f interpolateNonConvexPolygon( const PIndexer points, const UVIndexer uvs, const Imath::V2f uv, const int n )
{
	// NOTE : a simple triangle fan from any vertex will cover the non convex polygon
	//        the generated triangles may cover areas outside the polygon this is fine

	Imath::V3f p( 0.f );

	for( int i = 2; i < n; ++i )
	{
		const Imath::V2f tuv[ 3 ] =
		{
			uvs( 0 ),
			uvs( i - 1 ),
			uvs( i )
		};

		if( ptInPolygon( [ & tuv ]( const int ii ){ return tuv[ ii ]; }, uv, 3 ) )
		{
			const float w = ( tuv[ 2 ] - tuv[ 0 ] ) % ( tuv[ 1 ] - tuv[ 0 ] );

			if( w == 0.f )
			{
				// NOTE : uv triangle numerically has zero area so is effectively a line or point.
				//        position in 3d space is ambiguous unless the triangle in 3d space is a point.

				const Imath::V3f& vp = points( i - 1 );

				if(
					( ( points( 0 ) - vp ).length2() <= ( 2.f * std::numeric_limits< float >::min() ) ) &&
					( ( points( i ) - vp ).length2() <= ( 2.f * std::numeric_limits< float >::min() ) ) )
				{
					p = vp;

					break;
				}

				throw IECore::InvalidArgumentException( fmt::format(
					"Gaffer::Constraint : UV coordinates \"{}, {}\" map to ambiguous point(s) in 3d space.",
					uv.x, uv.y
				) );
			}

			// NOTE : ensure that the positive barycentric coordinates sum to a maximum of one.

			const float b0 = std::max( 0.f, ( ( tuv[ 1 ] - tuv[ 2 ] ) % ( uv - tuv[ 1 ] ) ) / w );
			const float b1 = std::max( 0.f, ( ( tuv[ 2 ] - tuv[ 0 ] ) % ( uv - tuv[ 2 ] ) ) / w );
			const float b2 = std::max( 0.f, ( ( tuv[ 0 ] - tuv[ 1 ] ) % ( uv - tuv[ 0 ] ) ) / w );

			const float bs = b0 + b1 + b2;

			if( bs != 0.f )
			{
				p =
					points(     0 ) * ( b0 / bs ) +
					points( i - 1 ) * ( b1 / bs ) +
					points( i     ) * ( b2 / bs );

				break;
			}
		}
	}

	return p;
}

void constructMatrix( Imath::M44f& m, const Imath::V3f& p, const Imath::V3f& x, const Imath::V3f& y, const Imath::V3f& z )
{
	m[ 0 ][ 0 ] = x[ 0 ];
	m[ 0 ][ 1 ] = x[ 1 ];
	m[ 0 ][ 2 ] = x[ 2 ];
	m[ 0 ][ 3 ] = 0.f;

	m[ 1 ][ 0 ] = y[ 0 ];
	m[ 1 ][ 1 ] = y[ 1 ];
	m[ 1 ][ 2 ] = y[ 2 ];
	m[ 1 ][ 3 ] = 0.f;

	m[ 2 ][ 0 ] = z[ 0 ];
	m[ 2 ][ 1 ] = z[ 1 ];
	m[ 2 ][ 2 ] = z[ 2 ];
	m[ 2 ][ 3 ] = 0.f;

	m[ 3 ][ 0 ] = p[ 0 ];
	m[ 3 ][ 1 ] = p[ 1 ];
	m[ 3 ][ 2 ] = p[ 2 ];
	m[ 3 ][ 3 ] = 1.f;
}

void constructLocalFrame( Imath::M44f& m, const Imath::V3f& p, const Imath::V3f& t, const Imath::V3f& b, const Imath::V3f& n )
{
	// NOTE : use tangent and bitangent when both have non zero length and are not colinear
	//        and either the normal has zero length or both the tangent and bitangent are
	//        not colinear with the normal, otherwise use tangent and normal when they both
	//        have non zero length and are not colinear, otherwise use bitangent and normal
	//        when they both have non zero length and are not colinear

	const Imath::V3f nt = t.normalized();
	const Imath::V3f nb = b.normalized();
	const Imath::V3f nn = n.normalized();
	const Imath::V3f bxt = nb % nt;
	const Imath::V3f txn = nt % nn;
	const Imath::V3f nxb = nn % nb;

	if(
		( bxt.length2() > ( 2.f * std::numeric_limits< float >::min() ) ) &&
		( ( n.length2() < ( 2.f * std::numeric_limits< float >::min() ) ) ||
			( ( std::fabs( nt ^ nn ) < 0.999f ) && ( std::fabs( nb ^ nn ) < 0.999f ) ) ) )
	{
		Imath::V3f y = bxt.normalized();

		// NOTE : ensure y axis of local frame points in same direction as normal

		if( n.dot( y ) < 0.f )
		{
			y *= -1.f;
		}

		constructMatrix( m, p, nt, y, ( nt % y ).normalized() );
	}
	else if( txn.length2() > ( 2.f * std::numeric_limits< float >::min() ) )
	{
		const Imath::V3f z = txn.normalized();
		constructMatrix( m, p, nt, ( z % nt ).normalized(), z );
	}
	else if( nxb.length2() > ( 2.f * std::numeric_limits< float >::min() ) )
	{
		const Imath::V3f x = nxb.normalized();
		constructMatrix( m, p, x, ( nb % x ).normalized(), nb );
	}
	else
	{
		m.translate( p );
	}
}

struct UVIndexer
{
	UVIndexer( const IECoreScene::MeshPrimitive& primitive, const std::string& uvSet, const bool throwOnError )
	: m_indices( nullptr )
	, m_view()
	{
		const IECoreScene::PrimitiveVariableMap::const_iterator it = primitive.variables.find( uvSet );

		if(
			( it == primitive.variables.end() ) ||
			( ( *it ).second.data->typeId() != IECore::V2fVectorDataTypeId ) )
		{
			if( throwOnError )
			{
				throw IECore::InvalidArgumentException( fmt::format(
					"Gaffer::Constraint : MeshPrimitive has no V2fVectorData primitive variable named \"{}\".",
					uvSet
				) );
			}
			else
			{
				return;
			}
		}

		// NOTE : for vertex and varying interpolation we need to redirect through the primitive indices

		if(
			( ( *it ).second.interpolation == IECoreScene::PrimitiveVariable::Vertex ) ||
			( ( *it ).second.interpolation == IECoreScene::PrimitiveVariable::Varying ) )
		{
			m_indices = &( primitive.vertexIds()->readable() );
		}
		else if( ( *it ).second.interpolation != IECoreScene::PrimitiveVariable::FaceVarying )
		{
			if( throwOnError )
			{
				throw IECore::InvalidArgumentException( fmt::format(
					"Gaffer::Constraint : Primitive variable named \"{}\" has incorrect interpolation, must be either Vertex, Varying or FaceVarying",
					uvSet
				) );
			}
			else
			{
				return;
			}
		}

		m_view = IECoreScene::PrimitiveVariable::IndexedView< Imath::V2f >( ( *it ).second );
	}

	bool valid() const
	{
		return static_cast< bool >( m_view );
	}

	const Imath::V2f& operator[]( const int i ) const
	{
		assert( valid() );
		const int index = ( m_indices != nullptr ) ? ( ( *m_indices )[ i ] ) : i;
		return ( *m_view )[ index ];
	}

private:

	const std::vector< int >* m_indices;
	std::optional<IECoreScene::PrimitiveVariable::IndexedView<Imath::V2f>> m_view;
};

void computePrimitiveVertexLocalFrame( const IECoreScene::Primitive& primitive, Imath::M44f& m, const int vertexId, const bool throwOnError )
{
	const IECore::V3fVectorData* const pdata = primitive.variableData< IECore::V3fVectorData >( "P" );
	if( pdata == nullptr )
	{
		if( throwOnError )
		{
			throw IECore::InvalidArgumentException( "Gaffer::Contraint : Primitive has no Vertex \"P\" primitive variable." );
		}
		else
		{
			return;
		}
	}
	const IECore::V3fVectorData::ValueType& points = pdata->readable();

	if( ( vertexId < 0 ) || ( vertexId >= static_cast< int >( points.size() ) ) )
	{
		if( throwOnError )
		{
			throw IECore::InvalidArgumentException( fmt::format(
				"Gaffer::Constraint : Vertex id \"{}\" is out of range.",
				vertexId
			) );
		}
		else
		{
			return;
		}
	}

	m.translate( points[ vertexId ] );
}

void computeMeshVertexLocalFrame( const IECoreScene::MeshPrimitive& primitive, Imath::M44f& m, const int vertexId, const std::string& uvSet, const bool throwOnError, const IECore::Canceller* const canceller )
{
	const IECore::V3fVectorData* const pdata = primitive.variableData< IECore::V3fVectorData >( "P" );

	if( pdata == nullptr )
	{
		if( throwOnError )
		{
			throw IECore::InvalidArgumentException( "Gaffer::Contraint : MeshPrimitive has no Vertex \"P\" primitive variable." );
		}
		else
		{
			return;
		}
	}

	const IECore::V3fVectorData::ValueType& points = pdata->readable();

	if( ( vertexId < 0 ) || ( vertexId >= static_cast< int >( points.size() ) ) )
	{
		if( throwOnError )
		{
			throw IECore::InvalidArgumentException( fmt::format(
				"Gaffer::Constraint : Vertex id \"{}\" is out of range.",
				vertexId
			) );
		}
		else
		{
			return;
		}
	}

	const IECore::IntVectorData::ValueType& indices = primitive.vertexIds()->readable();
	const IECore::IntVectorData::ValueType& faces = primitive.verticesPerFace()->readable();

	const UVIndexer uvs( primitive, uvSet, throwOnError );

	Imath::V3f t( 0.f );
	Imath::V3f b( 0.f );
	Imath::V3f n( 0.f );

	if( uvs.valid() )
	{
		int js = 0;
		for( int i = 0; i < static_cast< int >( faces.size() ); ++i )
		{
			const int ni = faces[ i ];

			// canceller support

			if( ( i % 100 ) == 0 )
			{
				IECore::Canceller::check( canceller );
			}

			// find matching face vertex index

			int jm = 0;
			for( ; jm < ni; ++jm )
			{
				if( indices[ js + jm ] == vertexId )
				{
					break;
				}
			}

			if( jm < ni )
			{
				// compute face normal, tangent and bitangent

				Imath::V3f ft( 0.f );
				Imath::V3f fb( 0.f );
				Imath::V3f fn( 0.f );

				float w = 0.f;

				for( int j = 0; j < ni; ++j )
				{
					const int iv = js + j;
					const int ip = js + ( ( j + ni - 1 ) % ni );
					const int in = js + ( ( j      + 1 ) % ni );

					const Imath::V3f pv = points[ indices[ iv ] ];
					const Imath::V3f v0 = points[ indices[ ip ] ] - pv;
					const Imath::V3f v2 = points[ indices[ in ] ] - pv;

					const Imath::V2f uv = uvs[ iv ];
					const Imath::V2f e0 = uvs[ ip ] - uv;
					const Imath::V2f e2 = uvs[ in ] - uv;

					ft += ( v0 * -e2.y + v2 * e0.y ).normalized();
					fb += ( v0 * -e2.x + v2 * e0.x ).normalized();
					fn += ( -v0 % v2 ).normalized();

					if( j == jm )
					{
						const float lv2 = v0.length2() * v2.length2();

						if( lv2 > ( 2.f * std::numeric_limits< float >::min() ) )
						{
							const float lv = std::sqrt( lv2 );

							if( lv != 0.f )
							{
								w = std::acos( std::min( std::max( ( v0 ^ v2 ) / lv, -1.f ), 1.f ) );
							}
						}
					}
				}

				// accumulate angle weighted normal, tangent and bitangent

				t += ft.normalized() * w;
				b += fb.normalized() * w;
				n += fn.normalized() * w;
			}

			js += ni;
		}
	}

	constructLocalFrame( m, points[ vertexId ], t, b, n );
}

void computeVertexLocalFrame( const IECore::Object& object, Imath::M44f& m, const int vertexId, const std::string& uvSet, const bool throwOnError, const IECore::Canceller* const canceller )
{
	switch( static_cast< IECoreScene::TypeId >( object.typeId() ) )
	{
		case IECoreScene::CurvesPrimitiveTypeId:
		case IECoreScene::PointsPrimitiveTypeId:
			computePrimitiveVertexLocalFrame( static_cast< const IECoreScene::Primitive& >( object ), m, vertexId, throwOnError );
			break;
		case IECoreScene::MeshPrimitiveTypeId:
			computeMeshVertexLocalFrame( static_cast< const IECoreScene::MeshPrimitive& >( object ), m, vertexId, uvSet, throwOnError, canceller );
			break;
		default:
			if( throwOnError )
			{
				throw IECore::InvalidArgumentException( fmt::format(
					"Gaffer::Constraint : Target primitive of type \"{}\" is not supported in Vertex target mode.",
					object.typeName()
				) );
			}
			break;
	}
}

void computeMeshUVLocalFrame( const IECoreScene::MeshPrimitive& primitive, Imath::M44f& m, const Imath::V2f& uv, const std::string& uvSet, const bool throwOnError, const IECore::Canceller* const canceller )
{
	const IECore::V3fVectorData* const pdata = primitive.variableData< IECore::V3fVectorData >( "P" );

	if( pdata == nullptr )
	{
		if( throwOnError )
		{
			throw IECore::InvalidArgumentException( "Gaffer::Contraint : MeshPrimitive has no Vertex \"P\" primitive variable." );
		}
		else
		{
			return;
		}
	}

	const IECore::V3fVectorData::ValueType& points = pdata->readable();
	const IECore::IntVectorData::ValueType& indices = primitive.vertexIds()->readable();
	const IECore::IntVectorData::ValueType& faces = primitive.verticesPerFace()->readable();

	const UVIndexer uvs( primitive, uvSet, throwOnError );
	if( ! uvs.valid() )
	{
		return;
	}

	int js = 0;
	for( int i = 0; i < static_cast< int >( faces.size() ); ++i )
	{
		const int ni = faces[ i ];

		// canceller support

		if( ( i % 100 ) == 0 )
		{
			IECore::Canceller::check( canceller );
		}

		// points and uv indexers

		const auto pIndexer = [ & points, & indices, js ]( const int ii )
		{
			return points[ indices[ js + ii ] ];
		};

		const auto uvIndexer = [ & uvs, js ]( const int ii )
		{
			return uvs[ js + ii ];
		};

		// determine if uv coordinate is inside face

		if( ptInPolygon( uvIndexer, uv, ni ) )
		{
			Imath::V3f fp( 0.f );
			Imath::V3f ft( 0.f );
			Imath::V3f fb( 0.f );
			Imath::V3f fn( 0.f );

			try
			{
				fp = ( convexPolygon( uvIndexer, ni ) )
					? interpolateConvexPolygon( pIndexer, uvIndexer, uv, ni )
					: interpolateNonConvexPolygon( pIndexer, uvIndexer, uv, ni );

				// compute face tangent and bitangent

				for( int j = 0; j < ni; ++j )
				{
					const int iv = js + j;
					const int ip = js + ( ( j + ni - 1 ) % ni );
					const int in = js + ( ( j      + 1 ) % ni );

					const Imath::V3f pv = points[ indices[ iv ] ];
					const Imath::V3f v0 = points[ indices[ ip ] ] - pv;
					const Imath::V3f v2 = points[ indices[ in ] ] - pv;

					const Imath::V2f uvv = uvs[ iv ];
					const Imath::V2f e0 = uvs[ ip ] - uvv;
					const Imath::V2f e2 = uvs[ in ] - uvv;

					ft += ( v0 * -e2.y + v2 * e0.y ).normalized();
					fb += ( v0 * -e2.x + v2 * e0.x ).normalized();
					fn += ( -v0 % v2 ).normalized();
				}
			}
			catch( const IECore::Exception & )
			{
				if( throwOnError )
				{
					throw;
				}
			}

			constructLocalFrame( m, fp, ft, fb, fn );

			return;
		}

		js += ni;
	}

	if( throwOnError )
	{
		throw IECore::InvalidArgumentException( fmt::format(
			"Gaffer::Constraint : UV coordinates \"{}, {}\" are out of range.",
			uv.x, uv.y
		) );
	}
}

void computeUVLocalFrame( const IECore::Object& object, Imath::M44f& m, const Imath::V2f& uv, const std::string& uvSet, const bool throwOnError, const IECore::Canceller* const canceller )
{
	switch( static_cast< IECoreScene::TypeId >( object.typeId() ) )
	{
		case IECoreScene::MeshPrimitiveTypeId:
			computeMeshUVLocalFrame( static_cast< const IECoreScene::MeshPrimitive& >( object ), m, uv, uvSet, throwOnError, canceller );
			break;
		default:
			if( throwOnError )
			{
				throw IECore::InvalidArgumentException( fmt::format(
					"Gaffer::Constraint : Target primitive of type \"{}\" is not supported in UV target mode.",
					object.typeName()
				) );
			}
			break;
	}
}

struct ReferenceFrameScope : public Context::EditableScope
{

	ReferenceFrameScope( const Gaffer::Context *context, const Constraint *constraint )
		: Context::EditableScope( context )
	{
		const float frame = constraint->referenceFramePlug()->getValue();
		setFrame( frame );
		if( !constraint->inPlug()->existsPlug()->getValue() )
		{
			const ScenePlug::ScenePath &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
			throw IECore::Exception( fmt::format(
				"Constrained object \"{}\" does not exist at reference frame {}",
				ScenePlug::pathToString( path ), frame
			) );
		}
	}

};

} // namespace

GAFFER_NODE_DEFINE_TYPE( Constraint );

size_t Constraint::g_firstPlugIndex = 0;

Constraint::Constraint( const std::string &name )
	:	SceneElementProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "targetScene" ) );
	addChild( new StringPlug( "target" ) );
	addChild( new BoolPlug( "ignoreMissingTarget" ) );
	addChild( new IntPlug( "targetMode", Plug::In, Constraint::Origin, Constraint::Origin, Constraint::Vertex ) );
	addChild( new V2fPlug( "targetUV" ) );
	addChild( new IntPlug( "targetVertex", Plug::In, 0, 0 ) );
	addChild( new V3fPlug( "targetOffset" ) );
	addChild( new BoolPlug( "keepReferencePosition" ) );
	addChild( new FloatPlug( "referenceFrame", Plug::In, 1.0 ) );
	addChild( new M44fPlug( "__targetModeMatrix", Plug::Out ) );
	addChild( new M44fPlug( "__constrainedTransform", Plug::Out ) );

	// Pass through things we don't want to modify
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
}

Constraint::~Constraint()
{
}

ScenePlug *Constraint::targetScenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *Constraint::targetScenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *Constraint::targetPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *Constraint::targetPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *Constraint::ignoreMissingTargetPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *Constraint::ignoreMissingTargetPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::IntPlug *Constraint::targetModePlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::IntPlug *Constraint::targetModePlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 3 );
}

Gaffer::V2fPlug *Constraint::targetUVPlug()
{
	return getChild<Gaffer::V2fPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::V2fPlug *Constraint::targetUVPlug() const
{
	return getChild<Gaffer::V2fPlug>( g_firstPlugIndex + 4 );
}

Gaffer::IntPlug *Constraint::targetVertexPlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::IntPlug *Constraint::targetVertexPlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 5 );
}

Gaffer::V3fPlug *Constraint::targetOffsetPlug()
{
	return getChild<Gaffer::V3fPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::V3fPlug *Constraint::targetOffsetPlug() const
{
	return getChild<Gaffer::V3fPlug>( g_firstPlugIndex + 6 );
}

Gaffer::BoolPlug *Constraint::keepReferencePositionPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::BoolPlug *Constraint::keepReferencePositionPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 7 );
}

Gaffer::FloatPlug *Constraint::referenceFramePlug()
{
	return getChild<Gaffer::FloatPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::FloatPlug *Constraint::referenceFramePlug() const
{
	return getChild<Gaffer::FloatPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::M44fPlug *Constraint::targetModeMatrixPlug() const
{
	return getChild<Gaffer::M44fPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::M44fPlug *Constraint::constrainedTransformPlug() const
{
	return getChild<Gaffer::M44fPlug>( g_firstPlugIndex + 10 );
}

void Constraint::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( affectsTargetModeMatrix( input ) )
	{
		outputs.push_back( targetModeMatrixPlug() );
	}

	if( affectsConstrainedTransform( input ) )
	{
		outputs.push_back( constrainedTransformPlug() );
	}

	if(
		input == constrainedTransformPlug() ||
		input == keepReferencePositionPlug() ||
		input == referenceFramePlug() ||
		// TypeId comparison is necessary to avoid calling pure virtual
		// if we're called before being fully constructed.
		( typeId() != staticTypeId() && affectsConstraint( input ) )
	)
	{
		outputs.push_back( outPlug()->transformPlug() );

		// This output of boundPlug seems unnecessary.  According to John: this was to account for
		// the SceneElementProcessor base class computing new bounds based on the new transforms that
		// we produce. But since the base class declares an out.childBounds -> out.bound dependency,
		// and SceneNode declares an out.transform -> out.childBounds dependency I think is redundant
		// now (but probably wasn't orginally, because childBounds is relatively recent).
		//
		// I don't want to risk changing behaviour while working on something unrelated, so not actually
		// removing it yet, just leaving a note for the next person to work on this.
		outputs.push_back( outPlug()->boundPlug() );
	}
}

void Constraint::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == targetModeMatrixPlug() )
	{
		hashTargetModeMatrix( context, h );
	}
	else if( output == constrainedTransformPlug() )
	{
		hashConstrainedTransform( context, h );
	}
	else
	{
		SceneElementProcessor::hash( output, context, h );
	}
}

void Constraint::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == targetModeMatrixPlug() )
	{
		static_cast<M44fPlug *>( output )->setValue( computeTargetModeMatrix( context ) );
	}
	else if( output == constrainedTransformPlug() )
	{
		static_cast<M44fPlug *>( output )->setValue( computeConstrainedTransform( context ) );
	}
	else
	{
		SceneElementProcessor::compute( output, context);
	}
}

bool Constraint::affectsTargetModeMatrix( const Gaffer::Plug *input ) const
{
	return
		input == targetModePlug() ||
		affectsTarget( input ) ||
		input == inPlug()->boundPlug() ||
		input == targetScenePlug()->boundPlug() ||
		input == inPlug()->objectPlug() ||
		input == targetScenePlug()->objectPlug() ||
		input == ignoreMissingTargetPlug() ||
		input->parent() == targetUVPlug() ||
		input == targetVertexPlug()
	;
}

void Constraint::hashTargetModeMatrix( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneElementProcessor::hash( targetModePlug(), context, h );

	const TargetMode targetMode = (TargetMode)targetModePlug()->getValue();
	h.append( targetMode );

	if( targetMode == Constraint::Origin )
	{
		return;
	}

	const Target target = this->target().value();

	switch( targetMode )
	{
		case Constraint::BoundMin:
		case Constraint::BoundMax:
		case Constraint::BoundCenter:
			h.append( target.scene->boundHash( target.path ) );
			break;
		case Constraint::UV:
			h.append( target.scene->objectHash( target.path ) );
			ignoreMissingTargetPlug()->hash( h );
			targetUVPlug()->hash( h );
			break;
		case Constraint::Vertex:
			h.append( target.scene->objectHash( target.path ) );
			ignoreMissingTargetPlug()->hash( h );
			targetVertexPlug()->hash( h );
			break;
		default:
			break;
	}
}

Imath::M44f Constraint::computeTargetModeMatrix( const Gaffer::Context *context ) const
{
	const TargetMode targetMode = (TargetMode)targetModePlug()->getValue();
	if( targetMode == Constraint::Origin )
	{
		return M44f();
	}

	// This plug is never evaluated unless the target exists, so we
	// don't need to consider the case where `optional<Target>` is empty.
	const Target target = this->target().value();
	switch( targetMode )
	{
		case Constraint::BoundMin:
		case Constraint::BoundMax:
		case Constraint::BoundCenter:
		{
			const Box3f targetBound = target.scene->bound( target.path );
			if( !targetBound.isEmpty() )
			{
				switch( targetMode )
				{
					case Constraint::BoundMin : return M44f().translate( targetBound.min );
					case Constraint::BoundMax : return M44f().translate( targetBound.max );
					case Constraint::BoundCenter : return M44f().translate( targetBound.center() );
					default : break;
				}
			}
			return M44f();
		}
		case Constraint::UV:
		{
			const IECore::ConstObjectPtr object = target.scene->object( target.path );
			const Imath::V2f uv = targetUVPlug()->getValue();
			const bool throwOnError = !( ignoreMissingTargetPlug()->getValue() );
			M44f result;
			computeUVLocalFrame( *object, result, uv, "uv", throwOnError, context->canceller() );
			return result;
		}
		case Constraint::Vertex:
		{
			const IECore::ConstObjectPtr object = target.scene->object( target.path );
			const int vertexId = targetVertexPlug()->getValue();
			const bool throwOnError = !( ignoreMissingTargetPlug()->getValue() );
			M44f result;
			computeVertexLocalFrame( *object, result, vertexId, "uv", throwOnError, context->canceller() );
			return result;
		}
		default:
			return M44f();
	}
}

bool Constraint::affectsConstrainedTransform( const Gaffer::Plug *input ) const
{
	return
		input == inPlug()->transformPlug() ||
		input == targetPlug() ||
		input == ignoreMissingTargetPlug() ||
		input == targetScenePlug()->existsPlug() ||
		input == inPlug()->existsPlug() ||
		input == targetScenePlug()->transformPlug() ||
		input == targetModeMatrixPlug() ||
		input->parent() == targetOffsetPlug() ||
		affectsConstraint( input )
	;
}

void Constraint::hashConstrainedTransform( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneElementProcessor::hash( constrainedTransformPlug(), context, h );

	inPlug()->transformPlug()->hash( h );

	auto targetOpt = target();
	if( !targetOpt )
	{
		return;
	}

	const ScenePath &path = context->get<ScenePath>( ScenePlug::scenePathContextName );
	const ScenePath parentPath( path.begin(), path.end() - 1 );

	h.append( inPlug()->fullTransformHash( parentPath ) );

	h.append( targetOpt->scene->fullTransformHash( targetOpt->path ) );
	targetModeMatrixPlug()->hash( h );
	targetOffsetPlug()->hash( h );

	hashConstraint( context, h );
}

Imath::M44f Constraint::computeConstrainedTransform( const Gaffer::Context *context ) const
{
	const M44f inputTransform = inPlug()->transformPlug()->getValue();

	auto targetOpt = target();
	if( !targetOpt )
	{
		return inputTransform;
	}

	// \todo - It's not obvious how we can use something like the hypothetical SceneAlgo::relativeTransform
	// here - unlike MergeObjects and BranchCreator, where the handling of relative transforms is entirely
	// internal, and the correct solution is pretty clear, here the use of world space is part of the API of
	// computeConstraint. However, it is still true that it would in many cases be desirable for this to output
	// fully accurate results even if the whole scene is placed under a large fixed transform ( whereas currently
	// this can introduce a lot of imprecision since we're working in world space ).

	const ScenePath &path = context->get<ScenePath>( ScenePlug::scenePathContextName );
	const ScenePath parentPath( path.begin(), path.end() - 1 );

	const M44f parentTransform = inPlug()->fullTransform( parentPath );
	const M44f fullInputTransform = inputTransform * parentTransform;

	M44f fullTargetTransform = targetOpt->scene->fullTransform( targetOpt->path );
	fullTargetTransform = targetModeMatrixPlug()->getValue() * fullTargetTransform;
	fullTargetTransform.translate( targetOffsetPlug()->getValue() );

	const M44f fullConstrainedTransform = computeConstraint( fullTargetTransform, fullInputTransform, inputTransform );
	return fullConstrainedTransform * parentTransform.inverse();
}

bool Constraint::processesTransform() const
{
	return true;
}

void Constraint::hashProcessedTransform( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	constrainedTransformPlug()->hash( h );
	if( keepReferencePositionPlug()->getValue() )
	{
		ReferenceFrameScope referenceFrameScope( context, this );
		constrainedTransformPlug()->hash( h );
		inPlug()->transformPlug()->hash( h );
	}
}

Imath::M44f Constraint::computeProcessedTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const
{
	M44f constrainedTransform = constrainedTransformPlug()->getValue();
	if( keepReferencePositionPlug()->getValue() )
	{
		ReferenceFrameScope referenceFrameScope( context, this );

		const M44f referenceConstrainedTransform = constrainedTransformPlug()->getValue();
		const M44f referenceInputTransform = inPlug()->transformPlug()->getValue();

		const M44f correction = referenceConstrainedTransform * referenceInputTransform.inverse();
		constrainedTransform = correction.inverse() * constrainedTransform;
	}

	return constrainedTransform;
}

bool Constraint::affectsTarget( const Gaffer::Plug *input ) const
{
	return
		input == targetPlug() ||
		input == targetScenePlug()->existsPlug() ||
		input == inPlug()->existsPlug() ||
		input == ignoreMissingTargetPlug()
	;
}

std::optional<Constraint::Target> Constraint::target() const
{
	std::string targetPathAsString = targetPlug()->getValue();
	if( targetPathAsString == "" )
	{
		return std::nullopt;
	}

	ScenePath targetPath;
	ScenePlug::stringToPath( targetPathAsString, targetPath );

	const ScenePlug *targetScene = targetScenePlug();
	if( !targetScene->getInput() )
	{
		// Default to using the main input if no specific `targetScene` plug
		// has been connected
		targetScene = inPlug();
	}

	if( !targetScene->exists( targetPath ) )
	{
		if( ignoreMissingTargetPlug()->getValue() )
		{
			return std::nullopt;
		}
		else
		{
			throw IECore::Exception( fmt::format(
				"Constraint target does not exist: \"{}\". Use 'ignoreMissingTarget' option if you want to just skip this constraint",
				targetPathAsString
			) );
		}
	}

	return Target( { targetPath, targetScene } );
}
