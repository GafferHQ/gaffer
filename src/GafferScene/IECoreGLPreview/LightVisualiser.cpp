//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, John Haddon. All rights reserved.
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

#include "GafferScene/Private/IECoreGLPreview/LightVisualiser.h"

#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/Group.h"

#include "IECore/StringAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/container/flat_map.hpp"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreGLPreview;

//////////////////////////////////////////////////////////////////////////
// Internal implementation details
//////////////////////////////////////////////////////////////////////////

namespace
{

typedef std::pair<IECore::InternedString, IECore::InternedString> AttributeAndShaderNames;

typedef boost::container::flat_map<AttributeAndShaderNames, ConstLightVisualiserPtr> LightVisualisers;
LightVisualisers &lightVisualisers()
{
	static LightVisualisers l;
	return l;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// LightVisualiser class
//////////////////////////////////////////////////////////////////////////


LightVisualiser::LightVisualiser()
{
}

LightVisualiser::~LightVisualiser()
{
}

void LightVisualiser::registerLightVisualiser( const IECore::InternedString &attributeName, const IECore::InternedString &shaderName, ConstLightVisualiserPtr visualiser )
{
	lightVisualisers()[AttributeAndShaderNames( attributeName, shaderName )] = visualiser;
}

Visualisations LightVisualiser::allVisualisations( const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state )
{
	Visualisations resultVis;

	if( !attributes )
	{
		return resultVis;
	}

	IECoreGL::StatePtr resultState = nullptr;

	/// This seems pretty expensive to do everywhere.
	/// The alternative would be to register attribute visualisers to specific attributes.  But then we wouldn't be able to have a visualiser that is influenced by multiple attributes simultaneously
	for( IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().begin();
		it != attributes->members().end(); it++ )
	{
		const std::string &attributeName = it->first.string();
		if( !( boost::ends_with( attributeName, ":light" ) || attributeName == "light" ) )
		{
			continue;
		}

		const IECoreScene::ShaderNetwork *shaderNetwork = IECore::runTimeCast<const IECoreScene::ShaderNetwork>( it->second.get() );
		if( !shaderNetwork )
		{
			continue;
		}

		IECore::InternedString shaderName;
		if( const IECoreScene::Shader *shader = shaderNetwork->outputShader() )
		{
			shaderName = shader->getName();
		}

		if( shaderName.string().empty() )
		{
			continue;
		}

		const LightVisualiser *visualiser = nullptr;

		const LightVisualisers &l = lightVisualisers();
		LightVisualisers::const_iterator visIt = l.find( AttributeAndShaderNames( it->first, shaderName ) );
		if( visIt != l.end() )
		{
			visualiser = visIt->second.get();
		}
		else
		{
			// Direct lookup failed. See if we have any wildcard matches.
			// We assume that the number of registered visualisers is small
			// enough that linear search is OK here.

			// First look for wildcards in shader names only, this ensures
			// "ai:light *" beats "*:light *" even if iterated after it.
			for( auto &r : l )
			{
				if( it->first == r.first.first && StringAlgo::matchMultiple( shaderName, r.first.second ) )
				{
					visualiser = r.second.get();
					break;
				}
			}

			// Then check look for wildcards in attribute names too if that failed
			if( !visualiser )
			{
				for( auto &r : l )
				{
					if( StringAlgo::matchMultiple( it->first, r.first.first ) && StringAlgo::matchMultiple( shaderName, r.first.second ) )
					{
						visualiser = r.second.get();
						break;
					}
				}
			}
		}

		if( !visualiser )
		{
			continue;
		}

		IECoreGL::ConstStatePtr curState = nullptr;
		const Visualisations curVis = visualiser->visualise( it->first, shaderNetwork, attributes, curState );

		if( !curVis.empty() )
		{
			Private::collectVisualisations( curVis, resultVis );
		}

		if( curState )
		{
			if( !resultState )
			{
				resultState = new IECoreGL::State( false );
			}
			resultState->add( const_cast<IECoreGL::State*>( curState.get() ) );
		}
	}

	state = resultState;
	return resultVis;
}
