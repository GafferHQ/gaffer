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
#include "Gaffer/Dot.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/SubGraph.h"
#include "Gaffer/Switch.h"

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
	return false;
}

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

	// And we support switches by traversing across them
	// ourselves when necessary, in `shaderOutPlug()`.

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
			for( PlugIterator it( switchNode->inPlugs() ); !it.done(); ++it )
			{
				if( (*it)->getInput() && !isShaderOutPlug( (*it)->source() ) )
				{
					return false;
				}
			}
			// For switches without any inputs, we have to assume that
			// the user might connect a shader in the future. But there
			// are certain plug types we know a shader can never be connected
			// to. Reject those, otherwise stupid things happen, like the
			// ShaderView trying to display scenes and images.
			if( !isParameterType( sourcePlug ) )
			{
				return false;
			}
			return true;
		}
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
		if( isParameterType( sourcePlug ) )
		{
			return true;
		}
	}

	return false;
}

IECore::MurmurHash ShaderPlug::attributesHash() const
{
	IECore::MurmurHash h;
	if( const Gaffer::Plug *p = shaderOutPlug() )
	{
		if( auto s = runTimeCast<const GafferScene::Shader>( p->node() ) )
		{
			Context::EditableScope scope( Context::current() );
			if( p != s->outPlug() )
			{
				scope.set( Shader::g_outputParameterContextName, p->relativeName( s->outPlug() ) );
			}
			h = s->outAttributesPlug()->hash();
		}
	}

	return h;
}

IECore::ConstCompoundObjectPtr ShaderPlug::attributes() const
{
	if( const Gaffer::Plug *p = shaderOutPlug() )
	{
		if( auto s = runTimeCast<const GafferScene::Shader>( p->node() ) )
		{
			Context::EditableScope scope( Context::current() );
			if( p != s->outPlug() )
			{
				scope.set( Shader::g_outputParameterContextName, p->relativeName( s->outPlug() ) );
			}
			return s->outAttributesPlug()->getValue();
		}
	}
	return new CompoundObject;
}

const Gaffer::Plug *ShaderPlug::shaderOutPlug() const
{
	const Plug *source = this->source<Gaffer::Plug>();
	if( source == this )
	{
		// No input
		return nullptr;
	}

	if( auto switchNode = runTimeCast<const Switch>( source->node() ) )
	{
		// Special case for switches with context-varying index values.
		// Query the active input for this context, and manually traverse
		// out the other side.
		/// \todo Perhaps we should support ContextProcessors in the same way?
		/// We have a similar pattern now in ShaderPlug, Shader::NetworkBuilder
		/// and Dispatcher. Perhaps the logic should be consolidated into a
		/// `PlugAlgo::computedSource()` utility of some sort?
		if( const Plug *activeInPlug = switchNode->activeInPlug( source ) )
		{
			source = activeInPlug->source();
		}
	}

	return source;
}
