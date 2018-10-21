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
#include "util/util_transform.h"
#include "util/util_types.h"
#include "util/util_vector.h"

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

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

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
			if( const DoubleData *data = static_cast<const DoubleData *>( value ) )
			{
				node->set( *socket, (float)data->readable() );
			}
			else if( const FloatData *data = static_cast<const FloatData *>( value ) )
			{
				node->set( *socket, data->readable() );
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
				const Imath::Color3f &c = data->readable();
				node->set( *socket, ccl::make_float3( c[0], c[1], c[2] ) );
			}
			else if( const Color4fData *data = static_cast<const Color4fData *>( value ) )
			{
				// Dropping alpha
				const Imath::Color4f &c = data->readable();
				node->set( *socket, ccl::make_float3( c[0], c[1], c[2] ) );
			}
			break;
		case ccl::SocketType::VECTOR:
		case ccl::SocketType::POINT:
		case ccl::SocketType::NORMAL:
			if( const V3iData *data = static_cast<const V3iData *>( value ) )
			{
				const Imath::V3f &v = Imath::V3f( data->readable() );
				node->set( *socket, ccl::make_float3( v.x, v.y, v.z ) );
			}
			else if( const V3fData *data = static_cast<const V3fData *>( value ) )
			{
				const Imath::V3f &v = data->readable();
				node->set( *socket, ccl::make_float3( v.x, v.y, v.z ) );
			}
			break;
		case ccl::SocketType::POINT2:
			if( const V2iData *data = static_cast<const V2iData *>( value ) )
			{
				const Imath::V2f &v = Imath::V2f( data->readable() );
				node->set( *socket, ccl::make_float2( v.x, v.y ) );
			}
			else if( const V2fData *data = static_cast<const V2fData *>( value ) )
			{
				const Imath::V2f &v = data->readable();
				node->set( *socket, ccl::make_float2( v.x, v.y ) );
			}
			break;
		case ccl::SocketType::CLOSURE:
			break;
		case ccl::SocketType::STRING:
			if( const StringData *data = static_cast<const StringData *>( value ) )
			{
				node->set( *socket, data->readable().c_str() );
			}
			break;
		case ccl::SocketType::ENUM:
			convert<IntData>( node, socket, value );
			break;
		case ccl::SocketType::TRANSFORM:
			if( const M44dData *data = static_cast<const M44dData *>( value ) )
			{
				const Imath::M44d &m = data->readable();
				ccl::Transform t;
				t.x = ccl::make_float4((float)m[0][0], (float)m[0][1], (float)m[0][2], (float)m[0][3]);
				t.y = ccl::make_float4((float)m[1][0], (float)m[1][1], (float)m[1][2], (float)m[1][3]);
				t.z = ccl::make_float4((float)m[2][0], (float)m[2][1], (float)m[2][2], (float)m[2][3]);
				node->set( *socket, t );
			}
			else if( const M44fData *data = static_cast<const M44fData *>( value ) )
			{
				const Imath::M44f &m = data->readable();
				ccl::Transform t;
				t.x = ccl::make_float4(m[0][0], m[0][1], m[0][2], m[0][3]);
				t.y = ccl::make_float4(m[1][0], m[1][1], m[1][2], m[1][3]);
				t.z = ccl::make_float4(m[2][0], m[2][1], m[2][2], m[2][3]);
				node->set( *socket, t );
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
				for(int i = 0; i < stringSize; ++i)
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
				for(int i = 0; i < matricesSize; ++i)
				{
					auto m = matrices[i];
					ccl::Transform t;
					t.x = ccl::make_float4((float)m[0][0], (float)m[0][1], (float)m[0][2], (float)m[0][3]);
					t.y = ccl::make_float4((float)m[1][0], (float)m[1][1], (float)m[1][2], (float)m[1][3]);
					t.z = ccl::make_float4((float)m[2][0], (float)m[2][1], (float)m[2][2], (float)m[2][3]);
					*(tdata++) = t;
				}
				node->set( *socket, array );
			}
			else if( const M44fVectorData *data = static_cast<const M44fVectorData *>( value ) )
			{
				const vector<M44f> &matrices = data->readable();
				auto matricesSize = matrices.size();
				ccl::array<ccl::Transform> array( matricesSize );
				ccl::Transform *tdata = array.data();
				for(int i = 0; i < matricesSize; ++i)
				{
					auto m = matrices[i];
					ccl::Transform t;
					t.x = ccl::make_float4(m[0][0], m[0][1], m[0][2], m[0][3]);
					t.y = ccl::make_float4(m[1][0], m[1][1], m[1][2], m[1][3]);
					t.z = ccl::make_float4(m[2][0], m[2][1], m[2][2], m[2][3]);
					*(tdata++) = t;
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
			return new IntData( node->get_int( *socket ) );
		case ccl::SocketType::TRANSFORM:
		{
			ccl::Transform t = node->get_transform( *socket );
			return new M44fData( Imath::M44f( 
				t.x.x, t.x.y, t.x.z, t.x.w,
				t.y.x, t.y.y, t.y.z, t.y.w,
				t.z.x, t.z.y, t.z.z, t.z.w,
				0.0f,  0.0f,  0.0f,  1.0f ) );
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
				auto t = array[i];
				v.push_back( Imath::M44f( 
					t.x.x, t.x.y, t.x.z, t.x.w,
					t.y.x, t.y.y, t.y.z, t.y.w,
					t.z.x, t.z.y, t.z.z, t.z.w,
					0.0f,  0.0f,  0.0f,  1.0f ) );
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
