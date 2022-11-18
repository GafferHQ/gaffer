//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "IECoreArnold/ParameterAlgo.h"

#include "IECore/DataAlgo.h"
#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

#include "ai_array.h"
#include "ai_msg.h" // Required for __AI_FILE__ macro used by `ai_array.h`
#include "ai_version.h"

using namespace std;
using namespace IECore;
using namespace IECoreArnold;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

using ArrayPtr = std::unique_ptr<AtArray, void (*)( AtArray *)>;

template<typename T>
inline const T *dataCast( const char *name, const IECore::Data *data )
{
	const T *result = runTimeCast<const T>( data );
	if( result )
	{
		return result;
	}
	msg( Msg::Warning, "setParameter", boost::format( "Unsupported value type \"%s\" for parameter \"%s\" (expected %s)." ) % data->typeName() % name % T::staticTypeName() );
	return nullptr;
}

void setParameterInternal( AtNode *node, AtString name, int parameterType, bool array, const IECore::Data *value )
{
	if( array )
	{
		AtArray *a = ParameterAlgo::dataToArray( value, parameterType );
		if( !a )
		{
			msg( Msg::Warning, "setParameter", boost::format( "Unable to create array from data of type \"%s\" for parameter \"%s\"" ) % value->typeName() % name );
			return;
		}
		if( AiArrayGetType( a ) != parameterType )
		{
			msg( Msg::Warning, "setParameter", boost::format( "Unable to create array of type %s from data of type \"%s\" for parameter \"%s\"" ) % AiParamGetTypeName( parameterType ) % value->typeName() % name );
			return;
		}
		AiNodeSetArray( node, name, a );
	}
	else
	{
		switch( parameterType )
		{
			case AI_TYPE_INT :
				if( const IntData *data = dataCast<IntData>( name, value ) )
				{
					AiNodeSetInt( node, name, data->readable() );
				}
				break;
			case AI_TYPE_UINT :
				if( const IntData *data = runTimeCast<const IntData>( value ) )
				{
					AiNodeSetUInt( node, name, std::max( 0, data->readable() ) );
				}
				else if( const UIntData *data = dataCast<UIntData>( name, value ) )
				{
					AiNodeSetUInt( node, name, data->readable() );
				}
				break;
			case AI_TYPE_BYTE :
				if( const IntData *data = dataCast<IntData>( name, value ) )
				{
					AiNodeSetByte( node, name, data->readable() );
				}
				break;
			case AI_TYPE_FLOAT :
				if( const DoubleData *data = runTimeCast<const DoubleData>( value ) )
				{
					AiNodeSetFlt( node, name, data->readable() );
				}
				else if( const FloatData *data = dataCast<FloatData>( name, value ) )
				{
					AiNodeSetFlt( node, name, data->readable() );
				}
				break;
			case AI_TYPE_STRING :
				if( const InternedStringData *data = runTimeCast<const InternedStringData>( value ) )
				{
					AiNodeSetStr( node, name, AtString( data->readable().c_str() ) );
				}
				else if( const StringData *data = dataCast<StringData>( name, value ) )
				{
					AiNodeSetStr( node, name, AtString( data->readable().c_str() ) );
				}
				break;
			case AI_TYPE_RGB :
				if( const Color3fData *data = dataCast<Color3fData>( name, value ) )
				{
					const Imath::Color3f &c = data->readable();
					AiNodeSetRGB( node, name, c[0], c[1], c[2] );
				}
				break;
			case AI_TYPE_RGBA :
				if( const Color4fData *data = dataCast<Color4fData>( name, value ) )
				{
					const Imath::Color4f &c = data->readable();
					AiNodeSetRGBA( node, name, c[0], c[1], c[2], c[3] );
				}
				break;
			case AI_TYPE_ENUM :
				// Arnold supports setting enums with either the integer index or the string name

				// First try getting an integer, but don't warn if it fails
				if( const IntData *data = runTimeCast<const IntData>( value ) )
				{
					AiNodeSetInt( node, name, data->readable() );
				}
				// Then try getting a string, with the usual warning if nothing has been found yet
				else if( const StringData *data = dataCast<StringData>( name, value ) )
				{
					AiNodeSetStr( node, name, AtString( data->readable().c_str() ) );
				}
				break;
			case AI_TYPE_BOOLEAN :
				if( const BoolData *data = dataCast<BoolData>( name, value ) )
				{
					AiNodeSetBool( node, name, data->readable() );
				}
				break;
			case AI_TYPE_VECTOR2 :
				if( const V2iData *data = runTimeCast<const V2iData>( value ) )
				{
					// Accept a V2i as an alternate since Arnold has
					// no integer vector type to store these in.
					const Imath::V2i &v = data->readable();
					AiNodeSetVec2( node, name, v.x, v.y );
				}
				else if( const V2fData *data = dataCast<V2fData>( name, value ) )
				{
					const Imath::V2f &v = data->readable();
					AiNodeSetVec2( node, name, v.x, v.y );
				}
				break;
			case AI_TYPE_VECTOR :
				if( const V3iData *data = runTimeCast<const V3iData>( value ) )
				{
					// Accept a V3i as an alternate since Arnold has
					// no integer vector type to store these in.
					const Imath::V3i &v = data->readable();
					AiNodeSetVec( node, name, v.x, v.y, v.z );
				}
				else if( const V3fData *data = dataCast<V3fData>( name, value ) )
				{
					const Imath::V3f &v = data->readable();
					AiNodeSetVec( node, name, v.x, v.y, v.z );
				}
				break;
			case AI_TYPE_MATRIX :
				if( const M44dData *data = runTimeCast<const M44dData>( value ) )
				{
					const Imath::M44f v( data->readable() );
					AiNodeSetMatrix( node, name, reinterpret_cast<const AtMatrix &>( v.x ) );
				}
				else if( const M44fData *data = dataCast<M44fData>( name, value ) )
				{
					const Imath::M44f &v = data->readable();

					// Can't see any reason why AiNodeSetMatrix couldn't have been declared const,
					// this const_cast seems safe
					AiNodeSetMatrix( node, name, reinterpret_cast<const AtMatrix &>( v.x ) );
				}
				break;
			default :
			{
				std::string nodeStr = AiNodeGetName( node );
				if( nodeStr == "" )
				{
					nodeStr = AiNodeEntryGetName( AiNodeGetNodeEntry( node ) );
				}

				msg( Msg::Warning, "setParameter", boost::format( "Arnold parameter \"%s\" on node \"%s\" has unsupported type \"%s\"." ) % name % nodeStr % AiParamGetTypeName( parameterType ) );
			}
		}
	}
}

template<typename T, typename F>
IECore::DataPtr arrayToDataInternal( AtArray *array, F f )
{
	using VectorType = vector<T>;
	using DataType = IECore::TypedData<vector<T> >;
	typename DataType::Ptr data = new DataType;
	VectorType &v = data->writable();

	v.reserve( AiArrayGetNumElements(array) );
	for( size_t i = 0; i < AiArrayGetNumElements(array); ++i )
	{
		v.push_back( f( array, i ) );
	}

	return data;
}

const char* getStrWrapper( const AtArray* a, uint32_t i )
{
	return AiArrayGetStr( a, i ).c_str();
}

IECore::DataPtr arrayToData( AtArray *array )
{
	if( AiArrayGetNumKeys( array ) > 1 )
	{
		/// \todo Decide how to deal with more
		/// than one key - is it more useful to return multiple Data
		/// objects or to put it all in one?
		return nullptr;
	}

	switch( AiArrayGetType( array ) )
	{
		case AI_TYPE_BOOLEAN :
			return arrayToDataInternal<bool>( array, AiArrayGetBool );
		case AI_TYPE_INT :
			return arrayToDataInternal<int>( array, AiArrayGetInt );
		case AI_TYPE_UINT :
			return arrayToDataInternal<uint32_t>( array, AiArrayGetUInt );
		case AI_TYPE_FLOAT :
			return arrayToDataInternal<float>( array, AiArrayGetFlt );
		case AI_TYPE_STRING :
			return arrayToDataInternal<string>( array, getStrWrapper );
		default :
			return nullptr;
	}
}

IECore::DataPtr getParameterInternal( AtNode *node, const AtString name, int parameterType )
{
	switch( parameterType )
	{
		case AI_TYPE_BOOLEAN :
			return new BoolData( AiNodeGetBool( node, name ) );
		case AI_TYPE_INT :
			return new IntData( AiNodeGetInt( node, name ) );
		case AI_TYPE_UINT :
			return new UIntData( AiNodeGetUInt( node, name ) );
		case AI_TYPE_FLOAT :
			return new FloatData( AiNodeGetFlt( node, name ) );
		case AI_TYPE_STRING :
			return new StringData( AiNodeGetStr( node, name ).c_str() );
		case AI_TYPE_RGB :
		{
			AtRGB rgb = AiNodeGetRGB( node, name );
			return new Color3fData( Imath::Color3f( rgb.r, rgb.g, rgb.b ) );
		}
		case AI_TYPE_RGBA :
		{
			AtRGBA rgba = AiNodeGetRGBA( node, name );
			return new Color4fData( Imath::Color4f( rgba.r, rgba.g, rgba.b, rgba.a ) );
		}
		case AI_TYPE_VECTOR :
		{
			AtVector vector = AiNodeGetVec( node, name );
			return new V3fData( Imath::V3f( vector.x, vector.y, vector.z ));
		}
		case AI_TYPE_ARRAY :
			return arrayToData( AiNodeGetArray( node, name ) );
	}
	return nullptr;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API.
//////////////////////////////////////////////////////////////////////////

namespace IECoreArnold
{

namespace ParameterAlgo
{

void setParameter( AtNode *node, const AtParamEntry *parameter, const IECore::Data *value )
{
	bool isArray = false;
	int type = AiParamGetType( parameter );
	if( type == AI_TYPE_ARRAY )
	{
		type = AiArrayGetType( AiParamGetDefault( parameter )->ARRAY() );
		isArray = true;
	}

	setParameterInternal( node, AiParamGetName( parameter ), type, isArray, value );
}

void setParameter( AtNode *node, AtString name, const IECore::Data *value )
{
	const AtParamEntry *parameter = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), name );
	if( parameter )
	{
		setParameter( node, parameter, value );
	}
	else
	{
		bool array = false;
		int type = parameterType( value->typeId(), array );
		if( type != AI_TYPE_NONE )
		{
			std::string typeString = "constant ";
			if( array )
			{
				typeString += "ARRAY ";
			}
			typeString += AiParamGetTypeName( type );
			if( !AiNodeLookUpUserParameter( node, name ) )
			{
				AiNodeDeclare( node, name, typeString.c_str() );
			}
			setParameterInternal( node, name, type, array, value );
		}
		else
		{
			msg(
				Msg::Warning,
				"setParameter",
				boost::format( "Unsupported data type \"%s\" for name \"%s\"" ) % value->typeName() % name
			);
		}
	}
}

void setParameter( AtNode *node, const char* name, const IECore::Data *value )
{
	setParameter( node, AtString( name ), value );
}

void setParameters( AtNode *node, const IECore::CompoundDataMap &values )
{
	for( CompoundDataMap::const_iterator it=values.begin(); it!=values.end(); it++ )
	{
		setParameter( node, it->first.value().c_str(), it->second.get() );
	}
}

IECore::DataPtr getParameter( AtNode *node, const AtParamEntry *parameter )
{
	return getParameterInternal( node, AiParamGetName( parameter ), AiParamGetType( parameter ) );
}

IECore::DataPtr getParameter( AtNode *node, const AtUserParamEntry *parameter )
{
	// \todo : This cast to AtString appears to be necessary only because SolidAngle missed this one while updating
	// their API.  If they fix it in the future, AiUserParamGetName would return AtString, and this cast would
	// be unnecessary
	return getParameterInternal( node, AtString( AiUserParamGetName( parameter ) ), AiUserParamGetType( parameter ) );
}

IECore::DataPtr getParameter( AtNode *node, AtString name )
{
	const AtParamEntry *parameter = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), name );
	if( parameter )
	{
		return getParameter( node, parameter );
	}
	else
	{
		const AtUserParamEntry *userParameter = AiNodeLookUpUserParameter( node, name );
		if( userParameter )
		{
			return getParameter( node, userParameter );
		}
	}

	return nullptr;
}

IECore::DataPtr getParameter( AtNode *node, const char *name )
{
	return getParameter( node, AtString( name ) );
}

void getParameters( AtNode *node, IECore::CompoundDataMap &values )
{
	/// \todo Non-user parameters

	AtUserParamIterator *it = AiNodeGetUserParamIterator( node );
	while( const AtUserParamEntry *param = AiUserParamIteratorGetNext( it ) )
	{
		DataPtr d = getParameter( node, param );
		if( d )
		{
			values[AiUserParamGetName( param )] = d;
		}
		else
		{
			msg(
				Msg::Warning,
				"getParameters",
				boost::format( "Unable to convert user parameter \"%s\"" ) % AiUserParamGetName( param )
			);
		}
	}
	AiUserParamIteratorDestroy( it );
}

int parameterType( IECore::TypeId dataType, bool &array )
{
	switch( dataType )
	{
		// non-array types

		case IntDataTypeId :
			array = false;
			return AI_TYPE_INT;
		case UIntDataTypeId :
			array = false;
			return AI_TYPE_UINT;
		case FloatDataTypeId :
		case DoubleDataTypeId :
			array = false;
			return AI_TYPE_FLOAT;
		case StringDataTypeId :
		case InternedStringDataTypeId :
			array = false;
			return AI_TYPE_STRING;
		case Color3fDataTypeId :
			array = false;
			return AI_TYPE_RGB;
		case Color4fDataTypeId :
			array = false;
			return AI_TYPE_RGBA;
		case BoolDataTypeId :
			array = false;
			return AI_TYPE_BOOLEAN;
		case V2fDataTypeId :
		case V2iDataTypeId :
			array = false;
			return AI_TYPE_VECTOR2;
		case V3fDataTypeId :
		case V3iDataTypeId :
			array = false;
			return AI_TYPE_VECTOR;
		case M44fDataTypeId :
		case M44dDataTypeId :
			array = false;
			return AI_TYPE_MATRIX;

		// array types

		case IntVectorDataTypeId :
			array = true;
			return AI_TYPE_INT;
		case UIntVectorDataTypeId :
			array = true;
			return AI_TYPE_UINT;
		case FloatVectorDataTypeId :
			array = true;
			return AI_TYPE_FLOAT;
		case StringVectorDataTypeId :
			array = true;
			return AI_TYPE_STRING;
		case Color3fVectorDataTypeId :
			array = true;
			return AI_TYPE_RGB;
		case Color4fVectorDataTypeId :
			array = true;
			return AI_TYPE_RGBA;
		case BoolVectorDataTypeId :
			array = true;
			return AI_TYPE_BOOLEAN;
		case V2fVectorDataTypeId :
		case V2iVectorDataTypeId :
			array = true;
			return AI_TYPE_VECTOR2;
		case V3fVectorDataTypeId :
		case V3iVectorDataTypeId :
			array = true;
			return AI_TYPE_VECTOR;
		case M44fVectorDataTypeId :
			array = true;
			return AI_TYPE_MATRIX;
		default :
			return AI_TYPE_NONE;
	}
}

int parameterType( const IECore::Data *data, bool &array )
{
	return parameterType( data->typeId(), array );
}

AtArray *dataToArray( const IECore::Data *data, int aiType )
{
	if( aiType == AI_TYPE_NONE )
	{
		bool isArray = false;
		aiType = parameterType( data->typeId(), isArray );
		if( aiType == AI_TYPE_NONE || !isArray )
		{
			return nullptr;
		}
	}


	if( aiType == AI_TYPE_BOOLEAN )
	{
		// bools are a special case because of how the STL implements vector<bool>.
		// Since the base for vector<bool> are not actual booleans, we need to manually
		// convert to an AtArray here.
		const vector<bool> &booleans = static_cast<const BoolVectorData *>( data )->readable();
		vector<bool>::size_type booleansSize = booleans.size();
		AtArray* array = AiArrayAllocate( booleansSize, 1, AI_TYPE_BOOLEAN );
		for(vector<bool>::size_type i = 0; i < booleansSize; ++i){
			AiArraySetBool(array, i, booleans[i]);
		}
		return array;
	}
	else if( aiType == AI_TYPE_STRING )
	{
		const vector<string> &strings = static_cast<const StringVectorData *>( data )->readable();
		const vector<string>::size_type size = strings.size();
		AtArray *array = AiArrayAllocate( size, 1, AI_TYPE_STRING );
		for( vector<string>::size_type i = 0; i < size; ++i )
		{
			AiArraySetStr( array, i, strings[i].c_str() );
		}
		return array;
	}

	return AiArrayConvert( size( data ), 1, aiType, address( data ) );
}

AtArray *dataToArray( const std::vector<const IECore::Data *> &samples, int aiType )
{
	if( aiType == AI_TYPE_NONE )
	{
		bool isArray = false;
		aiType = parameterType( samples.front()->typeId(), isArray );
		if( aiType == AI_TYPE_NONE || !isArray )
		{
			return nullptr;
		}
	}

	const size_t arraySize = size( samples.front() );
	ArrayPtr array(
		AiArrayAllocate( arraySize, samples.size(), aiType ),
		AiArrayDestroy
	);

	for( vector<const IECore::Data *>::const_iterator it = samples.begin(), eIt = samples.end(); it != eIt; ++it )
	{
		if( (*it)->typeId() != samples.front()->typeId() )
		{
			throw IECore::Exception( "ParameterAlgo::dataToArray() : Mismatched sample types." );
		}
		if( size( *it ) != arraySize )
		{
			throw IECore::Exception( "ParameterAlgo::dataToArray() : Mismatched sample lengths." );
		}
		AiArraySetKey( array.get(), /* key = */ it - samples.begin(), address( *it ) );
	}

	return array.release();
}

} // namespace ParameterAlgo

} // namespace IECoreArnold
