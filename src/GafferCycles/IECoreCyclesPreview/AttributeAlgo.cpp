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
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "IECore/SimpleTypedData.h"

// Cycles
#include "kernel/types.h"
#include "scene/mesh.h"
#include "util/param.h"
#include "util/types.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

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

template<typename T>
size_t dataSize( const TypedData<std::vector<T>> *data )
{
	return data->readable().size();
}

template<typename T>
size_t dataSize( const TypedData<T> *data )
{
	return 1;
}

template<typename T>
ccl::Attribute *convertTypedPrimitiveVariable( const std::string &name, const PrimitiveVariable &primitiveVariable, ccl::AttributeSet &attributes, ccl::TypeDesc typeDesc, ccl::AttributeElement attributeElement )
{
	// Create attribute. Cycles will allocate a buffer based on `attributeElement` and the information
	// `attributes.geometry` contains.

	ccl::Attribute *attribute = attributes.add( ccl::ustring( name.c_str() ), typeDesc, attributeElement );

	// Sanity check the size of the buffer, so we don't run off the end when copying our data into it.

	const T *data = static_cast<const T *>( primitiveVariable.data.get() );
	const size_t expectedSize = attribute->element_size( attributes.geometry, attributes.prim );
	if( dataSize( data ) != expectedSize )
	{
		msg(
			Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable",
			boost::format( "Primitive variable \"%1%\" has size %2% but Cycles expected size %3%." )
				% name % dataSize( data ) % expectedSize
		);
		return nullptr;
	}

	// Copy data into buffer.

	if constexpr( std::is_same_v<T, V3fVectorData> || std::is_same_v<T, Color3fVectorData> )
	{
		// Special case for arrays of `float3`, where each element actually contains 4 floats for alignment purposes.
		ccl::float3 *f3 = attribute->data_float3();
		for( const auto &v : data->readable() )
		{
			*f3++ = ccl::make_float3( v.x, v.y, v.z );
		}
	}
	else
	{
		// All other cases, (including int to float conversion) are a simple element-by-element copy.
		std::copy( data->baseReadable(), data->baseReadable() + data->baseSize(), attribute->data_float() );
	}

	return attribute;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace IECoreCycles
{

namespace AttributeAlgo
{

void convertPrimitiveVariable( const std::string &name, const IECoreScene::PrimitiveVariable &primitiveVariable, ccl::AttributeSet &attributes, ccl::AttributeElement attributeElement )
{
	ccl::Attribute *attr = nullptr;
	switch( primitiveVariable.data->typeId() )
	{
		// Simple int-based data. Cycles doesn't support int attributes, so we promote to the equivalent float types.

		case IntDataTypeId :
			attr = convertTypedPrimitiveVariable<IntData>( name, primitiveVariable, attributes, ccl::TypeDesc::TypeFloat, attributeElement );
			break;
		case V2iDataTypeId :
			attr = convertTypedPrimitiveVariable<V2iData>( name, primitiveVariable, attributes, ccl::TypeFloat2, attributeElement );
			break;
		case V3iDataTypeId :
			attr = convertTypedPrimitiveVariable<V3iData>(
				name, primitiveVariable, attributes,
				typeFromGeometricDataInterpretation(
					static_cast<const V3iData *>( primitiveVariable.data.get() )->getInterpretation()
				),
				attributeElement
			);
			break;

		// Vectors of int-based data. Cycles doesn't support int attributes, so we promote to the equivalent float types.

		case IntVectorDataTypeId :
			attr = convertTypedPrimitiveVariable<IntVectorData>( name, primitiveVariable, attributes, ccl::TypeDesc::TypeFloat, attributeElement );
			break;
		case V2iVectorDataTypeId :
			attr = convertTypedPrimitiveVariable<V2iVectorData>( name, primitiveVariable, attributes, ccl::TypeFloat2, attributeElement );
			break;
		case V3iVectorDataTypeId :
			attr = convertTypedPrimitiveVariable<V3iVectorData>(
				name, primitiveVariable, attributes,
				typeFromGeometricDataInterpretation(
					static_cast<const V3iVectorData *>( primitiveVariable.data.get() )->getInterpretation()
				),
				attributeElement
			);
			break;

		// Simple float-based data.

		case FloatDataTypeId :
			attr = convertTypedPrimitiveVariable<FloatData>( name, primitiveVariable, attributes, ccl::TypeDesc::TypeFloat, attributeElement );
			break;
		case V2fDataTypeId :
			attr = convertTypedPrimitiveVariable<V2fData>( name, primitiveVariable, attributes, ccl::TypeFloat2, attributeElement );
			break;
		case V3fDataTypeId :
			attr = convertTypedPrimitiveVariable<V3fData>(
				name, primitiveVariable, attributes,
				typeFromGeometricDataInterpretation(
					static_cast<const V3fData *>( primitiveVariable.data.get() )->getInterpretation()
				),
				attributeElement
			);
			break;
		case Color3fDataTypeId :
			attr = convertTypedPrimitiveVariable<Color3fData>( name, primitiveVariable, attributes, ccl::TypeDesc::TypeColor, attributeElement );
			break;

		// Vectors of float-based data.

		case FloatVectorDataTypeId :
			attr = convertTypedPrimitiveVariable<FloatVectorData>( name, primitiveVariable, attributes, ccl::TypeDesc::TypeFloat, attributeElement );
			break;
		case V2fVectorDataTypeId :
			attr = convertTypedPrimitiveVariable<V2fVectorData>( name, primitiveVariable, attributes, ccl::TypeFloat2, attributeElement );
			break;
		case V3fVectorDataTypeId :
			attr = convertTypedPrimitiveVariable<V3fVectorData>(
				name, primitiveVariable, attributes,
				typeFromGeometricDataInterpretation(
					static_cast<const V3fVectorData *>( primitiveVariable.data.get() )->getInterpretation()
				),
				attributeElement
			);
			break;
		case Color3fVectorDataTypeId :
			attr = convertTypedPrimitiveVariable<Color3fVectorData>( name, primitiveVariable, attributes, ccl::TypeDesc::TypeColor, attributeElement );
			break;
		default :
			msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Primitive variable \"%s\" has unsupported type \"%s\"." ) % name % primitiveVariable.data->typeName() );
			return;
	};

	// Tag as a standard attribute if possible. Note that we don't use `AttributeSet::add( AttributeStandard )`
	// because that crashes for certain combinations of geometry type and attribute. But some of those "crashy"
	// combinations are useful - see `RendererTest.testPointsWithNormals` for an example.
	//
	/// \todo Support more standard attributes here. Maybe then the geometry converters could
	/// use `convertPrimitiveVariable()` for most data, instead of having
	/// custom code paths for `P`, `uv` etc?

	if( name == "N" && attr->element == ccl::ATTR_ELEMENT_VERTEX && attr->type == ccl::TypeDesc::TypeNormal )
	{
		attr->std = ccl::ATTR_STD_VERTEX_NORMAL;
	}
}

} // AttributeAlgo

} // IECoreCycles
