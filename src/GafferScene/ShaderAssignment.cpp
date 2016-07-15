//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Box.h"
#include "Gaffer/Dot.h"

#include "GafferScene/ShaderAssignment.h"
#include "GafferScene/Shader.h"
#include "GafferScene/ShaderSwitch.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( ShaderAssignment );

size_t ShaderAssignment::g_firstPlugIndex = 0;

ShaderAssignment::ShaderAssignment( const std::string &name )
	:	SceneElementProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new Plug( "shader" ) );

	// Fast pass-throughs for the things we don't alter.
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
}

ShaderAssignment::~ShaderAssignment()
{
}

Gaffer::Plug *ShaderAssignment::shaderPlug()
{
	return getChild<Plug>( g_firstPlugIndex );
}

const Gaffer::Plug *ShaderAssignment::shaderPlug() const
{
	return getChild<Plug>( g_firstPlugIndex );
}

void ShaderAssignment::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( input == shaderPlug() )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

bool ShaderAssignment::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !SceneElementProcessor::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( !inputPlug )
	{
		return true;
	}

	if( plug == shaderPlug() )
	{
		const Node *sourceNode = inputPlug->source<Plug>()->node();
		// we only really want to accept connections from
		// shaders, because we can't assign anything else.
		// but we also accept the unconnected inputs and outputs
		// of subgraphs, so you can wrap shader assignments in boxes
		// prior to connecting the other side. the same goes for
		// shader switches - if a connection source is a switch,
		// then that means the switch hasn't had a shader connected
		// into it yet, but we'd still like to accept the connection
		// in anticipation of a shader being connected later.
		if(
			runTimeCast<const Shader>( sourceNode ) ||
			runTimeCast<const SubGraph>( sourceNode ) ||
			runTimeCast<const ShaderSwitch>( sourceNode ) ||
			runTimeCast<const Dot>( sourceNode )
		)
		{
			return true;
		}
		return false;
	}
	return true;
}

bool ShaderAssignment::processesAttributes() const
{
	return true;
}

void ShaderAssignment::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const Shader *shader = shaderPlug()->source<Plug>()->ancestor<Shader>();
	if( shader )
	{
		shader->attributesHash( h );
	}
}

IECore::ConstCompoundObjectPtr ShaderAssignment::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputAttributes ) const
{
	const Shader *shader = shaderPlug()->source<Plug>()->ancestor<Shader>();
	if( !shader )
	{
		return inputAttributes;
	}

	ConstCompoundObjectPtr attributes = shader->attributes();
	if( attributes->members().empty() )
	{
		return inputAttributes;
	}

	CompoundObjectPtr result = new CompoundObject;
	// Since we're not going to modify any existing members (only add new ones),
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. Be careful not to modify
	// them though!
	result->members() = inputAttributes->members();
	for( CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; ++it )
	{
		result->members()[it->first] = it->second;
	}

	return result;
}
