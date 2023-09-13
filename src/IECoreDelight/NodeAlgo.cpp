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

#include "IECoreDelight/NodeAlgo.h"

#include "IECoreDelight/ParameterList.h"

#include "IECore/MessageHandler.h"

#include <unordered_map>

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

using namespace IECoreDelight;

struct Converters
{

	NodeAlgo::Converter converter;
	NodeAlgo::MotionConverter motionConverter;

};

using Registry = std::unordered_map<IECore::TypeId, Converters>;

Registry &registry()
{
	static Registry r;
	return r;
}

void addPrimitiveVariableParameters( const char *name, const IECoreScene::PrimitiveVariable &value, const IECore::IntVectorData *vertexIndices, ParameterList &parameterList, ParameterList *indicesParameterList )
{
	const char *conformedName = strcmp( name, "uv" ) == 0 ? "st" : name;

	NSIParam_t p = parameterList.parameter( conformedName, value.data.get(), false );
	if( p.type == NSITypeInvalid )
	{
		return;
	}

	if( strcmp( conformedName, "P" ) == 0 )
	{
		// Work around sloppy use of geometric interpretation
		p.type = NSITypePoint;
	}

	switch( value.interpolation )
	{
		case PrimitiveVariable::Vertex :
			p.flags |= NSIParamPerVertex;
			break;
		case PrimitiveVariable::Varying :
			p.flags |= NSIParamPerVertex | NSIParamInterpolateLinear;
			break;
		case PrimitiveVariable::Uniform :
			p.flags |= NSIParamPerFace;
			break;
		case PrimitiveVariable::FaceVarying :
			/// \todo Hopefully this will make more sense
			/// once we have indexed primvars.
			break;
		default :
			break;
	}

	const IntVectorData *indices = nullptr;

	if( value.interpolation == PrimitiveVariable::Vertex && vertexIndices )
	{
		if( value.indices )
		{
			IECore::msg( IECore::Msg::Warning, "IECoreDelight", "Primitive variable indices not supported for Vertex interpolation" );
			return;
		}
		indices = vertexIndices;
	}
	else
	{
		indices = value.indices.get();
	}

	if( indices )
	{
		if( indicesParameterList )
		{
			const string indicesName = conformedName + string( ".indices" );
			indicesParameterList->add( {
				indicesParameterList->allocate( indicesName ),
				indices->readable().data(),
				NSITypeInteger,
				0,
				indices->readable().size(),
				0
			} );
		}
	}

	parameterList.add( p );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace IECoreDelight
{

namespace NodeAlgo
{

bool convert( const IECore::Object *object, NSIContext_t context, const char *handle )
{
	Registry &r = registry();
	auto it = r.find( object->typeId() );
	if( it == r.end() )
	{
		return false;
	}
	return it->second.converter( object, context, handle );
}

bool convert( const std::vector<const IECore::Object *> &samples, const std::vector<float> &sampleTimes, NSIContext_t context, const char *handle )
{
	Registry &r = registry();
	auto it = r.find( samples.front()->typeId() );
	if( it == r.end() )
	{
		return false;
	}
	if( it->second.motionConverter )
	{
		return it->second.motionConverter( samples, sampleTimes, context, handle );
	}
	else
	{
		return it->second.converter( samples.front(), context, handle );
	}
}

void registerConverter( IECore::TypeId fromType, Converter converter, MotionConverter motionConverter )
{
	registry()[fromType] = { converter, motionConverter };
}

void primitiveVariableParameterList( const IECoreScene::Primitive *primitive, ParameterList &parameters, const IECore::IntVectorData *vertexIndices )
{
	for( const auto &variable : primitive->variables )
	{
		addPrimitiveVariableParameters( variable.first.c_str(), variable.second, vertexIndices, parameters, &parameters );
	}
}

void primitiveVariableParameterLists( const std::vector<const IECoreScene::Primitive *> &primitives, ParameterList &staticParameters, std::vector<ParameterList> &animatedParameters, const IECore::IntVectorData *vertexIndices )
{
	for( const auto &variable : primitives.front()->variables )
	{
		bool moving = false;
		for( size_t i = 1, e = primitives.size(); i < e; ++i )
		{
			auto it = primitives[i]->variables.find( variable.first );
			if( it == primitives[i]->variables.end() )
			{
				moving = false;
				break;
			}
			else
			{
				if( it->second != variable.second )
				{
					moving = true;
					// Note that we do not break, because if a
					// later primitive omits the variable, we must
					// treat it as non-moving.
				}
			}
		}

		if( !moving )
		{
			addPrimitiveVariableParameters( variable.first.c_str(), variable.second, vertexIndices, staticParameters, &staticParameters );
		}
		else
		{
			if( animatedParameters.empty() )
			{
				animatedParameters.resize( primitives.size() );
			}
			for( size_t i = 0, e = primitives.size(); i < e; ++i )
			{
				addPrimitiveVariableParameters(
					variable.first.c_str(),
					primitives[i]->variables.find( variable.first )->second,
					vertexIndices,
					animatedParameters[i],
					i == 0 ? &staticParameters : nullptr
				);
			}
		}
	}
}

} // namespace NodeAlgo

} // namespace IECoreDelight
