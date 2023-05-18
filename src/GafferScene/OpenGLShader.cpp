//////////////////////////////////////////////////////////////////////////
//
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

#include "GafferScene/OpenGLShader.h"

#include "GafferImage/ImagePlug.h"
#include "GafferImage/ImageAlgo.h"

#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedPlug.h"

#include "IECoreGL/IECoreGL.h"
#include "IECoreGL/Shader.h"
#include "IECoreGL/ShaderLoader.h"

#include "IECoreScene/ShaderNetwork.h"

#include "IECore/MessageHandler.h"

#include "boost/algorithm/string/predicate.hpp"

#include "fmt/format.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( OpenGLShader );

namespace
{

IECore::InternedString g_glVertexSource( "glVertexSource" );
IECore::InternedString g_glNamespacedVertexSource( "gl:vertexSource" );
IECore::InternedString g_glGeometrySource( "glGeometrySource" );
IECore::InternedString g_glNamespacedGeometrySource( "gl:geometrySource" );
IECore::InternedString g_glFragmentSource( "glFragmentSource" );
IECore::InternedString g_glNamespacedFragmentSource( "gl:fragmentSource" );

} // namespace

OpenGLShader::OpenGLShader( const std::string &name )
	:	GafferScene::Shader( name )
{
	addChild( new Plug( "out", Plug::Out ) );
}

OpenGLShader::~OpenGLShader()
{
}

void OpenGLShader::loadShader( const std::string &shaderName, bool keepExistingValues )
{
	if( const ScriptNode *script = scriptNode() )
	{
		if( script->isExecuting() )
		{
			// We're being called during the loading of a script.
			// We might be on a headless farm blade with no GL available,
			// so we can't use IECoreGL to load the shader. Just set the
			// name and type correctly, and assume the dynamic plugs we
			// created for the parameters originally are still correct.
			/// \todo Investigate methods of loading shaders that don't
			/// require GL calls. Candidates include :
			///
			/// - Manual parsing of the GL source looking for "uniform"
			///   declarations.
			/// - Adopting something like GLSLFX and using that to load
			///   shaders.
			namePlug()->setValue( shaderName );
			typePlug()->setValue( "gl:surface" );
			return;
		}
	}

	IECoreGL::init( false );

	IECoreGL::ShaderLoaderPtr loader = IECoreGL::ShaderLoader::defaultShaderLoader();
	IECoreGL::ShaderPtr shader = loader->load( shaderName );

	if( !keepExistingValues )
	{
		// If we're not preserving existing values then remove all existing
		// parameter plugs - below we check if a plug exists and then preserve its values.
		parametersPlug()->clearChildren();
	}

	vector<string> parameterNames;
	shader->uniformParameterNames( parameterNames );
	for( vector<string>::const_iterator it = parameterNames.begin(), eIt = parameterNames.end(); it != eIt; it++ )
	{
		if( boost::starts_with( *it, "vertex" ) && boost::ends_with( *it, "Active" ) )
		{
			// skip parameters which are only there to tell the shader if a particular vertex
			// attribute has been provided - these will be set automatically by IECoreGL.
			continue;
		}

		const IECoreGL::Shader::Parameter *parameter = shader->uniformParameter( *it );
		PlugPtr plug = nullptr;

		const Plug *existingPlug = parametersPlug()->getChild<Plug>( *it );
		const IECore::TypeId existingType = existingPlug ? (IECore::TypeId)existingPlug->typeId() : IECore::InvalidTypeId;
		switch( parameter->type )
		{
			case GL_BOOL :
				plug = existingType != (IECore::TypeId)BoolPlugTypeId ? new BoolPlug( *it ) : nullptr;
				break;
			case GL_INT :
				plug = existingType != (IECore::TypeId)IntPlugTypeId ? new IntPlug( *it ) : nullptr;
				break;
			case GL_INT_VEC2 :
				plug = existingType != (IECore::TypeId)V2iPlugTypeId ? new V2iPlug( *it ) : nullptr;
				break;
			case GL_INT_VEC3 :
				plug = existingType != (IECore::TypeId)V3iPlugTypeId ? new V3iPlug( *it ) : nullptr;
				break;
			case GL_FLOAT :
				plug = existingType != (IECore::TypeId)FloatPlugTypeId ? new FloatPlug( *it ) : nullptr;
				break;
			case GL_FLOAT_VEC2 :
				plug = existingType != (IECore::TypeId)V2fPlugTypeId ? new V2fPlug( *it ) : nullptr;
				break;
			case GL_FLOAT_VEC3 :
				// we don't know it's a colour any more than it's a point,
				// but the colour ui is harmless for point types, and the point
				// ui is useless for colour types.
				plug = existingType != (IECore::TypeId)Color3fPlugTypeId ? new Color3fPlug( *it ) : nullptr;
				break;
			case GL_FLOAT_VEC4 :
				plug = existingType != (IECore::TypeId)Color4fPlugTypeId ? new Color4fPlug( *it ) : nullptr;
				break;
			case GL_SAMPLER_2D :
				plug = existingType != (IECore::TypeId)GafferImage::ImagePlugTypeId ? new GafferImage::ImagePlug( *it ) : nullptr;
				break;
			default :
				msg(
					Msg::Warning,
					"OpenGLShader::loadShader",
					fmt::format( "Parameter \"{}\" has unsupported type", *it )
				);
		}
		if( plug )
		{
			plug->setFlags( Plug::Dynamic, true );
			PlugAlgo::replacePlug( parametersPlug(), plug );
		}
	}

	namePlug()->setValue( shaderName );
	typePlug()->setValue( "gl:surface" );
}

void OpenGLShader::parameterHash( const Gaffer::Plug *parameterPlug, IECore::MurmurHash &h ) const
{
	if( const GafferImage::ImagePlug *imagePlug = runTimeCast<const GafferImage::ImagePlug>( parameterPlug ) )
	{
		h.append( GafferImage::ImageAlgo::imageHash( imagePlug ) );
	}
	else
	{
		Shader::parameterHash( parameterPlug, h );
	}
}

IECore::DataPtr OpenGLShader::parameterValue( const Gaffer::Plug *parameterPlug ) const
{
	if( const GafferImage::ImagePlug *imagePlug = runTimeCast<const GafferImage::ImagePlug>( parameterPlug ) )
	{
		IECoreImage::ImagePrimitivePtr image = GafferImage::ImageAlgo::image( imagePlug );
		if( image )
		{
			CompoundDataPtr value = new CompoundData;
			value->writable()["displayWindow"] = new Box2iData( image->getDisplayWindow() );
			value->writable()["dataWindow"] = new Box2iData( image->getDataWindow() );
			CompoundDataPtr channelData = new CompoundData( CompoundDataMap( image->channels.begin(), image->channels.end() ) );
			value->writable()["channels"] = channelData;
			return value;
		}
		return nullptr;
	}
	else
	{
		return Shader::parameterValue( parameterPlug );
	}
}

IECore::ConstCompoundObjectPtr OpenGLShader::attributes( const Gaffer::Plug *output ) const
{
	ConstCompoundObjectPtr original = Shader::attributes( output );
	const IECoreScene::ShaderNetwork *network = original->member<const IECoreScene::ShaderNetwork>( "gl:surface" );
	if( !network || !network->size() )
	{
		return original;
	}

	IECoreScene::ShaderNetworkPtr updatedNetwork = nullptr;

	auto swapParameter = [network, &updatedNetwork]
	(
		const IECoreScene::Shader *oldShader,
		IECoreScene::ShaderPtr &newShader,
		const InternedString &oldParameterName,
		const DataPtr oldParameterValue,
		const InternedString &newParameterName
	)
	{
		if( !updatedNetwork )
		{
			updatedNetwork = network->copy();
		}

		if( !newShader )
		{
			newShader = oldShader->copy();
		}

		newShader->parameters()[newParameterName] = oldParameterValue;
		newShader->parameters().erase( oldParameterName );
	};

	for( const auto &s : network->shaders() )
	{
		InternedString handle = s.first;
		const IECoreScene::Shader *shader = s.second.get();

		IECoreScene::ShaderPtr updatedShader = nullptr;

		for( auto &kv : shader->parameters() )
		{
			if( kv.first == g_glVertexSource )
			{
				swapParameter( shader, updatedShader, kv.first, kv.second, g_glNamespacedVertexSource );
			}
			else if( kv.first == g_glGeometrySource )
			{
				swapParameter( shader, updatedShader, kv.first, kv.second, g_glNamespacedGeometrySource );
			}
			else if( kv.first == g_glFragmentSource )
			{
				swapParameter( shader, updatedShader, kv.first, kv.second, g_glNamespacedFragmentSource );
			}
		}

		if( updatedShader )
		{
			updatedNetwork->setShader( handle, std::move( updatedShader ) );
		}
	}

	if( updatedNetwork )
	{
		CompoundObjectPtr result = original->copy();
		result->members()["gl:surface"] = updatedNetwork;
		return result;
	}
	else
	{
		return original;
	}
}
