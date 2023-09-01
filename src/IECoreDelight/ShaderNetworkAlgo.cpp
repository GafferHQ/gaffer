//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECoreDelight/ShaderNetworkAlgo.h"

#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/SearchPath.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/SplineData.h"
#include "IECore/VectorTypedData.h"

#include "OSL/oslquery.h"
// Don't let windows.h smash over IECore::SearchPath via a macro
#ifdef SearchPath
#undef SearchPath
#endif

#include "boost/algorithm/string/predicate.hpp"

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;

namespace
{

/////////////////////////////////////////////////////////////////////////
// LRUCache of OSLQueries
//////////////////////////////////////////////////////////////////////////

using OSLQueryPtr = std::shared_ptr<OSL::OSLQuery>;
using QueryCache = IECorePreview::LRUCache<std::string, OSLQueryPtr, IECorePreview::LRUCachePolicy::Parallel>;

QueryCache &queryCache()
{
	static QueryCache g_cache(
		[] ( const std::string &shaderName, size_t &cost, const IECore::Canceller *canceller ) -> OSLQueryPtr {
			const char *searchPath = getenv( "OSL_SHADER_PATHS" );
			OSLQueryPtr query = std::make_shared<OSL::OSLQuery>();
			cost = 1;
			if( !query->open( shaderName, searchPath ? searchPath : "" ) )
			{
				return nullptr;
			}
			return query;
		},
		10000
	);
	return g_cache;
}

}  // namespace

namespace
{

// From https://gitlab.com/3Delight/3delight-for-houdini/-/blob/master/osl_utilities.cpp
enum BasisTypes
{
	CONSTANT,
	LINEAR,
	MONOTONECUBIC,
	CATMULLROM
};

int basisInt( const std::string &basis )
{
	if( basis == "constant" )
	{
		return BasisTypes::CONSTANT;
	}
	if( basis == "linear" )
	{
		return BasisTypes::LINEAR;
	}
	// `SplinePlug` converts from `monotonecubic` to `bezier`, so we'll never get `monotonecubic`

	return BasisTypes::CATMULLROM;
}

const OSL::OSLQuery::Parameter *splineValueParameter(
	const OSL::OSLQuery &query,
	const std::string &splineParameterName
)
{
	for( size_t i = 0, eI = query.nparams(); i < eI; ++i )
	{
		const OSL::OSLQuery::Parameter *p = query.getparam( i );

		if( !boost::starts_with( p->name, splineParameterName ) )
		{
			continue;
		}
		for( const auto &m : p->metadata )
		{
			if(
				m.name == "widget" &&
				m.sdefault.size() > 0 &&
				m.sdefault[0].find( "Ramp" ) != std::string::npos
			)
			{
				return p;
			}
		}
	}
	return nullptr;
}

bool find3DelightSplineParameters(
	const OSL::OSLQuery &query,
	const std::string &splineParameterName,
	const OSL::OSLQuery::Parameter * &positionsParameter,
	const OSL::OSLQuery::Parameter * &valuesParameter,
	const OSL::OSLQuery::Parameter * &basisParameter
)
{
	positionsParameter = nullptr;
	valuesParameter = nullptr;
	basisParameter = nullptr;

	valuesParameter = splineValueParameter( query, splineParameterName );

	if( valuesParameter )
	{
		for( size_t i = 0, eI = query.nparams(); i < eI; ++i )
		{
			const OSL::OSLQuery::Parameter *p = query.getparam( i );
			if( p == valuesParameter || !p->type.is_array() || !boost::starts_with( p->name, splineParameterName ) )
			{
				continue;
			}
			if( p->type.basetype == OSL::TypeDesc::INT && p->type.aggregate == OSL::TypeDesc::SCALAR )
			{
				// Here we prefer the `int` value basis parameter because that is the only
				// basis parameter that is consistently found in all 3delight splines.
				basisParameter = p;
			}
			if( p->type.basetype == OSL::TypeDesc::FLOAT && p->type.aggregate == OSL::TypeDesc::SCALAR )
			{
				positionsParameter = p;
			}
		}
	}

	return positionsParameter && valuesParameter && basisParameter;
}

void renameSplineParameters( ShaderNetwork *shaderNetwork )
{
	for( const auto &[handle, oldShader] : shaderNetwork->shaders() )
	{
		ShaderPtr shader = oldShader->copy();

		if( OSLQueryPtr query = queryCache().get( shader->getName() ) )
		{
			for( const auto &[name, value] : oldShader->parameters() )
			{
				InternedString newName = name;
				DataPtr newValue = value;

				const std::string &parameterName = name.string();
				if(
					boost::ends_with( parameterName, "Positions" ) ||
					boost::ends_with( parameterName, "Values" ) ||
					boost::ends_with( parameterName, "Basis" )
				)
				{
					std::string splineParameterName;

					if( boost::ends_with( parameterName, "Positions" ) )
					{
						splineParameterName = parameterName.substr( 0, parameterName.size() - 9 );
					}
					else if( boost::ends_with( parameterName, "Values" ) )
					{
						splineParameterName = parameterName.substr( 0, parameterName.size() - 6 );
					}
					else
					{
						splineParameterName = parameterName.substr( 0, parameterName.size() - 5 );
					}

					const OSL::OSLQuery::Parameter *positionsParameter;
					const OSL::OSLQuery::Parameter *valuesParameter;
					const OSL::OSLQuery::Parameter *basisParameter;

					if( find3DelightSplineParameters(
							*query,
							splineParameterName,
							positionsParameter,
							valuesParameter,
							basisParameter
						)
					)
					{
						if( name == splineParameterName + "Positions" )
						{
							newName = positionsParameter->name.string();
						}
						else if( name == splineParameterName + "Values" )
						{
							newName = valuesParameter->name.string();
						}
						else if( boost::ends_with( parameterName, "Basis" ) )
						{
							auto positionData = oldShader->parametersData()->member<const FloatVectorData>( splineParameterName + "Positions" );
							auto basisData = runTimeCast<const StringData>( value );

							if( positionData && basisData )
							{
								newName = basisParameter->name.string();
								newValue = new IntVectorData(
									std::vector<int>( positionData->readable().size(), basisInt( basisData->readable() ) )
								);
							}
						}
						shader->parameters().erase( name );
					}
				}
				shader->parameters()[newName] = newValue;
			}
		}

		shaderNetwork->setShader( handle, shader.get() );
	}
}

}  // namespace

namespace IECoreDelight
{

namespace ShaderNetworkAlgo
{

ShaderNetworkPtr preprocessedNetwork( const ShaderNetwork *shaderNetwork )
{
	ShaderNetworkPtr result = shaderNetwork->copy();

	IECoreScene::ShaderNetworkAlgo::expandSplines( result.get() );

	renameSplineParameters( result.get() );

	IECoreScene::ShaderNetworkAlgo::removeUnusedShaders( result.get() );

	return result;
}

}  // namespace ShaderNetworkAlgo

}  // namespace IECoreDelight