//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/ShaderTweaks.h"

#include "GafferScene/Shader.h"

#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/TweakPlug.h"
#include "Gaffer/ValuePlug.h"

#include "IECoreScene/Shader.h"
#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/SimpleTypedData.h"
#include "IECore/StringAlgo.h"

#include "fmt/format.h"

#include <unordered_map>

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

std::pair<const GafferScene::Shader *, const Gaffer::Plug *> shaderOutput( const Gaffer::TweakPlug *tweakPlug )
{
	const Plug *source = tweakPlug->valuePlug()->source();
	if( source != tweakPlug->valuePlug() )
	{
		if( auto shader = runTimeCast<const GafferScene::Shader>( source->node() ) )
		{
			if( source == shader->outPlug() || shader->outPlug()->isAncestorOf( source ) )
			{
				return { shader, source };
			}
		}
	}
	return { nullptr, nullptr };
}

}  // namespace

GAFFER_NODE_DEFINE_TYPE( ShaderTweaks );

size_t ShaderTweaks::g_firstPlugIndex = 0;

ShaderTweaks::ShaderTweaks( const std::string &name )
	:	AttributeProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "shader" ) );
	addChild( new BoolPlug( "ignoreMissing", Plug::In, false ) );
	addChild( new TweaksPlug( "tweaks" ) );
	addChild( new BoolPlug( "localise", Plug::In, false ) );
}

ShaderTweaks::~ShaderTweaks()
{
}

Gaffer::StringPlug *ShaderTweaks::shaderPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *ShaderTweaks::shaderPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *ShaderTweaks::ignoreMissingPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *ShaderTweaks::ignoreMissingPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::TweaksPlug *ShaderTweaks::tweaksPlug()
{
	return getChild<Gaffer::TweaksPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::TweaksPlug *ShaderTweaks::tweaksPlug() const
{
	return getChild<Gaffer::TweaksPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *ShaderTweaks::localisePlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *ShaderTweaks::localisePlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 3 );
}

bool ShaderTweaks::affectsProcessedAttributes( const Gaffer::Plug *input ) const
{
	return
		AttributeProcessor::affectsProcessedAttributes( input ) ||
		tweaksPlug()->isAncestorOf( input ) ||
		input == shaderPlug() ||
		input == ignoreMissingPlug() ||
		input == localisePlug()
	;
}

void ShaderTweaks::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( tweaksPlug()->children().empty() )
	{
		h = inPlug()->attributesPlug()->hash();
	}
	else
	{
		AttributeProcessor::hashProcessedAttributes( path, context, h );
		shaderPlug()->hash( h );
		tweaksPlug()->hash( h );
		ignoreMissingPlug()->hash( h );
		localisePlug()->hash( h );

		for( auto &tweak : TweakPlug::Range( *tweaksPlug() ) )
		{
			const auto shaderOutput = ::shaderOutput( tweak.get() );
			if( shaderOutput.first )
			{
				shaderOutput.first->attributesHash( shaderOutput.second, h );
			}
		}

		if( localisePlug()->getValue() )
		{
			h.append( inPlug()->fullAttributesHash( path ) );
		}
	}
}

IECore::ConstCompoundObjectPtr ShaderTweaks::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, const IECore::CompoundObject *inputAttributes ) const
{
	const string shader = shaderPlug()->getValue();
	if( shader.empty() )
	{
		return inputAttributes;
	}

	const TweaksPlug *tweaksPlug = this->tweaksPlug();
	if( tweaksPlug->children().empty() )
	{
		return inputAttributes;
	}

	const bool ignoreMissing = ignoreMissingPlug()->getValue();

	CompoundObjectPtr result = new CompoundObject;
	result->members() = inputAttributes->members();
	CompoundObject::ObjectMap &out = result->members();

	// We switch our source attributes depending on whether we are
	// localising inherited shaders or just using the ones at the location.

	const CompoundObject::ObjectMap *source = &inputAttributes->members();

	// If we're using fullAttributes, we need to keep them alive.
	ConstCompoundObjectPtr fullAttributes;
	if( localisePlug()->getValue() )
	{
		fullAttributes = inPlug()->fullAttributes( path );
		source = &fullAttributes->members();
	}

	for( const auto &attribute : *source )
	{
		if( !StringAlgo::matchMultiple( attribute.first, shader ) )
		{
			continue;
		}

		const ShaderNetwork *network = runTimeCast<const ShaderNetwork>( attribute.second.get() );
		if( !network )
		{
			continue;
		}

		ShaderNetworkPtr tweakedNetwork = network->copy();
		if( applyTweaks( tweakedNetwork.get(), ignoreMissing ? TweakPlug::MissingMode::Ignore : TweakPlug::MissingMode::Error ) )
		{
			out[attribute.first] = tweakedNetwork;
		}
	}

	return result;
}

bool ShaderTweaks::applyTweaks( IECoreScene::ShaderNetwork *shaderNetwork, TweakPlug::MissingMode missingMode ) const
{
	unordered_map<InternedString, IECoreScene::ShaderPtr> modifiedShaders;

	const Plug *tweaksPlug = this->tweaksPlug();

	bool appliedTweaks = false;
	bool removedConnections = false;
	for( const auto &tweakPlug : TweakPlug::Range( *tweaksPlug ) )
	{
		const std::string name = tweakPlug->namePlug()->getValue();
		if( name.empty() )
		{
			continue;
		}

		if( !tweakPlug->enabledPlug()->getValue() )
		{
			continue;
		}

		ShaderNetwork::Parameter parameter;
		size_t dotPos = name.find_last_of( '.' );
		if( dotPos == string::npos )
		{
			parameter.shader = shaderNetwork->getOutput().shader;
			parameter.name = name;
		}
		else
		{
			parameter.shader = InternedString( name.c_str(), dotPos );
			parameter.name = InternedString( name.c_str() + dotPos + 1 );
		}

		const IECoreScene::Shader *shader = shaderNetwork->getShader( parameter.shader );
		if( !shader )
		{
			if( missingMode != TweakPlug::MissingMode::Ignore )
			{
				throw IECore::Exception( fmt::format(
					"Cannot apply tweak \"{}\" because shader \"{}\" does not exist",
					name, parameter.shader.string()
				) );
			}
			else
			{
				continue;
			}
		}

		const TweakPlug::Mode mode = static_cast<TweakPlug::Mode>( tweakPlug->modePlug()->getValue() );

		if( auto input = shaderNetwork->input( parameter )  )
		{
			if( mode != TweakPlug::Mode::Replace )
			{
				throw IECore::Exception( fmt::format( "Cannot apply tweak to \"{}\" : Mode must be \"Replace\" when a previous connection exists", name ) );
			}
			shaderNetwork->removeConnection( { input, parameter } );
			removedConnections = true;
		}

		const auto shaderOutput = ::shaderOutput( tweakPlug.get() );
		if( shaderOutput.first )
		{
			// New connection
			ConstCompoundObjectPtr shaderAttributes = shaderOutput.first->attributes( shaderOutput.second );
			const ShaderNetwork *inputNetwork = nullptr;
			for( const auto &a : shaderAttributes->members() )
			{
				if( ( inputNetwork = runTimeCast<const ShaderNetwork>( a.second.get() ) ) )
				{
					break;
				}
			}

			if( inputNetwork && inputNetwork->getOutput() )
			{
				if( mode != TweakPlug::Mode::Replace )
				{
					throw IECore::Exception( fmt::format( "Cannot apply tweak to \"{}\" : Mode must be \"Replace\" when inserting a connection", name ) );
				}
				const auto inputParameter = ShaderNetworkAlgo::addShaders( shaderNetwork, inputNetwork );
				shaderNetwork->addConnection( { inputParameter, parameter } );
				appliedTweaks = true;
			}
		}
		else
		{
			// Regular tweak
			auto modifiedShader = modifiedShaders.insert( { parameter.shader, nullptr } );
			if( modifiedShader.second )
			{
				modifiedShader.first->second = shader->copy();
			}

			if(
				tweakPlug->applyTweak(
					[&parameter, &modifiedShader]( const std::string &valueName )
					{
						return modifiedShader.first->second->parametersData()->member( parameter.name );
					},
					[&parameter, &modifiedShader]( const std::string &valueName, DataPtr newData )
					{
						if( newData )
						{
							modifiedShader.first->second->parameters()[parameter.name] = newData;
							return true;
						}
						else
						{
							return static_cast<bool>(
								modifiedShader.first->second->parameters().erase( parameter.name )
							);
						}
					},
					missingMode
				)
			)
			{
				appliedTweaks = true;
			}
		}
	}

	for( auto &x : modifiedShaders )
	{
		shaderNetwork->setShader( x.first, std::move( x.second ) );
	}

	if( removedConnections )
	{
		ShaderNetworkAlgo::removeUnusedShaders( shaderNetwork );
	}

	return appliedTweaks || removedConnections;
}
