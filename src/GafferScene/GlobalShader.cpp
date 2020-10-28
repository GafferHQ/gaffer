//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, John Haddon. All rights reserved.
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

#include "GafferScene/GlobalShader.h"

#include "GafferScene/ShaderPlug.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( GlobalShader );

size_t GlobalShader::g_firstPlugIndex = 0;

GlobalShader::GlobalShader( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ShaderPlug( "shader" ) );
}

GlobalShader::~GlobalShader()
{
}

ShaderPlug *GlobalShader::shaderPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

const ShaderPlug *GlobalShader::shaderPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

void GlobalShader::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( input == shaderPlug() || affectsOptionName( input ) )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void GlobalShader::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( shaderPlug()->attributesHash() );
	hashOptionName( context, h );
}

IECore::ConstCompoundObjectPtr GlobalShader::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{
	ConstCompoundObjectPtr attributes = shaderPlug()->attributes();
	if( attributes->members().empty() )
	{
		return inputGlobals;
	}

	if( attributes->members().size() > 1 )
	{
		throw IECore::Exception( "Unexpected number of attributes" );
	}

	CompoundObjectPtr result = new CompoundObject;

	// Since we're not going to modify any existing members (only add new ones),
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. Be careful not to modify
	// them though!
	result->members() = inputGlobals->members();
	result->members()["option:" + computeOptionName( context )] = attributes->members().begin()->second;

	return result;
}
