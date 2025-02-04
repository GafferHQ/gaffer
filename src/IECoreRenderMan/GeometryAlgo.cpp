//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, John Haddon. All rights reserved.
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

#include "GeometryAlgo.h"

#include "ParamListAlgo.h"

#include "IECore/DataAlgo.h"
#include "IECore/MessageHandler.h"

#include "fmt/format.h"

#include <unordered_map>

using namespace std;
using namespace IECore;
using namespace IECoreScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

using namespace IECoreRenderMan;

struct Converters
{

	GeometryAlgo::Converter converter;
	GeometryAlgo::MotionConverter motionConverter;

};

using Registry = std::unordered_map<IECore::TypeId, Converters>;

Registry &registry()
{
	static Registry r;
	return r;
}

RtDetailType detail( IECoreScene::PrimitiveVariable::Interpolation interpolation )
{
	switch( interpolation )
	{
		case PrimitiveVariable::Invalid :
			throw IECore::Exception( "No detail equivalent to PrimitiveVariable::Invalid" );
		case PrimitiveVariable::Constant :
			return RtDetailType::k_constant;
		case PrimitiveVariable::Uniform :
			return RtDetailType::k_uniform;
		case PrimitiveVariable::Vertex :
			return RtDetailType::k_vertex;
		case PrimitiveVariable::Varying :
			return RtDetailType::k_varying;
		case PrimitiveVariable::FaceVarying :
			return RtDetailType::k_facevarying;
		default :
			throw IECore::Exception( "Unknown PrimtiveVariable Interpolation" );
	}
}

RtDataType dataType( IECore::GeometricData::Interpretation interpretation )
{
	switch( interpretation )
	{
		case GeometricData::Vector :
			return RtDataType::k_vector;
		case GeometricData::Normal :
			return RtDataType::k_normal;
		default :
			return RtDataType::k_point;
	}
}

struct PrimitiveVariableConverter
{

	PrimitiveVariableConverter( const std::string &messageContext )
		:	m_messageContext( messageContext )
	{
	}

	// Simple data

	void operator()( const BoolData *data, RtUString name, const PrimitiveVariable &primitiveVariable, RtPrimVarList &primVarList, unsigned sampleIndex=0 ) const
	{
		const int b = data->readable();
		primVarList.SetIntegerDetail( name, &b, detail( primitiveVariable.interpolation ), sampleIndex );
	}

	void operator()( const IntData *data, RtUString name, const PrimitiveVariable &primitiveVariable, RtPrimVarList &primVarList, unsigned sampleIndex=0 ) const
	{
		primVarList.SetIntegerDetail( name, &data->readable(), detail( primitiveVariable.interpolation ), sampleIndex );
	}

	void operator()( const FloatData *data, RtUString name, const PrimitiveVariable &primitiveVariable, RtPrimVarList &primVarList, unsigned sampleIndex=0 ) const
	{
		primVarList.SetFloatDetail( name, &data->readable(), detail( primitiveVariable.interpolation ), sampleIndex );
	}

	void operator()( const StringData *data, RtUString name, const PrimitiveVariable &primitiveVariable, RtPrimVarList &primVarList, unsigned sampleIndex=0 ) const
	{
		RtUString s( data->readable().c_str() );
		primVarList.SetStringDetail( name, &s, detail( primitiveVariable.interpolation ), sampleIndex );
	}

	void operator()( const Color3fData *data, RtUString name, const PrimitiveVariable &primitiveVariable, RtPrimVarList &primVarList, unsigned sampleIndex=0 ) const
	{
		primVarList.SetColorDetail( name, reinterpret_cast<const RtColorRGB *>( data->readable().getValue() ), detail( primitiveVariable.interpolation ), sampleIndex );
	}

	void operator()( const V3fData *data, RtUString name, const PrimitiveVariable &primitiveVariable, RtPrimVarList &primVarList, unsigned sampleIndex=0 ) const
	{
		primVarList.SetParam(
			{
				name,
				dataType( data->getInterpretation() ),
				detail( primitiveVariable.interpolation ),
				/* length = */ 1,
				/* array = */ false,
				/* motion = */ sampleIndex > 0,
				/* deduplicated = */ false
			},
			data->readable().getValue(),
			sampleIndex
		);
	}

	// Vector data

	void operator()( const IntVectorData *data, RtUString name, const PrimitiveVariable &primitiveVariable, RtPrimVarList &primVarList, unsigned sampleIndex=0 ) const
	{
		emit(
			data,
			{
				name,
				RtDataType::k_integer,
				detail( primitiveVariable.interpolation ),
				/* length = */ 1,
				/* array = */ false,
				/* motion = */ sampleIndex > 0,
				/* deduplicated = */ false
			},
			primitiveVariable,
			primVarList,
			sampleIndex
		);
	}

	void operator()( const FloatVectorData *data, RtUString name, const PrimitiveVariable &primitiveVariable, RtPrimVarList &primVarList, unsigned sampleIndex=0 ) const
	{
		emit(
			data,
			{
				name,
				RtDataType::k_float,
				detail( primitiveVariable.interpolation ),
				/* length = */ 1,
				/* array = */ false,
				/* motion = */ sampleIndex > 0,
				/* deduplicated = */ false
			},
			primitiveVariable,
			primVarList,
			sampleIndex
		);
	}

	void operator()( const StringVectorData *data, RtUString name, const PrimitiveVariable &primitiveVariable, RtPrimVarList &primVarList, unsigned sampleIndex=0 ) const
	{
		PrimitiveVariable::IndexedView<string> view( primitiveVariable );
		vector<RtUString> value; value.reserve( view.size() );
		for( size_t i = 0; i < view.size(); ++i )
		{
			value.push_back( RtUString( view[i].c_str() ) );
		}
		primVarList.SetStringDetail( name, value.data(), detail( primitiveVariable.interpolation ), sampleIndex );
	}

	void operator()( const V2fVectorData *data, RtUString name, const PrimitiveVariable &primitiveVariable, RtPrimVarList &primVarList, unsigned sampleIndex=0 ) const
	{
		emit(
			data,
			{
				name,
				RtDataType::k_float,
				detail( primitiveVariable.interpolation ),
				/* length = */ 2,
				/* array = */ true,
				/* motion = */ sampleIndex > 0,
				/* deduplicated = */ false
			},
			primitiveVariable,
			primVarList,
			sampleIndex
		);
	}

	void operator()( const V3fVectorData *data, RtUString name, const PrimitiveVariable &primitiveVariable, RtPrimVarList &primVarList, unsigned sampleIndex=0 ) const
	{
		emit(
			data,
			{
				name,
				dataType( data->getInterpretation() ),
				detail( primitiveVariable.interpolation ),
				/* length = */ 1,
				/* array = */ false,
				/* motion = */ sampleIndex > 0,
				/* deduplicated = */ false
			},
			primitiveVariable,
			primVarList,
			sampleIndex
		);
	}

	void operator()( const Color3fVectorData *data, RtUString name, const PrimitiveVariable &primitiveVariable, RtPrimVarList &primVarList, unsigned sampleIndex=0 ) const
	{
		emit(
			data,
			{
				name,
				RtDataType::k_color,
				detail( primitiveVariable.interpolation ),
				/* length = */ 1,
				/* array = */ false,
				/* motion = */ sampleIndex > 0,
				/* deduplicated = */ false
			},
			primitiveVariable,
			primVarList,
			sampleIndex
		);
	}

	void operator()( const Data *data, RtUString name, const PrimitiveVariable &primitiveVariable, RtPrimVarList &primVarList, unsigned sampleIndex=0 ) const
	{
		IECore::msg(
			IECore::Msg::Warning,
			m_messageContext,
			fmt::format( "Unsupported primitive variable of type \"{}\"", data->typeName() )
		);
	}

	private :

		const std::string &m_messageContext;

		template<typename T>
		void emit( const T *data, const RtPrimVarList::ParamInfo &paramInfo, const PrimitiveVariable &primitiveVariable, RtPrimVarList &primVarList, unsigned sampleIndex=0 ) const
		{
			if( primitiveVariable.indices )
			{
				using Buffer = RtPrimVarList::Buffer<typename T::ValueType::value_type>;
				Buffer buffer( primVarList, paramInfo, sampleIndex );
				buffer.Bind();

				const vector<int> &indices = primitiveVariable.indices->readable();
				const typename T::ValueType &values = data->readable();
				for( int i = 0, e = indices.size(); i < e; ++i )
				{
					buffer[i] = values[indices[i]];
				}

				buffer.Unbind();
			}
			else
			{
				primVarList.SetParam(
					paramInfo,
					data->readable().data(),
					sampleIndex
				);
			}
		}

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of external API
//////////////////////////////////////////////////////////////////////////

RtUString IECoreRenderMan::GeometryAlgo::convert( const IECore::Object *object, RtPrimVarList &primVars, const std::string &messageContext )
{
	Registry &r = registry();
	auto it = r.find( object->typeId() );
	if( it == r.end() )
	{
		return RtUString();
	}
	return it->second.converter( object, primVars, messageContext );
}

RtUString IECoreRenderMan::GeometryAlgo::convert( const std::vector<const IECore::Object *> &samples, const std::vector<float> &sampleTimes, RtPrimVarList &primVars, const std::string &messageContext )
{
	Registry &r = registry();
	auto it = r.find( samples.front()->typeId() );
	if( it == r.end() )
	{
		return RtUString();
	}
	if( it->second.motionConverter )
	{
		return it->second.motionConverter( samples, sampleTimes, primVars, messageContext );
	}
	else
	{
		return it->second.converter( samples.front(), primVars, messageContext );
	}
}

void IECoreRenderMan::GeometryAlgo::registerConverter( IECore::TypeId fromType, Converter converter, MotionConverter motionConverter )
{
	registry()[fromType] = { converter, motionConverter };
}

void IECoreRenderMan::GeometryAlgo::convertPrimitiveVariables( const IECoreScene::Primitive *primitive, RtPrimVarList &primVarList, const std::string &messageContext )
{
	const PrimitiveVariableConverter converter( messageContext );
	for( const auto &[name, primitiveVariable] : primitive->variables )
	{
		const RtUString convertedName( name == "uv" ? "st" : name.c_str() );
		dispatch( primitiveVariable.data.get(), converter, convertedName, primitiveVariable, primVarList );
	}
}

void IECoreRenderMan::GeometryAlgo::convertPrimitiveVariables( const std::vector<const IECoreScene::Primitive *> &samples, const std::vector<float> &sampleTimes, RtPrimVarList &primVarList, const std::string &messageContext )
{
	const PrimitiveVariableConverter converter( messageContext );

	bool haveSetTimes = false;
	for( const auto &[name, primitiveVariable] : samples[0]->variables )
	{
		bool animated = false;
		for( size_t i = 1; i < samples.size(); ++i )
		{
			auto it = samples[i]->variables.find( name );
			if( it == samples[i]->variables.end() )
			{
				animated = false;
				break;
			}
			else if( it->second != primitiveVariable )
			{
				animated = true;
			}
		}

		const RtUString convertedName( name == "uv" ? "st" : name.c_str() );
		if( animated )
		{
			if( !haveSetTimes )
			{
				primVarList.SetTimes( sampleTimes.size(), sampleTimes.data() );
				haveSetTimes = true;
			}

			for( size_t i = 0; i < samples.size(); ++i )
			{
				auto it = samples[i]->variables.find( name );
				assert( it != samples[i]->variables.end() );
				dispatch( it->second.data.get(), converter, convertedName, primitiveVariable, primVarList, i );
			}
		}
		else
		{
			dispatch( primitiveVariable.data.get(), converter, convertedName, primitiveVariable, primVarList );
		}
	}
}
