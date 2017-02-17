//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
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

#include "IECore/SimpleTypedData.h"
#include "IECore/VectorTypedData.h"

#include "GafferImage/OpenImageIOAlgo.h"

using namespace OIIO;
using namespace IECore;

namespace GafferImage
{

namespace OpenImageIOAlgo
{

OIIO::TypeDesc::VECSEMANTICS vecSemantics( IECore::GeometricData::Interpretation interpretation )
{
	switch( interpretation )
	{
		case GeometricData::Point :
			return TypeDesc::POINT;
		case GeometricData::Normal :
			return TypeDesc::NORMAL;
		case GeometricData::Vector :
			return TypeDesc::VECTOR;
		case GeometricData::Color :
			return TypeDesc::COLOR;
		default :
			return TypeDesc::NOXFORM;
	}
}

IECore::GeometricData::Interpretation geometricInterpretation( OIIO::TypeDesc::VECSEMANTICS semantics )
{
	switch( semantics )
	{
		case TypeDesc::NOXFORM :
			return GeometricData::Numeric;
		case TypeDesc::COLOR :
			return GeometricData::Color;
		case TypeDesc::POINT :
			return GeometricData::Point;
		case TypeDesc::VECTOR :
			return GeometricData::Vector;
		case TypeDesc::NORMAL :
			return GeometricData::Normal;
		default :
			return GeometricData::Numeric;
	}
}

DataView::DataView()
	:	data( NULL ), m_charPointer( NULL )
{
}

DataView::DataView( const IECore::Data *d )
	:	data( NULL ), m_charPointer( NULL )
{
	switch( d ? d->typeId() : IECore::InvalidTypeId )
	{

		// Simple data

		case CharDataTypeId :
			type = TypeDesc::CHAR;
			data = static_cast<const CharData *>( d )->baseReadable();
			break;
		case UCharDataTypeId :
			type = TypeDesc::UCHAR;
			data = static_cast<const UCharData *>( d )->baseReadable();
			break;
		case StringDataTypeId :
			type = TypeDesc::TypeString;
			m_charPointer = static_cast<const StringData *>( d )->readable().c_str();
			data = &m_charPointer;
			break;
		case UShortDataTypeId :
			type = TypeDesc::USHORT;
			data = static_cast<const UShortData *>( d )->baseReadable();
			break;
		case ShortDataTypeId :
			type = TypeDesc::SHORT;
			data = static_cast<const ShortData *>( d )->baseReadable();
			break;
		case UIntDataTypeId :
			type = TypeDesc::UINT;
			data = static_cast<const UIntData *>( d )->baseReadable();
			break;
		case HalfDataTypeId :
			type = TypeDesc::HALF;
			data = static_cast<const HalfData *>( d )->baseReadable();
			break;
		case IntDataTypeId :
			type = TypeDesc::TypeInt;
			data = static_cast<const IntData *>( d )->baseReadable();
			break;
		case FloatDataTypeId :
			type = TypeDesc::TypeFloat;
			data = static_cast<const FloatData *>( d )->baseReadable();
			break;
		case DoubleDataTypeId :
			type = TypeDesc::DOUBLE;
			data = static_cast<const DoubleData *>( d )->baseReadable();
			break;
		case V2iDataTypeId :
			type = TypeDesc( TypeDesc::INT, TypeDesc::VEC2 );
			data = static_cast<const V2iData *>( d )->baseReadable();
			break;
		case V3iDataTypeId :
			type = TypeDesc( TypeDesc::INT, TypeDesc::VEC3 );
			data = static_cast<const V3iData *>( d )->baseReadable();
			break;
		case V2fDataTypeId :
			type = TypeDesc( TypeDesc::FLOAT, TypeDesc::VEC2, vecSemantics( static_cast<const V2fData *>( d )->getInterpretation() ) );
			data = static_cast<const V2fData *>( d )->baseReadable();
			break;
		case V3fDataTypeId :
			type = TypeDesc( TypeDesc::FLOAT, TypeDesc::VEC3, vecSemantics( static_cast<const V3fData *>( d )->getInterpretation() ) );
			data = static_cast<const V3fData *>( d )->baseReadable();
			break;
		case M44fDataTypeId :
			type = TypeDesc( TypeDesc::FLOAT, TypeDesc::MATRIX44 );
			data = static_cast<const M44fData *>( d )->baseReadable();
			break;
		case V2dDataTypeId :
			type = TypeDesc( TypeDesc::DOUBLE, TypeDesc::VEC2, vecSemantics( static_cast<const V2dData *>( d )->getInterpretation() ) );
			data = static_cast<const V2dData *>( d )->baseReadable();
			break;
		case V3dDataTypeId :
			type = TypeDesc( TypeDesc::DOUBLE, TypeDesc::VEC3, vecSemantics( static_cast<const V3dData *>( d )->getInterpretation() ) );
			data = static_cast<const V3dData *>( d )->baseReadable();
			break;
		case M44dDataTypeId :
			type = TypeDesc( TypeDesc::DOUBLE, TypeDesc::MATRIX44 );
			data = static_cast<const M44dData *>( d )->baseReadable();
			break;
		case Color3fDataTypeId :
			type = TypeDesc::TypeColor;
			data = static_cast<const Color3fData *>( d )->baseReadable();
			break;

		// Vector data

		case FloatVectorDataTypeId :
			type = TypeDesc( TypeDesc::FLOAT, static_cast<const FloatVectorData *>( d )->readable().size() );
			data = static_cast<const FloatVectorData *>( d )->baseReadable();
			break;
		case IntVectorDataTypeId :
			type = TypeDesc( TypeDesc::INT, static_cast<const IntVectorData *>( d )->readable().size() );
			data = static_cast<const IntVectorData *>( d )->baseReadable();
			break;
		case V3fVectorDataTypeId :
			type = TypeDesc(
				TypeDesc::FLOAT,
				TypeDesc::VEC3,
				vecSemantics( static_cast<const V3fVectorData *>( d )->getInterpretation() ),
				static_cast<const V3fVectorData *>( d )->readable().size()
			);
			data = static_cast<const V3fVectorData *>( d )->baseReadable();
			break;
		case Color3fVectorDataTypeId :
			type = TypeDesc(
				TypeDesc::FLOAT,
				TypeDesc::VEC3,
				TypeDesc::COLOR,
				static_cast<const Color3fVectorData *>( d )->readable().size()
			);
			data = static_cast<const Color3fVectorData *>( d )->baseReadable();
			break;
		case M44fVectorDataTypeId :
			type = TypeDesc(
				TypeDesc::FLOAT,
				TypeDesc::MATRIX44,
				TypeDesc::COLOR,
				static_cast<const M44fVectorData *>( d )->readable().size()
			);
			data = static_cast<const M44fVectorData *>( d )->baseReadable();
			break;

		default :
			// Default initialisers above did what we need already
			break;

	}
}

} // namespace OpenImageIOAlgo

} // namespace GafferImage


