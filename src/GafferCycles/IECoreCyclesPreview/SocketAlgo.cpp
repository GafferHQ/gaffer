//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "IECore/SimpleTypedData.h"
#include "IECore/VectorTypedData.h"

// Cycles
#include "kernel/types.h" // for RAMP_TABLE_SIZE
#include "util/transform.h"
#include "util/types.h"
#include "util/vector.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreCycles;

namespace
{

template<typename T>
void convert( ccl::Node *node, const ccl::SocketType *socket, const IECore::Data *value )
{
	if( const T *data = static_cast<const T *>( value ) )
	{
		node->set( *socket, data->readable() );
	}
}

template<typename T, typename U>
void dataToArray( ccl::Node *node, const ccl::SocketType *socket, const IECore::Data *value )
{
	if( const U *data = static_cast<const U *>( value ) )
	{
		const auto &vector = data->readable();
		ccl::array<T> array( vector.size() );
		memcpy((void*)array.data(), &vector[0], vector.size() * sizeof(T) );
		node->set( *socket, array );
	}
}

template<typename T, typename U>
IECore::DataPtr arrayToData( const ccl::array<U>& array )
{
	typedef vector<T> VectorType;
	typedef IECore::TypedData<vector<T> > DataType;
	typename DataType::Ptr data = new DataType;
	VectorType &v = data->writable();
	v.reserve( array.size() );

	for( size_t i = 0; i < array.size(); ++i )
	{
		v.push_back( array[i] );
	}

	return data;
}

template<typename T>
IECore::DataPtr arrayToData( const ccl::array<ccl::float3>& array )
{
	typedef vector<T> VectorType;
	typedef IECore::TypedData<vector<T> > DataType;
	typename DataType::Ptr data = new DataType;
	VectorType &v = data->writable();
	v.reserve( array.size() );

	for( size_t i = 0; i < array.size(); ++i )
	{
		v.push_back( T( array[i][0], array[i][1], array[i][2]) );
	}
	return data;
}

} // namespace

namespace IECoreCycles
{

namespace SocketAlgo

{

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

ccl::float2 setVector( const Imath::V2f &vector )
{
	return ccl::make_float2( vector[0], vector[1] );
}

ccl::float3 setVector( const Imath::V3f &vector )
{
	return ccl::make_float3( vector[0], vector[1], vector[2] );
}

ccl::float3 setColor( const Imath::Color3f &color )
{
	return ccl::make_float3( color[0], color[1], color[2] );
}

ccl::float3 setColor( const Imath::Color4f &color )
{
	// Dropping alpha
	return ccl::make_float3( color[0], color[1], color[2] );
}

float setAlpha( const Imath::Color4f &color )
{
	return color[3];
}

ccl::float4 setQuaternion( const Imath::Quatf &quat )
{
	return ccl::make_float4( quat[0], quat[1], quat[2], quat[3] );
}

ccl::Transform setTransform( const Imath::M44d &matrix )
{
	ccl::Transform t;
	t.x = ccl::make_float4( (float)matrix[0][0], (float)matrix[1][0], (float)matrix[2][0], (float)matrix[3][0] );
	t.y = ccl::make_float4( (float)matrix[0][1], (float)matrix[1][1], (float)matrix[2][1], (float)matrix[3][1] );
	t.z = ccl::make_float4( (float)matrix[0][2], (float)matrix[1][2], (float)matrix[2][2], (float)matrix[3][2] );
	return t;
}

ccl::Transform setTransform( const Imath::M44f &matrix )
{
	ccl::Transform t;
	t.x = ccl::make_float4( matrix[0][0], matrix[1][0], matrix[2][0], matrix[3][0] );
	t.y = ccl::make_float4( matrix[0][1], matrix[1][1], matrix[2][1], matrix[3][1] );
	t.z = ccl::make_float4( matrix[0][2], matrix[1][2], matrix[2][2], matrix[3][2] );
	return t;
}

Imath::V2f getVector( const ccl::float2 vector )
{
	return Imath::V2f( vector.x, vector.y );
}

Imath::V3f getVector( const ccl::float3 vector )
{
	return Imath::V3f( vector.x, vector.y, vector.z );
}

Imath::Color4f getColor( const ccl::float3 color )
{
	return Imath::Color4f( color.x, color.y, color.z, 1.0f );
}

Imath::Color4f getColor( const ccl::float4 color )
{
	return Imath::Color4f( color.x, color.y, color.z, color.w );
}

Imath::Quatf getQuaternion( const ccl::float4 quat )
{
	return Imath::Quatf( quat.x, quat.y, quat.z, quat.w );
}

Imath::M44f getTransform( const ccl::Transform transform )
{
	return Imath::M44f( 
		transform.x.x, transform.y.x, transform.z.x, 0.0f,
		transform.x.y, transform.y.y, transform.z.y, 0.0f,
		transform.x.z, transform.y.z, transform.z.z, 0.0f,
		transform.x.w, transform.y.w, transform.z.w, 1.0f
		);
}

void setSocket( ccl::Node *node, const ccl::SocketType *socket, const IECore::Data *value )
{
	if( socket == nullptr )
		return;

	switch( socket->type )
	{
		case ccl::SocketType::BOOLEAN:
			convert<BoolData>( node, socket, value );
			break;
		case ccl::SocketType::FLOAT:
			if( const FloatData *data = static_cast<const FloatData *>( value ) )
			{
				node->set( *socket, data->readable() );
			}
			else if( const DoubleData *data = static_cast<const DoubleData *>( value ) )
			{
				node->set( *socket, (float)data->readable() );
			}
			break;
		case ccl::SocketType::INT:
			convert<IntData>( node, socket, value );
			break;
		case ccl::SocketType::UINT:
			convert<UIntData>( node, socket, value );
			break;
		case ccl::SocketType::COLOR:
			if( const Color3fData *data = static_cast<const Color3fData *>( value ) )
			{
				node->set( *socket, setColor( data->readable() ) );
			}
			else if( const Color4fData *data = static_cast<const Color4fData *>( value ) )
			{
				// Dropping alpha
				node->set( *socket, setColor( data->readable() ) );
			}
			break;
		case ccl::SocketType::VECTOR:
		case ccl::SocketType::POINT:
		case ccl::SocketType::NORMAL:
			if( const V3fData *data = static_cast<const V3fData *>( value ) )
			{
				node->set( *socket, setVector( data->readable() ) );
			}
			else if( const V3iData *data = static_cast<const V3iData *>( value ) )
			{
				node->set( *socket, setVector( Imath::V3f( data->readable() ) ) );
			}
			break;
		case ccl::SocketType::POINT2:
			if( const V2fData *data = static_cast<const V2fData *>( value ) )
			{
				node->set( *socket, setVector( data->readable() ) );
			}
			else if( const V2iData *data = static_cast<const V2iData *>( value ) )
			{
				node->set( *socket, setVector( Imath::V2f( data->readable() ) ) );
			}
			break;
		case ccl::SocketType::CLOSURE:
			break;
		case ccl::SocketType::STRING:
			if( const StringData *data = runTimeCast<const StringData>( value ) )
			{
				node->set( *socket, data->readable().c_str() );
			}
			break;
		case ccl::SocketType::ENUM:
			if( const StringData *data = runTimeCast<const StringData>( value ) )
			{
				ccl::ustring enumName( data->readable().c_str() );
				const ccl::NodeEnum &enums = *socket->enum_values;
				if( enums.exists( enumName ) )
				{
					node->set( *socket, enums[enumName] );
				}
			}
			else
			{
				convert<IntData>( node, socket, value );
			}
			break;
		case ccl::SocketType::TRANSFORM:
			if( const M44fData *data = static_cast<const M44fData *>( value ) )
			{
				node->set( *socket, setTransform( data->readable() ) );
			}
			else if( const M44dData *data = static_cast<const M44dData *>( value ) )
			{
				node->set( *socket, setTransform( data->readable() ) );
			}
			break;
		case ccl::SocketType::NODE:
			break;

		// Cycles will 'steal' the ccl::array data and clear it for us
		case ccl::SocketType::BOOLEAN_ARRAY:
			// bools are a special case because of how the STL implements vector<bool>.
			// Since the base for vector<bool> are not actual booleans, we need to manually
			// convert to a ccl::array here.
			if( const BoolVectorData *data = static_cast<const BoolVectorData *>( value ) )
			{
				const vector<bool> &booleans = data->readable();
				vector<bool>::size_type booleansSize = booleans.size();
				ccl::array<bool> array( booleansSize );
				bool *bdata = array.data();
				for(vector<bool>::size_type i = 0; i < booleansSize; ++i){
					*(bdata++) = booleans[i];
				}
				node->set( *socket, array );
			}
			break;
		case ccl::SocketType::FLOAT_ARRAY:
			dataToArray<float, FloatVectorData>( node, socket, value );
			break;
		case ccl::SocketType::INT_ARRAY:
			dataToArray<int, IntVectorData>( node, socket, value );
			break;
		case ccl::SocketType::COLOR_ARRAY:
			dataToArray<ccl::float3, Color3fVectorData>( node, socket, value );
			break;
		case ccl::SocketType::VECTOR_ARRAY:
		case ccl::SocketType::POINT_ARRAY:
		case ccl::SocketType::NORMAL_ARRAY:
			dataToArray<ccl::float3, V3fVectorData>( node, socket, value );
			break;
		case ccl::SocketType::POINT2_ARRAY:
			dataToArray<ccl::float2, V2fVectorData>( node, socket, value );
		case ccl::SocketType::STRING_ARRAY:
			if( const StringVectorData *data = static_cast<const StringVectorData *>( value ) )
			{
				const vector<string> &strings = data->readable();
				auto stringSize = strings.size();
				ccl::array<ccl::ustring> array( stringSize );
				ccl::ustring *sdata = array.data();
				for( size_t i = 0; i < stringSize; ++i)
				{
					*(sdata++) = ccl::ustring( strings[i].c_str() );
				}
				node->set( *socket, array );
			}
			break;
		case ccl::SocketType::TRANSFORM_ARRAY:
			if( const M44dVectorData *data = static_cast<const M44dVectorData *>( value ) )
			{
				const vector<M44d> &matrices = data->readable();
				auto matricesSize = matrices.size();
				ccl::array<ccl::Transform> array( matricesSize );
				ccl::Transform *tdata = array.data();
				for(size_t i = 0; i < matricesSize; ++i)
				{
					auto m = matrices[i];
					*(tdata++) = setTransform( m );
				}
				node->set( *socket, array );
			}
			else if( const M44fVectorData *data = static_cast<const M44fVectorData *>( value ) )
			{
				const vector<M44f> &matrices = data->readable();
				auto matricesSize = matrices.size();
				ccl::array<ccl::Transform> array( matricesSize );
				ccl::Transform *tdata = array.data();
				for(size_t i = 0; i < matricesSize; ++i)
				{
					auto m = matrices[i];
					*(tdata++) = setTransform( m );
				}
				node->set( *socket, array );
			}
			break;
		case ccl::SocketType::NODE_ARRAY:
			break;
		default:
			break;
	}
}

void setSocket( ccl::Node *node, const std::string &name, const IECore::Data *value )
{
	setSocket( node, node->type->find_input( ccl::ustring( name.c_str() ) ), value );
}

void setSockets( ccl::Node *node, const IECore::CompoundDataMap &values )
{
	for( CompoundDataMap::const_iterator it=values.begin(); it!=values.end(); it++ )
	{
		setSocket( node, it->first.value().c_str(), it->second.get() );
	}
}

IECore::DataPtr getSocket( const ccl::Node *node, const ccl::SocketType *socket )
{
	if( socket == nullptr )
		return nullptr;

	switch( socket->type )
	{
		case ccl::SocketType::BOOLEAN:
			return new BoolData( node->get_bool( *socket ) );
		case ccl::SocketType::FLOAT:
			return new FloatData( node->get_float( *socket ) );
		case ccl::SocketType::INT:
			return new IntData( node->get_int( *socket ) );
		case ccl::SocketType::UINT:
			return new UIntData( node->get_uint( *socket ) );
		case ccl::SocketType::COLOR:
		{
			ccl::float3 rgb = node->get_float3( *socket );
			return new Color3fData( Imath::Color3f( rgb.x, rgb.y, rgb.z ) );
		}
		case ccl::SocketType::VECTOR:
		case ccl::SocketType::POINT:
		case ccl::SocketType::NORMAL:
		{
			ccl::float3 vector = node->get_float3( *socket );
			return new V3fData( Imath::V3f( vector.x, vector.y, vector.z ) );
		}
		case ccl::SocketType::POINT2:
		{
			ccl::float2 vector = node->get_float2( *socket );
			return new V2fData( Imath::V2f( vector.x, vector.y ) );
		}
		case ccl::SocketType::CLOSURE:
			return nullptr;
		case ccl::SocketType::STRING:
			return new StringData( string( node->get_string( *socket ).c_str() ) );
		case ccl::SocketType::ENUM:
			return new StringData( string( node->get_string( *socket ).c_str() ) );
		case ccl::SocketType::TRANSFORM:
		{
			return new M44fData( getTransform( node->get_transform( *socket ) ) );
		}
		case ccl::SocketType::NODE:
			return nullptr;

		case ccl::SocketType::BOOLEAN_ARRAY:
			return arrayToData<bool>( node->get_bool_array( *socket ) );
		case ccl::SocketType::FLOAT_ARRAY:
			return arrayToData<float>( node->get_float_array( *socket ) );
		case ccl::SocketType::INT_ARRAY:
			return arrayToData<int>( node->get_int_array( *socket ) );
		case ccl::SocketType::COLOR_ARRAY:
			return arrayToData<Color3f>( node->get_float3_array( *socket ) );
		case ccl::SocketType::VECTOR_ARRAY:
		case ccl::SocketType::POINT_ARRAY:
		case ccl::SocketType::NORMAL_ARRAY:
			return arrayToData<V3f>( node->get_float3_array( *socket ) );
		case ccl::SocketType::POINT2_ARRAY:
		{
			auto &array = node->get_float2_array( *socket );
			auto data = new IECore::TypedData<vector<V2f> >;
			vector<V2f> &v = data->writable();
			v.reserve( array.size() );

			for( size_t i = 0; i < array.size(); ++i )
			{
				v.push_back( V2f( array[i][0], array[i][1]) );
			}
			return data;
		}
		case ccl::SocketType::STRING_ARRAY:
		{
			auto &array = node->get_string_array( *socket );
			auto data = new IECore::TypedData<vector<string> >;
			vector<string> &v = data->writable();
			v.reserve( array.size() );

			for( size_t i = 0; i < array.size(); ++i )
			{
				v.push_back( string( array[i].c_str() ) );
			}
			return data;
		}
		case ccl::SocketType::TRANSFORM_ARRAY:
		{
			auto &array = node->get_transform_array( *socket );
			auto data = new IECore::TypedData<vector<M44f> >;
			vector<M44f> &v = data->writable();
			v.reserve( array.size() );

			for( size_t i = 0; i < array.size(); ++i )
			{
				v.push_back( getTransform( array[i] ) );
			}
			return data;
		}
		case ccl::SocketType::NODE_ARRAY:
			return nullptr;
		default:
			return nullptr;
	}
	return nullptr;
}

IECore::DataPtr getSocket( const ccl::Node *node, const std::string &name )
{
	return getSocket( node, node->type->find_input( ccl::ustring( name.c_str() ) ) );
}

void setRampSocket( ccl::Node *node, const ccl::SocketType *socket, const IECore::Splineff &spline )
{
	ccl::array<float> ramp( RAMP_TABLE_SIZE );
	for (int i = 0; i < RAMP_TABLE_SIZE; i++)
	{
		ramp[i] = spline( (float)i / (float)(RAMP_TABLE_SIZE - 1) );
	}
	node->set( *socket, ramp );
}

void setRampSocket( ccl::Node *node, const ccl::SocketType *socket, const IECore::SplinefColor3f &spline )
{
	ccl::array<ccl::float3> ramp( RAMP_TABLE_SIZE );
	for (int i = 0; i < RAMP_TABLE_SIZE; i++)
	{
		Color3f solve = spline( (float)i / (float)(RAMP_TABLE_SIZE - 1) );
		ramp[i] = ccl::make_float3( solve.x, solve.y, solve.z );
	}
	node->set( *socket, ramp );
}

} // namespace SocketAlgo

} // namespace IECoreCycles
