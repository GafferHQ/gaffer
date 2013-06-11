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

#include "GafferScene/ShaderAssignment.h"
#include "GafferScene/Shader.h"

#include "Gaffer/Box.h"

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
	
	if( plug == shaderPlug() )
	{
		ConstPlugPtr sourcePlug = inputPlug->source<Plug>();
		if( sourcePlug->ancestor<Shader>() )
		{
			return true;
		}
		else if( sourcePlug->ancestor<Box>() )
		{
			// should also be able to accept the unconnected inputs and outputs
			// of boxes, so you can wrap shader assignments in boxes without
			// connecting the other side
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
		IECore::ObjectVectorPtr state = shader->state();
		result->members()["shader"] = state;
	}
	
	return result;
}
