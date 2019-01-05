//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

#include "GafferCycles/CyclesShader.h"

#include "GafferCycles/SocketHandler.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"

#include "IECore/LRUCache.h"
#include "IECore/MessageHandler.h"

#include "boost/algorithm/string.hpp"
#include "boost/format.hpp"

// Cycles
#include "graph/node.h"

using namespace std;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace GafferScene;
using namespace GafferCycles;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( CyclesShader );

CyclesShader::CyclesShader( const std::string &name )
	:	GafferScene::Shader( name )
{
}

CyclesShader::~CyclesShader()
{
}

Gaffer::Plug *CyclesShader::correspondingInput( const Gaffer::Plug *output )
{
	// better to do a few harmless casts than manage a duplicate implementation
	return const_cast<Gaffer::Plug *>(
		const_cast<const CyclesShader *>( this )->correspondingInput( output )
	);
}

const Gaffer::Plug *CyclesShader::correspondingInput( const Gaffer::Plug *output ) const
{
	if( output != outPlug() )
	{
		return Shader::correspondingInput( output );
	}

	return nullptr;

	//const CompoundData *metadata = CyclesShader::metadata();
	//if( !metadata )
	//{
	//	return nullptr;
	//}

	//const StringData *primaryInput = static_cast<const StringData*>( metadata->member<IECore::CompoundData>( "shader" )->member<IECore::Data>( "primaryInput" ) );
	//if( !primaryInput )
	//{
	//	return nullptr;
	//}

	//const Plug *result = parametersPlug()->getChild<Plug>( primaryInput->readable() );
	//if( !result )
	//{
	//	IECore::msg( IECore::Msg::Error, "CyclesShader::correspondingInput", boost::format( "Parameter \"%s\" does not exist" ) % primaryInput->readable() );
	//	return nullptr;
	//}

	//return result;
}

void CyclesShader::loadShader( const std::string &shaderName, bool keepExistingValues )
{

	// First populate all the Gaffer plugs for shaders
	const ccl::NodeType *shaderNodeType = ccl::NodeType::find( ccl::ustring( shaderName.c_str() ) );

	if( !shaderNodeType )
	{
		throw Exception( str( format( "Shader \"%s\" not found" ) % shaderName ) );
	}

	if( !keepExistingValues )
	{
		parametersPlug()->clearChildren();
		outPlug()->clearChildren();
	}

	namePlug()->setValue( shaderName );

	if( boost::ends_with( shaderName, "volume" ) )
	{
		typePlug()->setValue( "ccl:volume" );
	}
	else if( boost::ends_with( shaderName, "displacement" ) )
	{
		typePlug()->setValue( "ccl:displacement" );
	}
	else
	{
		typePlug()->setValue( "ccl:surface" );
	}

	SocketHandler::setupPlugs( shaderNodeType, parametersPlug() );
	SocketHandler::setupPlugs( shaderNodeType, outPlug(), Gaffer::Plug::Out );
	//if( shaderName == "cycles_shader" )
	//{
	//	SocketHandler::setupOutputNodePlug( this );
	//}

}
