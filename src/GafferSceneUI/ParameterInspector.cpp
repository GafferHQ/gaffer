//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferSceneUI/Private/ParameterInspector.h"

#include "GafferSceneUI/Private/AttributeInspector.h"

#include "GafferScene/EditScopeAlgo.h"
#include "GafferScene/Light.h"
#include "GafferScene/LightFilter.h"
#include "GafferScene/ShaderAssignment.h"
#include "GafferScene/ShaderTweaks.h"

#include "Gaffer/OptionalValuePlug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Switch.h"

#include "boost/bind/bind.hpp"

#include "fmt/format.h"

using namespace boost::placeholders;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI::Private;

ParameterInspector::ParameterInspector(
	const GafferScene::ScenePlugPtr &scene, const Gaffer::PlugPtr &editScope,
	IECore::InternedString attribute, const IECoreScene::ShaderNetwork::Parameter &parameter
)
	: AttributeInspector( scene, editScope, attribute, parameter.name.string(), "parameter" ), m_parameter( parameter )
{

}

GafferScene::SceneAlgo::History::ConstPtr ParameterInspector::history() const
{
	// Computing histories is expensive, and there's no point doing it
	// if the specific attribute we want doesn't exist.
	if( !attributeExists() )
	{
		return nullptr;
	}

	return AttributeInspector::history();
}

IECore::ConstObjectPtr ParameterInspector::value( const GafferScene::SceneAlgo::History *history ) const
{
	auto attribute = AttributeInspector::value( history );
	auto shaderNetwork = runTimeCast<const ShaderNetwork>( attribute.get() );
	if( !shaderNetwork )
	{
		return nullptr;
	}

	const IECoreScene::Shader *shader = m_parameter.shader.string().empty() ? shaderNetwork->outputShader() : shaderNetwork->getShader( m_parameter.shader );
	if( !shader )
	{
		return nullptr;
	}

	return shader->parametersData()->member( m_parameter.name );
}

IECore::ConstObjectPtr ParameterInspector::fallbackValue( const GafferScene::SceneAlgo::History *history, std::string &description ) const
{
	// No fallback values are provided for parameters. Implemented to override AttributeInspector::fallbackValue().
	return nullptr;
}

Gaffer::ValuePlugPtr ParameterInspector::source( const GafferScene::SceneAlgo::History *history, std::string &editWarning ) const
{
	auto sceneNode = runTimeCast<SceneNode>( history->scene->node() );
	if( !sceneNode || history->scene != sceneNode->outPlug() )
	{
		return nullptr;
	}

	if( auto light = runTimeCast<Light>( sceneNode ) )
	{
		if( m_parameter.shader.string().empty() )
		{
			if( auto optionalPlug = light->parametersPlug()->getChild<OptionalValuePlug>( m_parameter.name ) )
			{
				return optionalPlug->enabledPlug()->getValue() ? optionalPlug : nullptr;
			}
			return light->parametersPlug()->descendant<ValuePlug>( m_parameter.name );
		}
		/// \todo Remove the need to search for a `ShaderPlug` by adding such a plug to
		/// `GafferScene::Light` itself.
		for( const auto &plug : Plug::Range( *light ) )
		{
			if( const auto shaderPlug = runTimeCast<ShaderPlug>( plug ) )
			{
				return shaderPlug->parameterSource( m_parameter );
			}
		}
	}
	else if( auto lightFilter = runTimeCast<LightFilter>( sceneNode ) )
	{
		return lightFilter->parametersPlug()->getChild<ValuePlug>( m_parameter.name );
	}
	else if( auto shaderAssignment = runTimeCast<ShaderAssignment>( sceneNode ) )
	{
		if( !(shaderAssignment->filterPlug()->match( shaderAssignment->inPlug() ) & PathMatcher::ExactMatch) )
		{
			return nullptr;
		}

		if( auto parameterPlug = shaderAssignment->shaderPlug()->parameterSource( m_parameter ) )
		{
			/// \todo This is overly conservative. We should test to see if there is more than
			/// one filter match (but make sure to early-out once two are found, rather than test
			/// the rest of the scene).
			const Node *shaderNode = parameterPlug->node();
			editWarning = fmt::format(
				"Edits to {} may affect other locations in the scene.",
				shaderNode->relativeName( shaderNode->scriptNode() )
			);
			return parameterPlug;
		}
	}
	else if( auto shaderTweaks = runTimeCast<ShaderTweaks>( sceneNode ) )
	{
		if( !(shaderTweaks->filterPlug()->match( shaderTweaks->inPlug() ) & PathMatcher::ExactMatch) )
		{
			return nullptr;
		}

		const std::string tweakName = (
			m_parameter.shader.string() +
			( m_parameter.shader.string().empty() ? "" : "." ) +
			m_parameter.name.string()
		);

		for( const auto &tweak : TweakPlug::Range( *shaderTweaks->tweaksPlug() ) )
		{
			if( tweak->namePlug()->getValue() == tweakName && tweak->enabledPlug()->getValue() )
			{
				return tweak;
			}
		}
	}

	return nullptr;
}

Inspector::AcquireEditFunctionOrFailure ParameterInspector::acquireEditFunction( Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history ) const
{
	auto attributeHistory = static_cast<const SceneAlgo::AttributeHistory *>( history );

	ConstObjectPtr v = value( history );
	if( !v )
	{
		return fmt::format( "Parameter \"{}\" does not exist.", m_parameter.name.string() );
	}

	const GraphComponent *readOnlyReason = EditScopeAlgo::parameterEditReadOnlyReason(
		editScope,
		history->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ),
		attributeHistory->attributeName,
		m_parameter
	);

	if( readOnlyReason )
	{
		// If we don't have an edit and the scope is locked, we error,
		// as we can't add an edit. Other cases where we already _have_
		// an edit will have been found by `source()`.
		return fmt::format(
			"{} is locked.",
			readOnlyReason->relativeName( readOnlyReason->ancestor<ScriptNode>() )
		);
	}
	else
	{
		return [
			editScope = EditScopePtr( editScope ),
			attributeName = attributeHistory->attributeName,
			context = attributeHistory->context,
			parameter = m_parameter
		] ( bool createIfNecessary ) {
				Context::Scope scope( context.get() );
				return EditScopeAlgo::acquireParameterEdit(
					editScope.get(),
					context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ),
					attributeName,
					parameter,
					createIfNecessary
				);
		};
	}
}
