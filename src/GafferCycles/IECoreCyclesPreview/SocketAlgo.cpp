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

#include "fmt/format.h"

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
				fmt::format(
					"Unsupported type `{}` for socket `{}` on node `{}`",
					value->typeName(), socket.name, node->name
				)
			);
			break;
	}
}

template<typename T>
void setFloat2Socket( ccl::Node *node, const ccl::SocketType &socket, const T &value )
{
	node->set( socket, ccl::make_float2( value[0], value[1] ) );
}

void setFloat2Socket( ccl::Node *node, const ccl::SocketType &socket, const IECore::Data *value )
{
	switch( value->typeId() )
	{
		case IECore::V2fDataTypeId :
			setFloat2Socket( node, socket, static_cast<const V2fData *>( value )->readable() );
			break;
		case IECore::V2iDataTypeId :
			setFloat2Socket( node, socket, static_cast<const V2iData *>( value )->readable() );
			break;
		default :
			IECore::msg(
				IECore::Msg::Warning, "Cycles::SocketAlgo",
				fmt::format(
					"Unsupported type `{}` for socket `{}` on node `{}`",
					value->typeName(), socket.name, node->name
				)
			);
			break;
	}
}

template<typename T>
void setFloat2ArraySocket( ccl::Node *node, const ccl::SocketType &socket, const T &value )
{
	ccl::array<ccl::float2> array( value.size() );
	for( size_t i = 0; i < value.size(); ++i )
	{
		array[i] = ccl::make_float2( value[i][0], value[i][1] );
	}
	node->set( socket, array );
}

void setFloat2ArraySocket( ccl::Node *node, const ccl::SocketType &socket, const IECore::Data *value )
{
	switch( value->typeId() )
	{
		case IECore::V2fVectorDataTypeId :
			setFloat2ArraySocket( node, socket, static_cast<const V2fVectorData *>( value )->readable() );
			break;
		case IECore::V2iVectorDataTypeId :
			setFloat2ArraySocket( node, socket, static_cast<const V2iVectorData *>( value )->readable() );
			break;
		default :
			IECore::msg(
				IECore::Msg::Warning, "Cycles::SocketAlgo",
				fmt::format(
					"Unsupported type `{}` for socket `{}` on node `{}`",
					value->typeName(), socket.name, node->name
				)
			);
			break;
	}
}

template<typename T>
void setFloat3Socket( ccl::Node *node, const ccl::SocketType &socket, const T &value )
{
	node->set( socket, ccl::make_float3( value[0], value[1], value[2] ) );
}

void setFloat3Socket( ccl::Node *node, const ccl::SocketType &socket, const IECore::Data *value )
{
	switch( value->typeId() )
	{
		case IECore::Color3fDataTypeId :
			setFloat3Socket( node, socket, static_cast<const Color3fData *>( value )->readable() );
			break;
		case IECore::Color4fDataTypeId :
			// Omitting alpha
			setFloat3Socket( node, socket, static_cast<const Color4fData *>( value )->readable() );
			break;
		case IECore::V3fDataTypeId :
			setFloat3Socket( node, socket, static_cast<const V3fData *>( value )->readable() );
			break;
		case IECore::V3iDataTypeId :
			setFloat3Socket( node, socket, static_cast<const V3iData *>( value )->readable() );
			break;
		default :
			IECore::msg(
				IECore::Msg::Warning, "Cycles::SocketAlgo",
				fmt::format(
					"Unsupported type `{}` for socket `{}` on node `{}`",
					value->typeName(), socket.name, node->name
				)
			);
			break;
	}
}

template<typename T>
void setFloat3ArraySocket( ccl::Node *node, const ccl::SocketType &socket, const T &value )
{
	ccl::array<ccl::float3> array( value.size() );
	for( size_t i = 0; i < value.size(); ++i )
	{
		array[i] = ccl::make_float3( value[i][0], value[i][1], value[i][2] );
	}
	node->set( socket, array );
}

void setFloat3ArraySocket( ccl::Node *node, const ccl::SocketType &socket, const IECore::Data *value )
{
	switch( value->typeId() )
	{
		case IECore::Color3fVectorDataTypeId :
			setFloat3ArraySocket( node, socket, static_cast<const Color3fVectorData *>( value )->readable() );
			break;
		case IECore::Color4fVectorDataTypeId :
			// Omitting alpha
			setFloat3ArraySocket( node, socket, static_cast<const Color4fVectorData *>( value )->readable() );
			break;
		case IECore::V3fVectorDataTypeId :
			setFloat3ArraySocket( node, socket, static_cast<const V3fVectorData *>( value )->readable() );
			break;
		case IECore::V3iVectorDataTypeId :
			setFloat3ArraySocket( node, socket, static_cast<const V3iVectorData *>( value )->readable() );
			break;
		default :
			IECore::msg(
				IECore::Msg::Warning, "Cycles::SocketAlgo",
				fmt::format(
					"Unsupported type `{}` for socket `{}` on node `{}`",
					value->typeName(), socket.name, node->name
				)
			);
			break;
	}
}

template<typename T, typename DataType = IECore::TypedData<vector<T>>>
void setArraySocket( ccl::Node *node, const ccl::SocketType &socket, const Data *value )
{
	if( auto data = runTimeCast<const DataType>( value ) )
	{
		ccl::array<T> array( data->readable().size() );
		std::copy( data->readable().begin(), data->readable().end(), array.data() );
		node->set( socket, array );
	}
	else
	{
		IECore::msg(
			IECore::Msg::Warning, "Cycles::SocketAlgo::setSocket",
			fmt::format(
				"Unsupported data type `{}` for socket `{}` on node `{}`",
				value->typeName(), socket.name, node->name
			)
		);
	}
}

void setEnumSocket( ccl::Node *node, const ccl::SocketType &socket, const IECore::Data *value )
{
	const char *name = nullptr;
	if( auto data = runTimeCast<const StringData>( value ) )
	{
		name = data->readable().c_str();
	}
	else if( auto internedData = runTimeCast<const InternedStringData>( value ) )
	{
		name = internedData->readable().c_str();
	}

	if( name )
	{
		ccl::ustring uName( name );
		const ccl::NodeEnum &enums = *socket.enum_values;
		if( enums.exists( uName ) )
		{
			node->set( socket, enums[uName] );
		}
		else
		{
			IECore::msg(
				IECore::Msg::Warning, "Cycles::SocketAlgo",
				fmt::format(
					"Invalid enum value \"{}\" for socket `{}` on node `{}`",
					name, socket.name, node->name
				)
			);
		}
	}
	else
	{
		setNumericSocket<int>( node, socket, value );
	}
}

void setStringSocket( ccl::Node *node, const ccl::SocketType &socket, const IECore::Data *value )
{
	if( auto data = runTimeCast<const StringData>( value ) )
	{
		node->set( socket, data->readable().c_str() );
	}
	else if( auto internedData = runTimeCast<const InternedStringData>( value ) )
	{
		node->set( socket, internedData->readable().c_str() );
	}
	else
	{
		IECore::msg(
			IECore::Msg::Warning, "Cycles::SocketAlgo",
			fmt::format(
				"Unsupported data type `{}` for socket `{}` on node `{}` (expected StringData or InternedStringData).",
				value->typeName(), socket.name, node->name
			)
		);
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

	if( !value )
	{
		node->set_default_value( *socket );
		return;
	}

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
			setNumericSocket<ccl::uint>( node, *socket, value );
			break;
		case ccl::SocketType::COLOR:
		case ccl::SocketType::VECTOR:
		case ccl::SocketType::POINT:
		case ccl::SocketType::NORMAL:
			setFloat3Socket( node, *socket, value );
			break;
		case ccl::SocketType::POINT2:
			setFloat2Socket( node, *socket, value );
			break;
		case ccl::SocketType::CLOSURE:
			break;
		case ccl::SocketType::STRING:
			setStringSocket( node, *socket, value );
			break;
		case ccl::SocketType::ENUM:
			setEnumSocket( node, *socket, value );
			break;
		case ccl::SocketType::BOOLEAN_ARRAY:
			setArraySocket<bool>( node, *socket, value );
			break;
		case ccl::SocketType::FLOAT_ARRAY:
			setArraySocket<float>( node, *socket, value );
			break;
		case ccl::SocketType::INT_ARRAY:
			setArraySocket<int>( node, *socket, value );
			break;
		case ccl::SocketType::COLOR_ARRAY:
		case ccl::SocketType::VECTOR_ARRAY:
		case ccl::SocketType::POINT_ARRAY:
		case ccl::SocketType::NORMAL_ARRAY:
			setFloat3ArraySocket( node, *socket, value );
			break;
		case ccl::SocketType::POINT2_ARRAY:
			setFloat2ArraySocket( node, *socket, value );
			break;
		case ccl::SocketType::STRING_ARRAY:
			setArraySocket<ccl::ustring, StringVectorData>( node, *socket, value );
			break;
		default:
			IECore::msg(
				IECore::Msg::Warning, "Cycles::SocketAlgo",
				fmt::format(
					"Unsupported socket type `{}` for socket `{}` on node `{}`.",
					ccl::SocketType::type_name( socket->type ), socket->name, node->name
				)
			);
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
			fmt::format( "Socket `{}` on node `{}` does not exist", name, node->name )
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
				// A ParamValue that we can test with .data() to see if it's a nullptr.
				return ccl::ParamValue();
			}
	}
}

IECore::DataPtr getSocket( const ccl::Node *node, const ccl::SocketType *socket )
{
	switch( socket->type )
	{
		case ccl::SocketType::BOOLEAN :
			return new BoolData( node->get_bool( *socket ) );
		case ccl::SocketType::INT :
			return new IntData( node->get_int( *socket ) );
		case ccl::SocketType::FLOAT :
			return new FloatData( node->get_float( *socket ) );
		case ccl::SocketType::ENUM :
			return new StringData( node->get_string( *socket ).string() );
		default :
			IECore::msg(
				IECore::Msg::Warning, "Cycles::SocketAlgo::getSocket",
				fmt::format(
					"Unsupported socket type `{}` for socket `{}` on node `{}`.",
					ccl::SocketType::type_name( socket->type ), socket->name, node->name
				)
			);
	}
	return nullptr;
}

IECore::CompoundDataPtr getSockets( const ccl::Node *node )
{
	IECore::CompoundDataPtr result = new IECore::CompoundData;
	for( const ccl::SocketType &socket : node->type->inputs )
	{
		if( DataPtr d = getSocket( node, &socket ) )
		{
			result->writable()[socket.name.c_str()] = d;
		}
	}
	return result;
}

} // namespace SocketAlgo

} // namespace IECoreCycles
