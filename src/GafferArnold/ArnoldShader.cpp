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

#include "boost/format.hpp"

#include "ai.h"

#include "IECore/MessageHandler.h"

#include "IECoreArnold/UniverseBlock.h"

#include "Gaffer/TypedPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/CompoundNumericPlug.h"

#include "GafferArnold/ArnoldShader.h"
#include "GafferArnold/ParameterHandler.h"

using namespace std;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace GafferScene;
using namespace GafferArnold;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( ArnoldShader );

ArnoldShader::ArnoldShader( const std::string &name )
	:	GafferScene::Shader( name )
{
}

ArnoldShader::~ArnoldShader()
{
}

void ArnoldShader::loadShader( const std::string &shaderName )
{
	IECoreArnold::UniverseBlock arnoldUniverse;

	const AtNodeEntry *shader = AiNodeEntryLookUp( shaderName.c_str() );
	if( !shader )
	{
		throw Exception( str( format( "Shader \"%s\" not found" ) % shaderName ) );
	}

	namePlug()->setValue( AiNodeEntryGetName( shader ) );
	typePlug()->setValue( "ai:surface" );

	ParameterHandler::setupPlugs( shader, parametersPlug() );

	PlugPtr outPlug = 0;
	const int outputType = AiNodeEntryGetOutputType( shader );
	switch( outputType )
	{
		case AI_TYPE_RGB :

			outPlug = new Color3fPlug(
				"out",
				Plug::Out
			);

			break;

		case AI_TYPE_RGBA :

			outPlug = new Color4fPlug(
				"out",
				Plug::Out
			);

			break;

		case AI_TYPE_FLOAT :

			outPlug = new FloatPlug(
				"out",
				Plug::Out
			);

			break;

		case AI_TYPE_INT :

			outPlug = new IntPlug(
				"out",
				Plug::Out
			);

			break;

	}

	if( outPlug )
	{
		outPlug->setFlags( Plug::Dynamic, true );
		addChild( outPlug );
	}
	else
	{
		if( outputType != AI_TYPE_NONE )
		{
			msg(
				Msg::Warning,
				"ArnoldShader::loadShader",
				format( "Unsupported output parameter of type \"%s\"" ) %
					AiParamGetTypeName( AiNodeEntryGetOutputType( shader ) )
			);
		}
	}

}
