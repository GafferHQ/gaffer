//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "IECore/SimpleTypedData.h"
#include "IECore/WorldBlock.h"

#include "Gaffer/Context.h"

#include "GafferScene/ScenePlug.h"
#include "GafferScene/SceneProcedural.h"
#include "GafferScene/ExecutableRender.h"
#include "GafferScene/RendererAlgo.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( ExecutableRender );

size_t ExecutableRender::g_firstPlugIndex = 0;

ExecutableRender::ExecutableRender( const std::string &name )
	:	ExecutableNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in" ) );
}

ExecutableRender::~ExecutableRender()
{
}

ScenePlug *ExecutableRender::inPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *ExecutableRender::inPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

IECore::MurmurHash ExecutableRender::hash( const Gaffer::Context *context ) const
{
	const ScenePlug *scenePlug = inPlug()->source<ScenePlug>();
	if ( scenePlug == inPlug() )
	{
		return IECore::MurmurHash();
	}
	
	Context::Scope scope( context );
	IECore::MurmurHash h = ExecutableNode::hash( context );
	/// \todo hash the actual scene when we have a hierarchyHash
	h.append( (uint64_t)scenePlug );
	
	std::vector<IECore::InternedString> names;
	context->names( names );
	for ( std::vector<IECore::InternedString>::const_iterator it = names.begin(); it != names.end(); ++it )
	{
		if ( it->string().compare( 0, 3, "ui:" ) )
		{
			h.append( *it );
			if ( const IECore::Data *data = context->get<const IECore::Data>( *it ) )
			{
				data->hash( h );
			}
		}
	}
	
	return h;
}

void ExecutableRender::execute() const
{
	const ScenePlug *scene = inPlug()->getInput<ScenePlug>();
	if( !scene )
	{
		throw IECore::Exception( "No input scene" );
	}
	
	ConstCompoundObjectPtr globals = scene->globalsPlug()->getValue();
	
	createDisplayDirectories( globals.get() );
	
	IECore::RendererPtr renderer = createRenderer();		
	outputOptions( globals.get(), renderer.get() );
	outputCamera( scene, globals.get(), renderer.get() );
	{
		WorldBlock world( renderer );
		
		outputCoordinateSystems( scene, globals.get(), renderer.get() );
		outputLights( scene, globals.get(), renderer.get() );
		outputWorldProcedural( scene, renderer.get() );
	}
	
	std::string systemCommand = command();
	if( systemCommand.size() )
	{
		int result = system( systemCommand.c_str() );
		if( result )
		{
			throw Exception( "System command failed" );
		}
	}
}

void ExecutableRender::outputWorldProcedural( const ScenePlug *scene, IECore::Renderer *renderer ) const
{
	renderer->procedural( new SceneProcedural( scene, Context::current() ) );
}

std::string ExecutableRender::command() const
{
	return "";
}
