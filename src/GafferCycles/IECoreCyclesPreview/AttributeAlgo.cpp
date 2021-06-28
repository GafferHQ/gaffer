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

#include "GafferCycles/IECoreCyclesPreview/AttributeAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/ObjectAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "IECore/SimpleTypedData.h"

// Cycles
#include "kernel/kernel_types.h"
#include "render/mesh.h"
#include "util/util_param.h"
#include "util/util_types.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{
} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace IECoreCycles

{

namespace AttributeAlgo

{

ccl::TypeDesc typeDesc( IECore::TypeId dataType )
{
	switch( dataType )
	{
		case FloatVectorDataTypeId :
		case IntVectorDataTypeId :
		case IntDataTypeId:
			return ccl::TypeDesc::TypeFloat;
		case Color3fVectorDataTypeId :
		case Color4fVectorDataTypeId :
			return ccl::TypeDesc::TypeColor;
		case V2fVectorDataTypeId :
		case V2iVectorDataTypeId :
			return ccl::TypeFloat2;
		case V3fVectorDataTypeId :
		case V3iVectorDataTypeId :
			return ccl::TypeDesc::TypeVector;
		case M44fVectorDataTypeId :
		case M44fDataTypeId :
			return ccl::TypeDesc::TypeMatrix;
		default :
			return ccl::TypeDesc::TypeVector;
	}
}

ccl::TypeDesc typeFromGeometricDataInterpretation( IECore::GeometricData::Interpretation dataType )
{
	switch( dataType )
	{
		case GeometricData::Numeric :
			return ccl::TypeDesc::TypeVector;
		case GeometricData::Point :
			return ccl::TypeDesc::TypePoint;
		case GeometricData::Normal :
			return ccl::TypeDesc::TypeNormal;
		case GeometricData::Vector :
			return ccl::TypeDesc::TypeVector;
		case GeometricData::Color :
			return ccl::TypeDesc::TypeColor;
		case GeometricData::UV :
			return ccl::TypeDesc::TypePoint;
		default :
			return ccl::TypeDesc::TypeVector;
	}
}

void convertPrimitiveVariable( const std::string &name, const IECoreScene::PrimitiveVariable &primitiveVariable, ccl::AttributeSet &attributes )
{
	IECore::TypeId dataType = primitiveVariable.data.get()->typeId();
	if( dataType == StringDataTypeId )
	{
		//msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\"." ) % name % primitiveVariable.data->typeName() );
		return;
	}
	ccl::TypeDesc ctype = typeDesc( dataType );
	ccl::Attribute *attr = nullptr;
	bool exists = false;
	if( name == "N" )
	{
		attr = attributes.find( ccl::ATTR_STD_VERTEX_NORMAL );
		if(!attr)
			attr = attributes.add( ccl::ATTR_STD_VERTEX_NORMAL, ccl::ustring(name.c_str()) );
		else
			exists = true;
	}
	else if( name == "uv" )
	{
		attr = attributes.find( ccl::ATTR_STD_UV );
		if(!attr)
			attr = attributes.add( ccl::ATTR_STD_UV, ccl::ustring(name.c_str()) );
		else
			exists = true;
	}
	else if( name == "uTangent" )
	{
		attr = attributes.find( ccl::ATTR_STD_UV_TANGENT );
		if(!attr)
			attr = attributes.add( ccl::ATTR_STD_UV_TANGENT, ccl::ustring(name.c_str()) );
		else
			exists = true;
	}
	else
	{
		if( ctype != ccl::TypeDesc::TypeFloat )
		{
			// We need to determine what kind of vector it is
			const V3fVectorData *data = runTimeCast<const V3fVectorData>( primitiveVariable.data.get() );
			if( data )
				ctype = typeFromGeometricDataInterpretation( data->getInterpretation() );
		}
		ccl::AttributeElement celem = ccl::ATTR_ELEMENT_NONE;
		switch( primitiveVariable.interpolation )
		{
			case PrimitiveVariable::Constant :
				celem = ccl::ATTR_ELEMENT_MESH;
				break;
			case PrimitiveVariable::Vertex :
				if( attributes.geometry->geometry_type == ccl::Geometry::HAIR )
				{
					celem = ccl::ATTR_ELEMENT_CURVE_KEY;
				}
				else
				{
					celem = ccl::ATTR_ELEMENT_VERTEX;
				}
				break;
			case PrimitiveVariable::Varying :
			case PrimitiveVariable::FaceVarying :
				celem = ccl::ATTR_ELEMENT_CORNER;
				break;
			case PrimitiveVariable::Uniform :
				celem = ccl::ATTR_ELEMENT_FACE;
				break;
			default :
				break;
		}
		attr = attributes.find( ccl::ustring(name.c_str()) );
		if( !attr )
			attr = attributes.add( ccl::ustring(name.c_str()), ctype, celem );
		else
			exists = true;
	}

	if( primitiveVariable.interpolation != PrimitiveVariable::Constant && ctype == ccl::TypeDesc::TypeFloat )
	{
		if( const FloatVectorData *data = runTimeCast<const FloatVectorData>( primitiveVariable.data.get() ) )
		{
			const std::vector<float> &floatData = data->readable();

			size_t num = floatData.size();
			float *cdata = attr->data_float();

			if( cdata )
			{
				for( size_t i = 0; i < num; ++i )
					*(cdata++) = floatData[i];
				cdata = attr->data_float();
				return;
			}
		}

		if( const IntVectorData *data = runTimeCast<const IntVectorData>( primitiveVariable.data.get() ) )
		{
			const std::vector<int> &intData = data->readable();

			size_t num = intData.size();
			float *cdata = attr->data_float();

			if( cdata )
			{
				for( size_t i = 0; i < num; ++i )
					*(cdata++) = (float)intData[i];
				cdata = attr->data_float();
				return;
			}
		}

		msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected FloatVectorData or IntVectorData)." ) % name % primitiveVariable.data->typeName() );
		attributes.remove( attr );
		return;
	}
	else if( primitiveVariable.interpolation != PrimitiveVariable::Constant )
	{
		if( const V3fVectorData *data = runTimeCast<const V3fVectorData>( primitiveVariable.data.get() ) )
		{
			const std::vector<V3f> &v3fData = data->readable();
			size_t num = v3fData.size();
			ccl::float3 *cdata = attr->data_float3();

			if( cdata )
			{
				for( size_t i = 0; i < num; ++i )
					*(cdata++) = ccl::make_float3( v3fData[i].x, v3fData[i].y, v3fData[i].z );
				cdata = attr->data_float3();
				return;
			}
		}

		if( const V3iVectorData *data = runTimeCast<const V3iVectorData>( primitiveVariable.data.get() ) )
		{
			const std::vector<V3i> &v3iData = data->readable();
			size_t num = v3iData.size();
			ccl::float3 *cdata = attr->data_float3();

			if( cdata )
			{
				for( size_t i = 0; i < num; ++i )
					*(cdata++) = ccl::make_float3( (float)v3iData[i].x, (float)v3iData[i].y, (float)v3iData[i].z );
				cdata = attr->data_float3();
				return;
			}
		}

		if( const V2fVectorData *data = runTimeCast<const V2fVectorData>( primitiveVariable.data.get() ) )
		{
			const std::vector<V2f> &v2fData = data->readable();
			size_t num = v2fData.size();
			ccl::float2 *cdata = attr->data_float2();

			if( cdata )
			{
				for( size_t i = 0; i < num; ++i )
					*(cdata++) = ccl::make_float2( v2fData[i].x, v2fData[i].y );
				cdata = attr->data_float2();
				return;
			}
		}

		if( const V2iVectorData *data = runTimeCast<const V2iVectorData>( primitiveVariable.data.get() ) )
		{
			const std::vector<V2i> &v2iData = data->readable();
			size_t num = v2iData.size();
			ccl::float2 *cdata = attr->data_float2();

			if( cdata )
			{
				for( size_t i = 0; i < num; ++i )
					*(cdata++) = ccl::make_float2( (float)v2iData[i].x, (float)v2iData[i].y );
				cdata = attr->data_float2();
				return;
			}
		}

		if( const Color3fVectorData *data = runTimeCast<const Color3fVectorData>( primitiveVariable.data.get() ) )
		{
			const std::vector<Color3f> &colorData = data->readable();
			size_t num = colorData.size();
			ccl::float3 *cdata = attr->data_float3();

			if( cdata )
			{
				for( size_t i = 0; i < num; ++i )
					*(cdata++) = ccl::make_float3( colorData[i].x, colorData[i].y, colorData[i].z );
				cdata = attr->data_float3();
				return;
			}
		}

		msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected V3fVectorData, Color3fVectorData or V2fVectorData)." ) % name % primitiveVariable.data->typeName() );
		attributes.remove( attr );
		return;
	}
	else if( primitiveVariable.interpolation == PrimitiveVariable::Constant )
	{
		if( const FloatData *data = runTimeCast<const FloatData>( primitiveVariable.data.get() ) )
		{
			const float &floatData = data->readable();
			float *cdata = attr->data_float();

			if( cdata )
			{
				*(cdata) = floatData;
				return;
			}
		}

		if( const IntData *data = runTimeCast<const IntData>( primitiveVariable.data.get() ) )
		{
			const int &intData = data->readable();
			float *cdata = attr->data_float();

			if( cdata )
			{
				*(cdata) = (float)intData;
				return;
			}
		}

		if( const V2fData *data = runTimeCast<const V2fData>( primitiveVariable.data.get() ) )
		{
			const Imath::V2f &v2fData = data->readable();
			ccl::float2 *cdata = attr->data_float2();

			if( cdata )
			{
				*(cdata) = ccl::make_float2( v2fData.x, v2fData.y );
				return;
			}
		}

		if( const V2iData *data = runTimeCast<const V2iData>( primitiveVariable.data.get() ) )
		{
			const Imath::V2i &v2iData = data->readable();
			ccl::float2 *cdata = attr->data_float2();

			if( cdata )
			{
				*(cdata) = ccl::make_float2( (float)v2iData.x, (float)v2iData.y );
				return;
			}
		}

		if( const V3fData *data = runTimeCast<const V3fData>( primitiveVariable.data.get() ) )
		{
			const Imath::V3f &v3fData = data->readable();
			ccl::float3 *cdata = attr->data_float3();

			if( cdata )
			{
				*(cdata) = SocketAlgo::setVector( v3fData );
				return;
			}
		}

		if( const V3iData *data = runTimeCast<const V3iData>( primitiveVariable.data.get() ) )
		{
			const Imath::V3i &v3iData = data->readable();
			ccl::float3 *cdata = attr->data_float3();

			if( cdata )
			{
				*(cdata) = ccl::make_float3( (float)v3iData.x, (float)v3iData.y, (float)v3iData.z );
				return;
			}
		}

		if( const Color3fData *data = runTimeCast<const Color3fData>( primitiveVariable.data.get() ) )
		{
			const Imath::Color3f &colorData = data->readable();
			ccl::float3 *cdata = attr->data_float3();

			if( cdata )
			{
				*(cdata) = SocketAlgo::setColor( colorData );
				return;
			}
		}

		if( const M44fData *data = runTimeCast<const M44fData>( primitiveVariable.data.get() ) )
		{
			const Imath::M44f &m44fData = data->readable();
			ccl::Transform *cdata = attr->data_transform();

			if( cdata )
			{
				*(cdata) = SocketAlgo::setTransform( m44fData );
				return;
			}
		}

		msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected FloatData, IntData, V3fData, Color3fData or M44fData)." ) % name % primitiveVariable.data->typeName() );
		attributes.remove( attr );
		return;
	}
}

} // AttributeAlgo

} // IECoreCycles
