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

#include "GafferCycles/IECoreCyclesPreview/ObjectAlgo.h"

#include "IECore/MessageHandler.h"

#include <unordered_map>

// Cycles (for ustring)
#include "util/util_param.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace std
{

/// \todo Move to IECore/TypeIds.h
template<>
struct hash<IECore::TypeId>
{
	size_t operator()( IECore::TypeId typeId ) const
	{
		return hash<size_t>()( typeId );
	}
};

} // namespace std

namespace
{

using namespace IECoreCycles;

struct Converters
{

	ObjectAlgo::Converter converter;
	ObjectAlgo::MotionConverter motionConverter;

};

typedef std::unordered_map<IECore::TypeId, Converters> Registry;

Registry &registry()
{
	static Registry r;
	return r;
}

void convertPrimitiveVariable( std::string &name, const IECoreScene::PrimitiveVariable &value, ccl::AttributeSet &attributes )
{
	// Work out what kind of attribute it needs to be
	const VectorData *data = value.data.get();
	ccl::Attribute *attr = nullptr;
	bool exists = false;
	if( name == "N" )
	{
		attr = attributes.find( ccl::ATTR_STD_VERTEX_NORMAL );
		if(!attr)
			attr = attributes.add( ccl::ATTR_STD_VERTEX_NORMAL, name.c_str() );
		else
			exists = true;
	}
	else if( name == "uv" )
	{
		attr = attributes.find( ccl::ATTR_STD_UV );
		if(!attr)
			attr = attributes.add( ccl::ATTR_STD_UV, name.c_str() );
		else
			exists = true;
	}
	else if( name == "uTangent" )
	{
		attr = attributes.find( ccl::ATTR_STD_UV_TANGENT );
		if(!attr)
			attr = attributes.add( ccl::ATTR_STD_UV_TANGENT, name.c_str() );
		else
			exists = true;
	}
	else
	{
		GeometricData::Interpretation interp = data->getInterpretation();
		TypeDesc ctype = TypeDesc::TypePoint;
		ccl::AttributeElement celem = ccl::ATTR_ELEMENT_NONE;
		bool isUV = false;
		switch( interp )
		{
			case GeometricData::Numeric:
				type = TypeDesc::TypeFloat;
				break;
			case GeometricData::Point :
				type = TypeDesc::TypePoint;
				break;
			case GeometricData::Normal :
				type = TypeDesc::TypeNormal;
				break;
			case GeometricData::Vector :
				type = TypeDesc::TypeVector;
				break;
			case GeometricData::Color :
				type = TypeDesc::TypeColor;
				break;
			case GeometricData::UV :
				type = TypeDesc::TypePoint;
				break;
			default :
				break;
		}
		switch( value.interpolation )
		{
			case PrimitiveVariable::Constant :
				elem = ATTR_ELEMENT_MESH;
				break;
			case PrimitiveVariable::Vertex :
				elem = ATTR_ELEMENT_VERTEX;
				break;
			case PrimitiveVariable::Varying :
			case PrimitiveVariable::FaceVarying :
				elem = ATTR_ELEMENT_CORNER;
				break;
			case PrimitiveVariable::Uniform :
				elem = ATTR_ELEMENT_FACE;
				break;
			default :
				break;
		}
		attr = attributes.find( name.c_str() );
		if( !attr )
			attr = attributes.add( name.c_str(), type, elem );
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

			for( size_t i = 0; i < num; ++i, ++cdata; )
				*cdata = attr->make_float( floatData[i] );
			cdata = attr->data_float();
		}
		else
		{
			msg( Msg::Warning, "IECoreCyles::NodeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected FloatVectorData)." ) % name % value.data->typeName() );
			attributes.remove( name );
		}
	}
	else
	{
		const V3fVectorData *data = runTimeCast<const V3fVectorData>( value.data.get() );
		if( data )
		{
			const std::vector<V3f> &v3fData = data->readable();
			size_t num = v3fData->readable().size();
			float3 *cdata = attr->data_float3();

			for( size_t i = 0; i < num; ++i, ++cdata; )
				*cdata = ccl::make_float3( v3fData[i].x, v3fData[i].y, v3fData[i].z );
			cdata = attr->data_float3();
		}
		else
		{
			msg( Msg::Warning, "IECoreCyles::NodeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected V3fVectorData)." ) % name % value.data->typeName() );
			attributes.remove( name );
		}
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace IECoreCycles
{

namespace ObjectAlgo
{

ccl::Object *convert( const IECore::Object *object, const std::string &nodeName )
{
	const Registry &r = registry();
	Registry::const_iterator it = r.find( object->typeId() );
	if( it == r.end() )
	{
		return nullptr;
	}
	return it->second.converter( object, nodeName );
}

ccl::Object *convert( const std::vector<const IECore::Object *> &samples, const std::string &nodeName )
{
	if( samples.empty() )
	{
		return nullptr;
	}

	const IECore::Object *firstSample = samples.front();
	const IECore::TypeId firstSampleTypeId = firstSample->typeId();
	for( std::vector<const IECore::Object *>::const_iterator it = samples.begin()+1, eIt = samples.end(); it != eIt; ++it )
	{
		if( (*it)->typeId() != firstSampleTypeId )
		{
			throw IECore::Exception( "Inconsistent object types." );
		}
	}

	const Registry &r = registry();
	Registry::const_iterator it = r.find( firstSampleTypeId );
	if( it == r.end() )
	{
		return nullptr;
	}
	if( it->second.motionConverter )
	{
		return it->second.motionConverter( samples, nodeName );
	}
	else
	{
		return it->second.converter( samples.front(), nodeName );
	}
}

void registerConverter( IECore::TypeId fromType, Converter converter, MotionConverter motionConverter )
{
	registry().insert( Registry::value_type( fromType, Converters( converter, motionConverter ) ) );
}

} // namespace ObjectAlgo

} // namespace IECoreCycles
