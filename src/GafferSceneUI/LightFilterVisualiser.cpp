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

#include "boost/container/flat_map.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string.hpp"

#include "IECore/Light.h"
#include "IECore/Shader.h"

#include "IECoreGL/Group.h"
#include "IECoreGL/Primitive.h"

#include "GafferSceneUI/LightFilterVisualiser.h"
#include "GafferSceneUI/AttributeVisualiser.h"

using namespace std;
using namespace Imath;
using namespace GafferSceneUI;

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

/// Class for visualisation of light filters. All light filters in Gaffer are represented
/// as IECore::Shader objects, but we need to visualise them differently
/// depending on their shader name (accessed using `IECore::Shader::getName()`). A
/// factory mechanism is provided to map from this type to a specialised
/// LightFilterVisualiser.
class AttributeVisualiserForLightFilters : public AttributeVisualiser
{

	public :

		IE_CORE_DECLAREMEMBERPTR( AttributeVisualiserForLightFilters )

		/// Uses a custom visualisation registered via `registerLightFilterVisualiser()` if one
		/// is available, if not falls back to a basic visualisation.
		virtual IECoreGL::ConstRenderablePtr visualise( const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const;

	protected :

		static AttributeVisualiser::AttributeVisualiserDescription<AttributeVisualiserForLightFilters> g_visualiserDescription;

};

} // namespace

IECoreGL::ConstRenderablePtr AttributeVisualiserForLightFilters::visualise( const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const
{
	if( !attributes )
	{
		return nullptr;
	}

	IECoreGL::GroupPtr resultGroup = nullptr;
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

		const IECore::ObjectVector *filterShaderVector = IECore::runTimeCast<const IECore::ObjectVector>( it.second.get() );
		if( !filterShaderVector || filterShaderVector->members().empty() )
		{
			continue;
		}

		IECore::InternedString filterShaderName;
		if( const IECore::Shader *filterShader = IECore::runTimeCast<const IECore::Shader>( filterShaderVector->members().back().get() ) )
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
		auto lightIt = attributes->members().find( tokens.front() + ":light" );

		if( lightIt == attributes->members().end() )
		{
			continue;
		}

		const IECore::ObjectVector *lightShaderVector = IECore::runTimeCast<const IECore::ObjectVector>( lightIt->second.get() );
		if( !lightShaderVector || lightShaderVector->members().empty() )
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
		IECoreGL::ConstRenderablePtr curVis = visualiser->visualise( attributeName, filterShaderVector, lightShaderVector, curState );

		if( curVis )
		{
			if( !resultGroup )
			{
				resultGroup = new IECoreGL::Group();
			}
			// resultGroup will be returned as const, so const-casting the children in order to add them is safe
			resultGroup->addChild( const_cast<IECoreGL::Renderable*>( curVis.get() ) );
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
	return resultGroup;
}

AttributeVisualiser::AttributeVisualiserDescription<AttributeVisualiserForLightFilters> AttributeVisualiserForLightFilters::g_visualiserDescription;

//////////////////////////////////////////////////////////////////////////
// LightVisualiser class
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
