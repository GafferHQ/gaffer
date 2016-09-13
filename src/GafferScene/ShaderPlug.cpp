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

#include "IECore/MurmurHash.h"

#include "Gaffer/SubGraph.h"
#include "Gaffer/Dot.h"

#include "GafferScene/Shader.h"
#include "GafferScene/ShaderPlug.h"
#include "GafferScene/ShaderSwitch.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

const GafferScene::Shader *shader( const ShaderPlug *plug )
{
	const Plug *source = plug->source<Plug>();
	if( source == plug )
	{
		// No input
		return NULL;
	}
	return runTimeCast<const GafferScene::Shader>( source->node() );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ShaderPlug
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ShaderPlug );

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
	const Plug *sourcePlug = input->source<Plug>();
	const Node *sourceNode = sourcePlug->node();
	if( const Shader *shader = runTimeCast<const Shader>( sourceNode ) )
	{
		return sourcePlug == shader->outPlug() || shader->outPlug()->isAncestorOf( sourcePlug );
	}

	// But we also accept intermediate connections from
	// other ShaderPlugs, knowing that they will apply
	// the same rules when they have their input set.
	if( runTimeCast<const ShaderPlug>( sourcePlug ) )
	{
		return true;
	}

	// Really, we want to return false now, but we can't
	// for backwards compatibility reasons. Before we had
	// a ShaderPlug type, we just used regular Plugs in
	// its place, and those may have made their way onto
	// Boxes and Dots, so we accept those as intermediate
	// connections, and rely on the checks above being
	// called when the intermediate plug receives a
	// connection.

	return
		runTimeCast<const SubGraph>( sourceNode ) ||
		runTimeCast<const ShaderSwitch>( sourceNode ) ||
		runTimeCast<const Dot>( sourceNode )
	;
}

IECore::MurmurHash ShaderPlug::attributesHash() const
{
	const Shader *s = shader( this );
	return s ? s->attributesHash() : MurmurHash();
}

IECore::ConstCompoundObjectPtr ShaderPlug::attributes() const
{
	const Shader *s = shader( this );
	return s ? s->attributes() : new CompoundObject;
}
