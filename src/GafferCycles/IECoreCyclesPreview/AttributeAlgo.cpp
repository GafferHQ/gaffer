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
			return ccl::TypeDesc::TypeFloat;
		case Color3fVectorDataTypeId :
		case Color4fVectorDataTypeId :
			return ccl::TypeDesc::TypeColor;
		case V2fVectorDataTypeId :
		case V2iVectorDataTypeId :
		case V3fVectorDataTypeId :
		case V3iVectorDataTypeId :
			return ccl::TypeDesc::TypeVector;
		case M44fVectorDataTypeId :
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
	ccl::TypeDesc ctype = typeDesc( primitiveVariable.data.get()->typeId() );
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
		bool isUV = false;
		switch( primitiveVariable.interpolation )
		{
			case PrimitiveVariable::Constant :
				celem = ccl::ATTR_ELEMENT_MESH;
				break;
			case PrimitiveVariable::Vertex :
				if( attributes.curve_mesh )
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

	if( ctype == ccl::TypeDesc::TypeFloat )
	{
		const FloatVectorData *data = runTimeCast<const FloatVectorData>( primitiveVariable.data.get() );
		if( data )
		{
			const std::vector<float> &floatData = data->readable();

			size_t num = floatData.size();
			float *cdata = attr->data_float();

			if( !cdata )
			{
				msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected FloatVectorData)." ) % name % primitiveVariable.data->typeName() );
				attributes.remove( attr );
			}

			for( size_t i = 0; i < num; ++i )
				*(cdata++) = floatData[i];
			cdata = attr->data_float();
		}
		else
		{
			msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected FloatVectorData)." ) % name % primitiveVariable.data->typeName() );
			attributes.remove( attr );
		}
	}
	else
	{
		const V3fVectorData *data = runTimeCast<const V3fVectorData>( primitiveVariable.data.get() );
		if( data )
		{
			const std::vector<V3f> &v3fData = data->readable();
			size_t num = v3fData.size();
			ccl::float3 *cdata = attr->data_float3();

			if( !cdata )
			{
				msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected V3fVectorData)." ) % name % primitiveVariable.data->typeName() );
				attributes.remove( attr );
			}

			for( size_t i = 0; i < num; ++i )
				*(cdata++) = ccl::make_float3( v3fData[i].x, v3fData[i].y, v3fData[i].z );
			cdata = attr->data_float3();
		}
		else
		{
			msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected V3fVectorData)." ) % name % primitiveVariable.data->typeName() );
			attributes.remove( attr );
		}
	}
}

} // AttributeAlgo

} // IECoreCycles
