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

#include "boost/algorithm/string/predicate.hpp"

#include "IECore/MessageHandler.h"

#include "IECoreGL/Shader.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/IECoreGL.h"

#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/CompoundNumericPlug.h"

#include "GafferImage/ImagePlug.h"

#include "GafferScene/OpenGLShader.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( OpenGLShader );

OpenGLShader::OpenGLShader( const std::string &name )
	:	GafferScene::Shader( name )
{
	addChild( new Plug( "out", Plug::Out ) );
}

OpenGLShader::~OpenGLShader()
{
}

void OpenGLShader::loadShader( const std::string &shaderName )
{
	IECoreGL::init( false );

	IECoreGL::ShaderLoaderPtr loader = IECoreGL::ShaderLoader::defaultShaderLoader();
	IECoreGL::ShaderPtr shader = loader->load( shaderName );
	
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
		PlugPtr plug = 0;
		switch( parameter->type )
		{
			case GL_BOOL :
				plug = new BoolPlug( *it );
				break;
			case GL_INT :
				plug = new IntPlug( *it );
				break;
			case GL_INT_VEC2 :
				plug = new V2iPlug( *it );
				break;
			case GL_INT_VEC3 :
				plug = new V3iPlug( *it );
				break;
			case GL_FLOAT :
				plug = new FloatPlug( *it );
				break;
			case GL_FLOAT_VEC2 :
				plug = new V2fPlug( *it );
				break;
			case GL_FLOAT_VEC3 :
				// we don't know it's a colour any more than it's a point,
				// but the colour ui is harmless for point types, and the point
				// ui is useless for colour types.
				plug = new Color3fPlug( *it );
				break;
			case GL_FLOAT_VEC4 :
				plug = new Color4fPlug( *it );
				break;
			case GL_SAMPLER_2D :
				/// \todo This introduces a GafferImage dependency into GafferScene,
				/// which I'm not sure is ideal. We could work around this by using
				/// ObjectPlug and using an ImageToObject node to do the conversion,
				/// but that might be a bit annoying for users. Keeping the dependency
				/// might turn out to be useful for other nodes (Seeds perhaps?), so
				/// revisit this at some point to see how things are working out.
				plug = new GafferImage::ImagePlug( *it );
				break;
			default :
				msg(
					Msg::Warning,
					"OpenGLShader::loadShader",
					boost::format( "Parameter \"%s\" has unsupported type" ) % *it
				);
		}
		if( plug )
		{
			plug->setFlags( Plug::Dynamic, true );
			parametersPlug()->addChild( plug );
		}
	}
	
	namePlug()->setValue( shaderName );
	typePlug()->setValue( "gl:surface" );
}

void OpenGLShader::shaderHash( IECore::MurmurHash &h ) const
{
	/// \todo Rejig base class and sibling classes so we don't need to
	/// totally reimplement the base class method as we do here.
	h.append( typeId() );
	for( InputValuePlugIterator it( parametersPlug() ); it!=it.end(); it++ )
	{
		if( const GafferImage::ImagePlug *imagePlug = runTimeCast<GafferImage::ImagePlug>( it->get() ) )
		{
			h.append( imagePlug->imageHash() );
		}
		else
		{
			(*it)->hash( h );
		}
	}
	namePlug()->hash( h );
}

IECore::ShaderPtr OpenGLShader::shader( NetworkBuilder &network ) const
{
	ShaderPtr result = new IECore::Shader( namePlug()->getValue(), typePlug()->getValue() );
	for( InputValuePlugIterator it( parametersPlug() ); it!=it.end(); it++ )
	{
		if( GafferImage::ImagePlug *imagePlug = runTimeCast<GafferImage::ImagePlug>( it->get() ) )
		{
			IECore::ImagePrimitivePtr image = imagePlug->image();
			if( image )
			{
				CompoundDataPtr value = new CompoundData;
				value->writable()["displayWindow"] = new Box2iData( image->getDisplayWindow() );
				value->writable()["dataWindow"] = new Box2iData( image->getDataWindow() );
				CompoundDataPtr channelData = new CompoundData;
				vector<string> channelNames;
				image->channelNames( channelNames );
				for( vector<string>::const_iterator cIt = channelNames.begin(), eCIt = channelNames.end(); cIt != eCIt; cIt++ )
				{
					channelData->writable()[*cIt] = image->variableData<Data>( *cIt );
				}
				value->writable()["channels"] = channelData;
				result->parameters()[(*it)->getName()] = value;
			}
		}
		else
		{
			result->parameters()[(*it)->getName()] = CompoundDataPlug::extractDataFromPlug( *it );
		}
	}
	return result;
}

