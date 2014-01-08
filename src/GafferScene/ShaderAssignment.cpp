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

	/// \todo This currently only works if the incoming shader connection is from
	/// a Plug (and not a Color3fPlug or something of that sort). This covers us for
	/// RenderManShaders and OpenGLShaders, but not for ArnoldShaders. The problem is
	/// that dirtiness propagates along the leaf plugs (r,g,b) and not along the parent,
	/// and we only have a connection from the parent. The leaf propagation rule was devised
	/// with ComputeNodes in mind (where computation must occur at the leaf levels) so perhaps
	/// we'll be able to relax the rule for non-ComputeNodes like this one.
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
		// of boxes, so you can wrap shader assignments in boxes
		// prior to connecting the other side. the same goes for
		// shader switches - if a connection source is a switch,
		// then that means the switch hasn't had a shader connected
		// into it yet, but we'd still like to accept the connection
		// in anticipation of a shader being connected later.
		if(
			runTimeCast<const Shader>( sourceNode ) ||
			runTimeCast<const Box>( sourceNode ) ||
			runTimeCast<const ShaderSwitch>( sourceNode )
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
		shader->stateHash( h );
	}
}
		
IECore::ConstCompoundObjectPtr ShaderAssignment::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputAttributes ) const
{
	CompoundObjectPtr result = inputAttributes->copy();
	
	const Shader *shader = shaderPlug()->source<Plug>()->ancestor<Shader>();
	if( shader )
	{
		// Shader::state() returns a const object, so that in the future it may
		// come from a cached value. we're putting it into our result which, once
		// returned, will also be treated as const and cached. for that reason the
		// temporary const_cast needed to put it into the result is justified -
		// we never change the object and nor can anyone after it is returned.
		ObjectVectorPtr state = constPointerCast<ObjectVector>( shader->state() );
		if( state->members().size() )
		{
			result->members()["shader"] = state;
		}
	}
	
	return result;
}
