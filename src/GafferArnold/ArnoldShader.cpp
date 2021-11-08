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

#include "GafferArnold/ArnoldShader.h"

#include "GafferArnold/ParameterHandler.h"
#include "GafferArnold/Private/IECoreArnold/UniverseBlock.h"

#include "GafferOSL/OSLShader.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECore/MessageHandler.h"

#include "boost/format.hpp"

#include "ai_metadata.h"

using namespace std;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace GafferScene;
using namespace GafferArnold;
using namespace Gaffer;
using namespace GafferOSL;

namespace
{

// This is to allow Arnold Shaders to be connected to OSL Shaders
static bool g_oslRegistration = OSLShader::registerCompatibleShader( "ai:surface" );

} // namespace

GAFFER_NODE_DEFINE_TYPE( ArnoldShader );

ArnoldShader::ArnoldShader( const std::string &name )
	:	GafferScene::Shader( name )
{
}

ArnoldShader::~ArnoldShader()
{
}

Gaffer::Plug *ArnoldShader::correspondingInput( const Gaffer::Plug *output )
{
	// better to do a few harmless casts than manage a duplicate implementation
	return const_cast<Gaffer::Plug *>(
		const_cast<const ArnoldShader *>( this )->correspondingInput( output )
	);
}

const Gaffer::Plug *ArnoldShader::correspondingInput( const Gaffer::Plug *output ) const
{
	if( output != outPlug() )
	{
		return Shader::correspondingInput( output );
	}

	const CompoundData *metadata = ArnoldShader::metadata();
	if( !metadata )
	{
		return nullptr;
	}

	const StringData *primaryInput = static_cast<const StringData*>( metadata->member<IECore::CompoundData>( "shader" )->member<IECore::Data>( "primaryInput" ) );
	if( !primaryInput )
	{
		return nullptr;
	}

	const Plug *result = parametersPlug()->getChild<Plug>( primaryInput->readable() );
	if( !result )
	{
		IECore::msg( IECore::Msg::Error, "ArnoldShader::correspondingInput", boost::format( "Parameter \"%s\" does not exist" ) % primaryInput->readable() );
		return nullptr;
	}

	return result;
}

void ArnoldShader::loadShader( const std::string &shaderName, bool keepExistingValues )
{
	IECoreArnold::UniverseBlock arnoldUniverse( /* writable = */ false );

	const AtNodeEntry *shader = AiNodeEntryLookUp( AtString( shaderName.c_str() ) );
	if( !shader )
	{
		throw Exception( str( format( "Shader \"%s\" not found" ) % shaderName ) );
	}

	Plug *parametersPlug = this->parametersPlug()->source<Plug>();

	if( !keepExistingValues )
	{
		parametersPlug->clearChildren();
		if( Plug *out = outPlug() )
		{
			removeChild( out );
		}
	}

	namePlug()->source<StringPlug>()->setValue( AiNodeEntryGetName( shader ) );

	string type;
	switch( AiNodeEntryGetType( shader ) )
	{
		case AI_NODE_LIGHT :
			type = "ai:light";
			break;
		case AI_NODE_COLOR_MANAGER :
			type = "ai:color_manager";
			break;
		default :
			type = "ai:surface";
			break;
	}

	if( auto d = metadata()->member<CompoundData>( "shader" )->member<StringData>( "shaderType" ) )
	{
		type = "ai:" + d->readable();
	}
	typePlug()->setValue( type );

	if( !keepExistingValues )
	{
		attributeSuffixPlug()->setValue( type == "ai:lightFilter" ? shaderName : "" );
	}

	ParameterHandler::setupPlugs( shader, parametersPlug );

	int aiOutputType = AiNodeEntryGetOutputType( shader );
	aiOutputType = aiOutputType == AI_TYPE_NONE ? AI_TYPE_POINTER : aiOutputType;
	ParameterHandler::setupPlug( "out", aiOutputType, this, Plug::Out );
}

//////////////////////////////////////////////////////////////////////////
// Metadata loading code
//////////////////////////////////////////////////////////////////////////

namespace {
	const AtString g_nullArnoldString( nullptr );
	const AtString g_primaryInputArnoldString( "primaryInput" );
	const AtString g_shaderTypeArnoldString( "shaderType" );
}

static IECore::ConstCompoundDataPtr metadataGetter( const std::string &key, size_t &cost, const IECore::Canceller *canceller )
{
	IECoreArnold::UniverseBlock arnoldUniverse( /* writable = */ false );

	const AtNodeEntry *shader = AiNodeEntryLookUp( AtString( key.c_str() ) );
	if( !shader )
	{
		throw Exception( str( format( "Shader \"%s\" not found" ) % key ) );
	}

	CompoundDataPtr metadata = new CompoundData;

	CompoundDataPtr shaderMetadata = new CompoundData;
	metadata->writable()["shader"] = shaderMetadata;

	// Currently we don't store metadata for parameters.
	// We add the "parameter" CompoundData mainly so that we are consistent with the OSLShader.
	// Eventually we will load all metadata here and access it from ArnoldShaderUI.
	CompoundDataPtr parameterMetadata = new CompoundData;
	metadata->writable()["parameter"] = parameterMetadata;

	AtString value;
	if( AiMetaDataGetStr( shader, /* look up metadata on node, not on parameter */ g_nullArnoldString , g_primaryInputArnoldString, &value ) )
	{
		shaderMetadata->writable()["primaryInput"] = new StringData( value.c_str() );
	}

	AtString shaderType;
	if( AiMetaDataGetStr( shader, /* look up metadata on node, not on parameter */ g_nullArnoldString , g_shaderTypeArnoldString, &shaderType ) )
	{
		shaderMetadata->writable()["shaderType"] = new StringData( shaderType.c_str() );
	}

	return metadata;
}

typedef IECorePreview::LRUCache<std::string, IECore::ConstCompoundDataPtr> MetadataCache;
MetadataCache g_arnoldMetadataCache( metadataGetter, 10000 );

const IECore::CompoundData *ArnoldShader::metadata() const
{
	if( m_metadata )
	{
		return m_metadata.get();
	}

	m_metadata = g_arnoldMetadataCache.get( namePlug()->getValue() );
	return m_metadata.get();
}
