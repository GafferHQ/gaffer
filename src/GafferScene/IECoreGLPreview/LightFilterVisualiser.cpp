//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine. All rights reserved.
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

#include "GafferScene/Private/IECoreGLPreview/LightFilterVisualiser.h"

#include "GafferScene/Private/IECoreGLPreview/AttributeVisualiser.h"

#include "IECoreGL/Group.h"
#include "IECoreGL/Primitive.h"

#include "IECoreScene/Shader.h"

#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/container/flat_map.hpp"

using namespace std;
using namespace Imath;
using namespace IECoreGLPreview;

//////////////////////////////////////////////////////////////////////////
// Internal implementation details
//////////////////////////////////////////////////////////////////////////

namespace
{

typedef std::pair<IECore::InternedString, IECore::InternedString> AttributeAndShaderNames;

typedef boost::container::flat_map<AttributeAndShaderNames, ConstLightFilterVisualiserPtr> LightFilterVisualisers;
LightFilterVisualisers &lightFilterVisualisers()
{
	static LightFilterVisualisers l;
	return l;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// LightFilterVisualiser class
//////////////////////////////////////////////////////////////////////////


LightFilterVisualiser::LightFilterVisualiser()
{
}

LightFilterVisualiser::~LightFilterVisualiser()
{
}

void LightFilterVisualiser::registerLightFilterVisualiser( const IECore::InternedString &attributeName, const IECore::InternedString &shaderName, ConstLightFilterVisualiserPtr visualiser )
{
	lightFilterVisualisers()[AttributeAndShaderNames( attributeName, shaderName )] = visualiser;
}

Visualisations LightFilterVisualiser::allVisualisations( const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state )
{
	Visualisations resultVis;

	if( !attributes )
	{
		return resultVis;
	}

	IECoreGL::StatePtr resultState = nullptr;

	/// This seems pretty expensive to do everywhere.
	/// The alternative would be to register attribute visualisers to specific attributes.
	/// But then we wouldn't be able to have a visualiser that is influenced by multiple attributes simultaneously
	for( const auto& it : attributes->members() )
	{
		const std::string &attributeName = it.first.string();
		if( attributeName.find( ":lightFilter" ) == std::string::npos )
		{
			continue;
		}

		const IECoreScene::ShaderNetwork *filterShaderNetwork = IECore::runTimeCast<const IECoreScene::ShaderNetwork>( it.second.get() );
		if( !filterShaderNetwork )
		{
			continue;
		}

		IECore::InternedString filterShaderName;
		if( const IECoreScene::Shader *filterShader = filterShaderNetwork->outputShader() )
		{
			filterShaderName = filterShader->getName();
		}

		if( filterShaderName.string().empty() )
		{
			continue;
		}

		// find the light shader influenced by the filter

		std::vector<std::string> tokens;
		boost::split( tokens, attributeName, boost::is_any_of(":") );
		const IECoreScene::ShaderNetwork *lightShaderNetwork = attributes->member<IECoreScene::ShaderNetwork>( tokens.front() + ":light" );

		// It's possible that we found a light filter defined in world space
		// that isn't assigned to a light just yet. If we found a filter in
		// light space it must have a valid light shader, though.
		if( lightShaderNetwork && !lightShaderNetwork->outputShader() )
		{
			continue;
		}

		const LightFilterVisualisers &l = lightFilterVisualisers();

		// light filters are stored in attributes following this syntax:
		// renderer:lightFilter:optionalName. Visualisers get registered to
		// renderer:lightFilter only, though. It's therefore necessary to strip off
		// the optional part
		std::string attrLookup = tokens[0] + ":" + tokens[1];

		const LightFilterVisualiser *visualiser = nullptr;
		auto visIt = l.find( AttributeAndShaderNames( attrLookup, filterShaderName ) );
		if( visIt != l.end() )
		{
			visualiser = visIt->second.get();
		}
		else
		{
			continue;
		}

		IECoreGL::ConstStatePtr curState = nullptr;
		const Visualisations curVis = visualiser->visualise( attributeName, filterShaderNetwork, lightShaderNetwork, attributes, curState );

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
