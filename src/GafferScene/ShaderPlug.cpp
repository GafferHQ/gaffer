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

#include "GafferScene/ShaderPlug.h"

#include "GafferScene/Shader.h"

#include "Gaffer/BoxIO.h"
#include "Gaffer/Context.h"
#include "Gaffer/ContextProcessor.h"
#include "Gaffer/Dot.h"
#include "Gaffer/Loop.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Spreadsheet.h"
#include "Gaffer/SubGraph.h"
#include "Gaffer/Switch.h"

#include "IECoreScene/ShaderNetwork.h"

#include "IECore/MurmurHash.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

bool isShaderOutPlug( const Plug *plug )
{
	auto shader = runTimeCast<const Shader>( plug->node() );
	if( !shader )
	{
		return false;
	}
	const Plug *outPlug = shader->outPlug();
	if( !outPlug )
	{
		return false;
	}
	return plug == shader->outPlug() || shader->outPlug()->isAncestorOf( plug );
}

bool isParameterType( const Plug *plug )
{
	switch( (int)plug->typeId() )
	{
		case PlugTypeId :      // These two could be used to represent
		case ValuePlugTypeId : // struct parameters
		case FloatPlugTypeId :
		case IntPlugTypeId :
		case StringPlugTypeId :
		case V2fPlugTypeId :
		case V3fPlugTypeId :
		case V2iPlugTypeId :
		case V3iPlugTypeId :
		case Color3fPlugTypeId :
		case Color4fPlugTypeId :
		case M33fPlugTypeId :
		case M44fPlugTypeId :
		case BoolPlugTypeId :
			return true;
		default :
			// Use typeName query to avoid hard dependency on
			// GafferOSL. It may be that we should move ClosurePlug
			// to GafferScene anyway.
			return plug->isInstanceOf( "GafferOSL::ClosurePlug" );
	}
}

const IECore::InternedString hasProxyNodesIdentifier( "__hasProxyNodes" );
const IECore::InternedString g_out( "out" );

} // namespace

//////////////////////////////////////////////////////////////////////////
// ShaderPlug
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( ShaderPlug );

ShaderPlug::ShaderPlug( const std::string &name, Direction direction, unsigned flags )
	:	Plug( name, direction, flags )
{
}

ShaderPlug::~ShaderPlug()
{
}

bool ShaderPlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	return false;
}

Gaffer::PlugPtr ShaderPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new ShaderPlug( name, direction, getFlags() );
}

bool ShaderPlug::acceptsInput( const Gaffer::Plug *input ) const
{
	if( !Plug::acceptsInput( input ) )
	{
		return false;
	}

	if( !input )
	{
		return true;
	}

	// We only want to accept connections from the output
	// plug of a shader.
	const Plug *sourcePlug = input->source();
	if( isShaderOutPlug( sourcePlug ) )
	{
		return true;
	}

	// But we also accept intermediate connections from
	// other ShaderPlugs, knowing that they will apply
	// the same rules when they have their input set.
	if( runTimeCast<const ShaderPlug>( sourcePlug ) )
	{
		return true;
	}

	// We also allow a bunch of general-purpose nodes below, but there are
	// certain plug types we know a shader can never be connected to. Reject
	// those, otherwise stupid things happen, like the ShaderView trying to
	// display scenes and images.

	if( !isParameterType( sourcePlug ) )
	{
		return false;
	}

	// Allow nodes we handle using `PlugAlgo::contextSensitiveSource()` in
	// `sourceShader()`.

	const Node *sourceNode = sourcePlug->node();
	if( auto switchNode = runTimeCast<const Switch>( sourceNode ) )
	{
		if(
			sourcePlug == switchNode->outPlug() ||
			( switchNode->outPlug() && switchNode->outPlug()->isAncestorOf( sourcePlug ) ) ||
			sourcePlug->parent() == switchNode->inPlugs()
		)
		{
			// Reject switches which have inputs from non-shader nodes.
			for( Plug::Iterator it( switchNode->inPlugs() ); !it.done(); ++it )
			{
				if( (*it)->getInput() && !isShaderOutPlug( (*it)->source() ) )
				{
					return false;
				}
			}
			return true;
		}
	}
	else if(
		runTimeCast<const ContextProcessor>( sourceNode ) ||
		runTimeCast<const Loop>( sourceNode ) ||
		runTimeCast<const Spreadsheet>( sourceNode )
	)
	{
		/// \todo Ideally we'd also check that `sourceNode.in` doesn't have an
		/// input that we can't accept ourselves. But there's nothing stopping
		/// someone connecting one later even if there isn't one now, so we just
		/// have to reject them later in `sourceShader()` instead. The only
		/// reason we can do it for Switch (above) is that Switch overrides
		/// `acceptsInput()` in a way that would reject the later connection.
		auto sourceNodeOut = sourceNode->getChild<Plug>( g_out );
		return sourceNodeOut && ( sourcePlug == sourceNodeOut || sourceNodeOut->isAncestorOf( sourcePlug ) );
	}

	// We must accept intermediate connections from plugs on utility nodes on the
	// assumption that they will later be connected to a shader. Once we're connected
	// to `sourcePlug`, we'll be consulted about any inputs it will receive, so we
	// can reject non-shaders then.

	if(
		runTimeCast<const SubGraph>( sourceNode ) ||
		runTimeCast<const Dot>( sourceNode ) ||
		runTimeCast<const BoxIO>( sourceNode )
	)
	{
		return true;
	}

	return false;
}

struct ShaderPlug::ShaderContext
{

	ConstContextPtr context;
	std::optional<Context::Scope> scope;
	std::string outputParameter;
	std::optional<Context::EditableScope> editableScope;

};

IECore::MurmurHash ShaderPlug::attributesHash() const
{
	IECore::MurmurHash h;
	ShaderContext context;
	const Gaffer::Plug *plug = shaderOutPlug( context );
	if( plug )
	{
		auto shader = static_cast<const Shader*>( plug->node() );
		h = shader->outAttributesPlug()->hash();
	}

	return h;
}

IECore::ConstCompoundObjectPtr ShaderPlug::attributes() const
{
	ShaderContext context;
	const Gaffer::Plug *plug = shaderOutPlug( context );
	if( plug )
	{
		auto shader = static_cast<const Shader*>( plug->node() );
		IECore::ConstCompoundObjectPtr result = shader->outAttributesPlug()->getValue();

		// Check for outputs from ShaderTweakProxy, which should only be used with ShaderTweaks nodes
		for( const auto &i : result->members() )
		{
			if( const IECoreScene::ShaderNetwork *shaderNetwork = IECore::runTimeCast< const IECoreScene::ShaderNetwork >( i.second.get() ) )
			{
				if( const BoolData *hasProxyNodes = shaderNetwork->blindData()->member<IECore::BoolData>( hasProxyNodesIdentifier ) )
				{
					if( hasProxyNodes->readable() )
					{
						throw IECore::Exception(
							"ShaderTweakProxy only works with ShaderTweaks - it doesn't make sense to connect one here"
						);

					}
				}
			}
		}

		return result;
	}

	return new CompoundObject;
}

const Gaffer::ValuePlug *ShaderPlug::parameterSource( const IECoreScene::ShaderNetwork::Parameter &parameter) const
{
	ShaderContext context;
	const Gaffer::Plug *plug = shaderOutPlug( context );

	if( plug )
	{
		auto shader = static_cast<const Shader*>( plug->node() );
		if( parameter.shader.string().empty() )
		{
			return shader->parametersPlug()->descendant<ValuePlug>( parameter.name );
		}
		return shader->parameterSource( plug, parameter );
	}
	return nullptr;
}

Gaffer::ValuePlug *ShaderPlug::parameterSource( const IECoreScene::ShaderNetwork::Parameter &parameter)
{
	return const_cast<ValuePlug *>( const_cast<const ShaderPlug *>( this )->parameterSource( parameter ) );
}

const Gaffer::Plug *ShaderPlug::shaderOutPlug( ShaderContext &shaderContext ) const
{
	auto [source, context] = PlugAlgo::contextSensitiveSource( this );
	if( source == this )
	{
		// No input
		return nullptr;
	}

	auto shader = runTimeCast<const GafferScene::Shader>( source->node() );
	if( !shader )
	{
		return nullptr;
	}

	const Plug *shaderOutPlug = shader->outPlug();
	if(
		!shaderOutPlug ||
		( source != shaderOutPlug && !shaderOutPlug->isAncestorOf( source ) )
	)
	{
		return nullptr;
	}

	if( source != shaderOutPlug )
	{
		shaderContext.editableScope.emplace( context.get() );
		shaderContext.outputParameter = source->relativeName( shaderOutPlug );
		shaderContext.editableScope->set( Shader::g_outputParameterContextName, &shaderContext.outputParameter );
	}
	else if( context != Context::current() )
	{
		shaderContext.context = context;
		shaderContext.scope.emplace( context.get() );
	}

	return source;
}
