//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
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

#include "IECoreDelight/ParameterList.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

#include "fmt/format.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreDelight;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

NSIType_t type( GeometricData::Interpretation interpretation )
{
	switch( interpretation )
	{
		case GeometricData::None :
			return NSITypeVector;
		case GeometricData::Point :
			return NSITypePoint;
		case GeometricData::Normal :
			return NSITypeNormal;
		case GeometricData::Vector :
			return NSITypeVector;
		case GeometricData::Color :
			return NSITypeColor;
		default :
			return NSITypeInvalid;
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ParameterList
//////////////////////////////////////////////////////////////////////////

ParameterList::ParameterList()
{
}

ParameterList::ParameterList( std::initializer_list<NSIParam_t> parameters )
	:	m_params( parameters )
{
}

ParameterList::ParameterList( const IECore::CompoundDataMap &values )
{
	for( const auto &p : values )
	{
		add( p.first.c_str(), p.second.get() );
	}
}

ParameterList::~ParameterList()
{
	for( const void *p : m_allocations )
	{
		free( const_cast<void *>( p ) );
	}
}

void ParameterList::add( const NSIParam_t &parameter )
{
	m_params.push_back( parameter );
}

void ParameterList::add( const char *name, const std::string &value )
{
	const char **charPtr = allocate<const char *>();
	*charPtr = value.c_str();
	add( { name, charPtr, NSITypeString, 0, 1, 0 } );
}

void ParameterList::add( const char *name, const IECore::Data *value )
{
	NSIParam_t p = parameter( name, value );
	if( p.type != NSITypeInvalid )
	{
		add( p );
	}
}

int ParameterList::size() const
{
	return m_params.size();
}

const NSIParam_t *ParameterList::data() const
{
	return m_params.data();
}

NSIParam_t ParameterList::parameter( const char *name, const IECore::Data *value )
{
	NSIParam_t result = {
		name,
		nullptr, // data
		NSITypeInvalid,
		0, // array length
		0, // count
		0  // flags
	};

	switch( value->typeId() )
	{
		// Simple
		case BoolDataTypeId :
		{
			result.type = NSITypeInteger;
			int *intPtr = allocate<int>();
			*intPtr = static_cast<const BoolData *>( value )->readable();
			result.data = intPtr;
			result.count = 1;
			break;
		}
		case IntDataTypeId :
			result.type = NSITypeInteger;
			result.data = static_cast<const IntData *>( value )->baseReadable();
			result.count = 1;
			break;
		case FloatDataTypeId :
			result.type = NSITypeFloat;
			result.data = static_cast<const FloatData *>( value )->baseReadable();
			result.count = 1;
			break;
		case DoubleDataTypeId :
			result.type = NSITypeDouble;
			result.data = static_cast<const DoubleData *>( value )->baseReadable();
			result.count = 1;
			break;
		case V2fDataTypeId :
			result.type = NSITypeFloat;
			result.arraylength = 2;
			result.flags |= NSIParamIsArray;
			result.data = static_cast<const V2fData *>( value )->baseReadable();
			result.count = 1;
			break;
		case Color3fDataTypeId :
			result.type = NSITypeColor;
			result.data = static_cast<const Color3fData *>( value )->baseReadable();
			result.count = 1;
			break;
		case V3fDataTypeId :
			result.type = type( static_cast<const V3fData *>( value )->getInterpretation() );
			result.data = static_cast<const Color3fData *>( value )->baseReadable();
			result.count = 1;
			break;
		case StringDataTypeId :
		{
			result.type = NSITypeString;
			const char **charPtr = allocate<const char *>();
			*charPtr = static_cast<const StringData *>( value )->readable().c_str();
			result.data = charPtr;
			result.count = 1;
			break;
		}
		// Vector
		case IntVectorDataTypeId :
		{
			const vector<int> &v = static_cast<const IntVectorData *>( value )->readable();
			result.type = NSITypeInteger;
			result.data = v.data();
			result.count = v.size();
			break;
		}
		case FloatVectorDataTypeId :
		{
			const vector<float> &v = static_cast<const FloatVectorData *>( value )->readable();
			result.type = NSITypeFloat;
			result.data = v.data();
			result.count = v.size();
			break;
		}
		case V2fVectorDataTypeId :
		{
			const vector<V2f> &v = static_cast<const V2fVectorData *>( value )->readable();
			result.type = NSITypeFloat;
			result.arraylength = 2;
			result.flags |= NSIParamIsArray;
			result.data = v.data();
			result.count = v.size();
			break;
		}
		case V3fVectorDataTypeId :
		{
			const vector<V3f> &v = static_cast<const V3fVectorData *>( value )->readable();
			result.type = type( static_cast<const V3fVectorData *>( value )->getInterpretation() );
			result.data = v.data();
			result.count = v.size();
			break;
		}
		case Color3fVectorDataTypeId :
		{
			const vector<Color3f> &v = static_cast<const Color3fVectorData *>( value )->readable();
			result.type = NSITypeColor;
			result.data = v.data();
			result.count = v.size();
			break;
		}
		default :
			result.type = NSITypeInvalid;
			msg( Msg::Warning, "ParameterList", fmt::format( "Attribute \"{}\" has unsupported datatype \"{}\".", name, value->typeName() ) );
			break;
	}
	return result;
}

const char *ParameterList::allocate( const std::string &s )
{
	const char *c = strdup( s.c_str() );
	m_allocations.push_back( c );
	return c;
}

template<typename T>
T *ParameterList::allocate()
{
	T *result = (T *)malloc( sizeof( T ) );
	m_allocations.push_back( result );
	return result;
}
