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

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/VectorTypedData.h"

// Cycles
IECORE_PUSH_DEFAULT_VISIBILITY
#include "kernel/types.h" // for RAMP_TABLE_SIZE
#include "util/transform.h"
#include "util/types.h"
#include "util/vector.h"
IECORE_POP_DEFAULT_VISIBILITY

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreCycles;

namespace
{

template<typename T>
void setNumericSocket( ccl::Node *node, const ccl::SocketType &socket, const IECore::Data *value )
{
	switch( value->typeId() )
	{
		case IECore::BoolDataTypeId :
			node->set( socket, static_cast<T>( static_cast<const BoolData *>( value )->readable() ) );
			break;
		case IECore::FloatDataTypeId :
			node->set( socket, static_cast<T>( static_cast<const FloatData *>( value )->readable() ) );
			break;
		case IECore::DoubleDataTypeId :
			node->set( socket, static_cast<T>( static_cast<const DoubleData *>( value )->readable() ) );
			break;
		case IECore::IntDataTypeId :
			node->set( socket, static_cast<T>( static_cast<const IntData *>( value )->readable() ) );
			break;
		case IECore::UIntDataTypeId :
			node->set( socket, static_cast<T>( static_cast<const UIntData *>( value )->readable() ) );
			break;
		default :
			IECore::msg(
				IECore::Msg::Warning, "Cycles::SocketAlgo",
				boost::format( "Unsupported type `%1%` for socket `%2%` on node `%3%" )
					% value->typeName() % socket.name % node->name
			);
			break;
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

ccl::float2 setVector( const Imath::V2i &vector )
{
	return ccl::make_float2( (float)vector[0], (float)vector[1] );
}

ccl::float3 setVector( const Imath::V3f &vector )
{
	return ccl::make_float3( vector[0], vector[1], vector[2] );
}

ccl::float3 setVector( const Imath::V3i &vector )
{
	return ccl::make_float3( (float)vector[0], (float)vector[1], (float)vector[2] );
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
			setNumericSocket<bool>( node, *socket, value );
			break;
		case ccl::SocketType::FLOAT:
			setNumericSocket<float>( node, *socket, value );
			break;
		case ccl::SocketType::INT:
			setNumericSocket<int>( node, *socket, value );
			break;
		case ccl::SocketType::UINT:
			setNumericSocket<uint>( node, *socket, value );
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
				setNumericSocket<int>( node, *socket, value );
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
			break;
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
	if( auto socket = node->type->find_input( ccl::ustring( name.c_str() ) ) )
	{
		setSocket( node, socket, value );
	}
	else
	{
		IECore::msg(
			IECore::Msg::Warning, "Cycles::SocketAlgo",
			boost::format( "Socket `%1%` on node `%2%` does not exist" ) % name % node->name
		);
	}
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

ccl::ParamValue setParamValue( const IECore::InternedString &name, const IECore::Data *value )
{
	switch( value->typeId() )
	{
		case BoolDataTypeId :
			{
				const BoolData *data = static_cast<const BoolData *>( value );
				float result = static_cast<float>( data->readable() );
				return ccl::ParamValue( name.string(), ccl::TypeDesc::TypeFloat, 1, &result );
			}
			break;
		case IntDataTypeId :
			{
				const IntData *data = static_cast<const IntData *>( value );
				float result = static_cast<float>( data->readable() );
				return ccl::ParamValue( name.string(), ccl::TypeDesc::TypeFloat, 1, &result );
			}
			break;
		case UIntDataTypeId :
			{
				const UIntData *data = static_cast<const UIntData *>( value );
				float result = static_cast<float>( data->readable() );
				return ccl::ParamValue( name.string(), ccl::TypeDesc::TypeFloat, 1, &result );
			}
			break;
		case DoubleDataTypeId :
			{
				const DoubleData *data = static_cast<const DoubleData *>( value );
				float result = static_cast<float>( data->readable() );
				return ccl::ParamValue( name.string(), ccl::TypeDesc::TypeFloat, 1, &result );
			}
			break;
		case FloatDataTypeId :
			{
				const FloatData *data = static_cast<const FloatData *>( value );
				return ccl::ParamValue( name.string(), ccl::TypeDesc::TypeFloat, 1, &data->readable() );
			}
			break;
		case Color3fDataTypeId :
			{
				const Color3fData *data = static_cast<const Color3fData *>( value );
				// Need to pad to float4 to prevent an assert in Cycles debug mode
				const Color3f color = data->readable();
				const ccl::float4 result = ccl::make_float4( color[0], color[1], color[2], 1.0f );
				return ccl::ParamValue( name.string(), ccl::TypeRGBA, 1, &result );
			}
			break;
		case Color4fDataTypeId :
			{
				const Color4fData *data = static_cast<const Color4fData *>( value );
				return ccl::ParamValue( name.string(), ccl::TypeRGBA, 1, data->readable().getValue() );
			}
			break;
		case V2fDataTypeId :
			{
				const V2fData *data = static_cast<const V2fData *>( value );
				return ccl::ParamValue( name.string(), ccl::TypeFloat2, 1, data->readable().getValue() );
			}
			break;
		case V2iDataTypeId :
			{
				const V2iData *data = static_cast<const V2iData *>( value );
				const ccl::float2 result = setVector( data->readable() );
				return ccl::ParamValue( name.string(), ccl::TypeFloat2, 1, &result );
			}
			break;
		case V3fDataTypeId :
			{
				const V3fData *data = static_cast<const V3fData *>( value );
				// Need to pad to float4 to prevent an assert in Cycles debug mode
				const V3f vec = data->readable();
				const ccl::float4 result = ccl::make_float4( vec[0], vec[1], vec[2], 1.0f );
				return ccl::ParamValue( name.string(), ccl::TypeDesc::TypeFloat4, 1, &result );
			}
			break;
		case V3iDataTypeId :
			{
				const V3iData *data = static_cast<const V3iData *>( value );
				// Need to pad to float4 to prevent an assert in Cycles debug mode
				const V3i vec = data->readable();
				const ccl::float4 result = ccl::make_float4( (float)vec[0], (float)vec[1], (float)vec[2], 1.0f );
				return ccl::ParamValue( name.string(), ccl::TypeDesc::TypeFloat4, 1, &result );
			}
			break;
		case QuatfDataTypeId :
			{
				const QuatfData *data = static_cast<const QuatfData *>( value );
				const ccl::float4 result = setQuaternion( data->readable() );
				return ccl::ParamValue( name.string(), ccl::TypeFloat4, 1, &result );
			}
			break;
		case M44fDataTypeId :
			{
				const M44fData *data = static_cast<const M44fData *>( value );
				const ccl::Transform result = setTransform( data->readable() );
				return ccl::ParamValue( name.string(), ccl::TypeDesc::TypeMatrix, 1, &result );
			}
			break;
		case M44dDataTypeId :
			{
				const M44dData *data = static_cast<const M44dData *>( value );
				const ccl::Transform result = setTransform( data->readable() );
				return ccl::ParamValue( name.string(), ccl::TypeDesc::TypeMatrix, 1, &result );
			}
			break;
		default :
			{
				return ccl::ParamValue();
			}
	}
	// A ParamValue that we can test with .data() to see if it's a nullptr.
	return ccl::ParamValue();
}

} // namespace SocketAlgo

} // namespace IECoreCycles
