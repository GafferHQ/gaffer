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

#include "GafferCycles/IECoreCyclesPreview/MeshAlgo.h"

#include "GafferCycles/IECoreCyclesPreview/ObjectAlgo.h"

#include "IECoreScene/MeshPrimitive.h"

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

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

void AttributeAlgo::convertPrimitiveVariable( const char *name, const IECoreScene::PrimitiveVariable &primitiveVariable, ccl::AttributeSet &attributes )
{
	// Work out what kind of attribute it needs to be
	const VectorData *data = primitiveVariable.data.get();
	GeometricData::Interpretation interp = data->getInterpretation();
	ccl::Attribute *attr = nullptr;
	bool exists = false;
	if( name == "N" )
	{
		attr = attributes.find( ccl::ATTR_STD_VERTEX_NORMAL );
		if(!attr)
			attr = attributes.add( ccl::ATTR_STD_VERTEX_NORMAL, ccl::ustring(name) );
		else
			exists = true;
	}
	else if( name == "uv" )
	{
		attr = attributes.find( ccl::ATTR_STD_UV );
		if(!attr)
			attr = attributes.add( ccl::ATTR_STD_UV, ccl::ustring(name) );
		else
			exists = true;
	}
	else if( name == "uTangent" )
	{
		attr = attributes.find( ccl::ATTR_STD_UV_TANGENT );
		if(!attr)
			attr = attributes.add( ccl::ATTR_STD_UV_TANGENT, ccl::ustring(name) );
		else
			exists = true;
	}
	else
	{
		ccl::TypeDesc ctype = ccl::TypeDesc::TypePoint;
		ccl::AttributeElement celem = ccl::ATTR_ELEMENT_NONE;
		bool isUV = false;
		switch( interp )
		{
			case GeometricData::Numeric:
				ctype = ccl::TypeDesc::TypeFloat;
				break;
			case GeometricData::Point :
				ctype = ccl::TypeDesc::TypePoint;
				break;
			case GeometricData::Normal :
				ctype = ccl::TypeDesc::TypeNormal;
				break;
			case GeometricData::Vector :
				ctype = ccl::TypeDesc::TypeVector;
				break;
			case GeometricData::Color :
				ctype = ccl::TypeDesc::TypeColor;
				break;
			case GeometricData::UV :
				ctype = ccl::TypeDesc::TypePoint;
				break;
			default :
				break;
		}
		switch( primitiveVariable.interpolation )
		{
			case PrimitiveVariable::Constant :
				celem = ccl::ATTR_ELEMENT_MESH;
				break;
			case PrimitiveVariable::Vertex :
				celem = ccl::ATTR_ELEMENT_VERTEX;
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
		attr = attributes.find( ccl::ustring(name) );
		if( !attr )
			attr = attributes.add( ccl::ustring(name), ctype, celem );
		else
			exists = true;
	}

	if( interp == GeometricData::Numeric )
	{
		const FloatVectorData *data = runTimeCast<const FloatVectorData>( value.data.get() );
		if( data )
		{
			const std::vector<float> &floatData = data->readable();

			size_t num = floatData->readable().size();
			float *cdata = attr->data_float();

			for( size_t i = 0; i < num; ++i, ++cdata )
				*cdata = attr->make_float( floatData[i] );
			cdata = attr->data_float();
		}
		else
		{
			msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected FloatVectorData)." ) % name % value.data->typeName() );
			attributes.remove( attr );
		}
	}
	else
	{
		const V3fVectorData *data = runTimeCast<const V3fVectorData>( value.data.get() );
		if( data )
		{
			const std::vector<V3f> &v3fData = data->readable();
			size_t num = v3fData->readable().size();
			ccl::float3 *cdata = attr->data_float3();

			for( size_t i = 0; i < num; ++i, ++cdata )
				*cdata = ccl::make_float3( v3fData[i].x, v3fData[i].y, v3fData[i].z );
			cdata = attr->data_float3();
		}
		else
		{
			msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected V3fVectorData)." ) % name % value.data->typeName() );
			attributes.remove( attr );
		}
	}
}
