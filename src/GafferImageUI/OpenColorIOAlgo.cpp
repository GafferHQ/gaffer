//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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

#include "GafferImageUI/OpenColorIOAlgo.h"

#include "IECoreGL/IECoreGL.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/Shader.h"
#include "IECoreGL/Texture.h"

namespace
{

/// These 3 functions are copied from: OpenColorIO/blob/main/src/libutils/oglapphelpers/glsl.cpp
/// in order to match how OpenColorIO expects textures to be loaded
void SetTextureParameters(GLenum textureType, OCIO_NAMESPACE::Interpolation interpolation)
{
	if(interpolation==OCIO_NAMESPACE::INTERP_NEAREST)
	{
		glTexParameteri(textureType, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
		glTexParameteri(textureType, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
	}
	else
	{
		glTexParameteri(textureType, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
		glTexParameteri(textureType, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	}

	glTexParameteri(textureType, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
	glTexParameteri(textureType, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
	glTexParameteri(textureType, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE);
}

void AllocateTexture3D(
	unsigned index, unsigned & texId,
	OCIO_NAMESPACE::Interpolation interpolation,
	unsigned edgelen, const float * values
)
{
	if(values==nullptr)
	{
		throw IECore::Exception("OpenColorIOAlgo : Initializing LUT : Missing texture data");
	}

	glGenTextures(1, &texId);

	glActiveTexture(GL_TEXTURE0 + index);

	glBindTexture(GL_TEXTURE_3D, texId);

	SetTextureParameters(GL_TEXTURE_3D, interpolation);

	glTexImage3D(
		GL_TEXTURE_3D, 0, GL_RGB32F_ARB,
		edgelen, edgelen, edgelen, 0, GL_RGB, GL_FLOAT, values
	);
}

void AllocateTexture2D(
	unsigned index, unsigned & texId,
	unsigned width, unsigned height,
	OCIO_NAMESPACE::GpuShaderDesc::TextureType channel,
	OCIO_NAMESPACE::Interpolation interpolation, const float * values
)
{
	if (values == nullptr)
	{
		throw IECore::Exception("OpenColorIOAlgo : Initializing LUT : Missing texture data");
	}

	GLint internalformat = GL_RGB32F_ARB;
	GLenum format = GL_RGB;

	if (channel == OCIO_NAMESPACE::GpuShaderCreator::TEXTURE_RED_CHANNEL)
	{
		internalformat = GL_R32F;
		format = GL_RED;
	}

	glGenTextures(1, &texId);

	glActiveTexture(GL_TEXTURE0 + index);

	if (height > 1)
	{
		glBindTexture(GL_TEXTURE_2D, texId);

		SetTextureParameters(GL_TEXTURE_2D, interpolation);

		glTexImage2D(GL_TEXTURE_2D, 0, internalformat, width, height, 0, format, GL_FLOAT, values);
	}
	else
	{
		glBindTexture(GL_TEXTURE_1D, texId);

		SetTextureParameters(GL_TEXTURE_1D, interpolation);

		glTexImage1D(GL_TEXTURE_1D, 0, internalformat, width, 0, format, GL_FLOAT, values);
	}
}

} // namespace

namespace GafferImageUI
{

namespace OpenColorIOAlgo
{

IECoreGL::Shader::SetupPtr displayTransformToFramebufferShader( const OCIO_NAMESPACE::Processor *processor )
{
	std::string colorTransformCode;
	OCIO_NAMESPACE::GpuShaderDescRcPtr shaderDesc;
	if( processor )
	{
		shaderDesc = OCIO_NAMESPACE::GpuShaderDesc::CreateShaderDesc();
		shaderDesc->setLanguage( OCIO_NAMESPACE::GPU_LANGUAGE_GLSL_1_3 );
		shaderDesc->setFunctionName( "OCIODisplay" );

		OCIO_NAMESPACE::ConstGPUProcessorRcPtr gpuProc = processor->getOptimizedGPUProcessor( OCIO_NAMESPACE::OPTIMIZATION_VERY_GOOD );
		gpuProc->extractGpuShaderInfo(shaderDesc);

		colorTransformCode = shaderDesc->getShaderText();
	}
	else
	{
		colorTransformCode = "vec4 OCIODisplay(vec4 inPixel) { return inPixel; }\n";
	}

	colorTransformCode += R"(
vec4 luminance( vec4 c )
{
	return vec4( vec3( c.r * 0.2126 + c.g * 0.7152 + c.b * 0.0722 ), c.a );
}

vec4 colorTransformWithSolo( vec4 inPixel, bool absoluteValue, bool clipping, vec3 multiply, vec3 power, int soloChannel )
{
	if( absoluteValue )
	{
		inPixel = vec4( abs( inPixel.r ), abs( inPixel.g ), abs( inPixel.b ), abs( inPixel.a ) );
	}

	if( clipping )
	{
		inPixel = vec4(
			inPixel.r < 0.0 ? 1.0 : ( inPixel.r > 1.0 ? 0.0 : inPixel.r ),
			inPixel.g < 0.0 ? 1.0 : ( inPixel.g > 1.0 ? 0.0 : inPixel.g ),
			inPixel.b < 0.0 ? 1.0 : ( inPixel.b > 1.0 ? 0.0 : inPixel.b ),
			inPixel.a
		);
	}
	inPixel = vec4( inPixel.rgb * multiply, inPixel.a );
	if( inPixel.r > 0.0 && power.r != 1.0 ) inPixel.r = pow( inPixel.r, power.r );
	if( inPixel.g > 0.0 && power.g != 1.0 ) inPixel.g = pow( inPixel.g, power.g );
	if( inPixel.b > 0.0 && power.b != 1.0 ) inPixel.b = pow( inPixel.b, power.b );

	if( soloChannel == -1 )
	{
		return OCIODisplay( inPixel );
	}
	else if( soloChannel == 0 )
	{
		return OCIODisplay( inPixel.rrrr ).rrrr;
	}
	else if( soloChannel == 1 )
	{
		return OCIODisplay( inPixel.gggg ).gggg;
	}
	else if( soloChannel == 2 )
	{
		return OCIODisplay( inPixel.bbbb ).bbbb;
	}
	else if( soloChannel == 3 )
	{
		return inPixel.aaaa;
	}
	else // -2 is for luminance
	{
		return luminance( OCIODisplay( luminance( inPixel ) ) );
	}
}

vec4 colorTransform( vec4 inPixel, bool unpremultiply, bool absoluteValue, bool clipping, vec3 multiply, vec3 power, int soloChannel )
{
	if( inPixel == vec4( 0.0 ) )
	{
		return inPixel;
	}
	else if( inPixel.a == 0.0 || !unpremultiply || soloChannel == 3 )
	{
		return colorTransformWithSolo( inPixel, absoluteValue, clipping, multiply, power, soloChannel );
	}
	else
	{
		return inPixel.a * colorTransformWithSolo( inPixel / inPixel.a, absoluteValue, clipping, multiply, power, soloChannel );
	}
})";

	// Build and compile GLSL shader
	static const char *g_vertexSource = R"(
#version 120

#if __VERSION__ <= 120
#define in attribute
#define out varying
#endif

in vec3 vertexP;
in vec2 vertexuv;
out vec2 fragmentuv;

void main()
{
	gl_Position = vec4( vertexP, 1.0 );
	fragmentuv = vertexuv;
})";

	std::string combinedFragmentCode;
	if( IECoreGL::glslVersion() >= 330 )
	{
		static const char *g_fragmentSuffixNew = R"(
uniform sampler2D framebufferTexture;
uniform bool unpremultiply;
uniform bool absoluteValue;
uniform bool clipping;
uniform vec3 multiply;
uniform vec3 power;
uniform int soloChannel;
in vec2 fragmentuv;
layout( location=0 ) out vec4 outColor;
void main()
{
	outColor = colorTransform( texture2D( framebufferTexture, fragmentuv ), unpremultiply, absoluteValue, clipping, multiply, power, soloChannel );
})";
		combinedFragmentCode = "#version 330 compatibility\n" + colorTransformCode + g_fragmentSuffixNew;
	}
	else
	{
		static const char *g_fragmentSuffixOld = R"(
uniform sampler2D framebufferTexture;
uniform bool unpremultiply;
uniform bool absoluteValue;
uniform bool clipping;
uniform vec3 multiply;
uniform vec3 power;
uniform int soloChannel;
varying vec2 fragmentuv;
void main()
{
	gl_FragColor = colorTransform( texture2D( framebufferTexture, fragmentuv ), unpremultiply, absoluteValue, clipping, multiply, power, soloChannel );
})";
		combinedFragmentCode = colorTransformCode + g_fragmentSuffixOld;
	}

	IECoreGL::Shader::SetupPtr shaderSetup = new IECoreGL::Shader::Setup(
		IECoreGL::ShaderLoader::defaultShaderLoader()->create( g_vertexSource, "", combinedFragmentCode )
	);

	shaderSetup->addUniformParameter( "unpremultiply", new IECore::BoolData( false ) );
	shaderSetup->addUniformParameter( "absoluteValue", new IECore::BoolData( false ) );
	shaderSetup->addUniformParameter( "clipping", new IECore::BoolData( false ) );
	shaderSetup->addUniformParameter( "multiply", new IECore::Color3fData( Imath::Color3f( 1 ) ) );
	shaderSetup->addUniformParameter( "power", new IECore::Color3fData( Imath::Color3f( 1 ) ) );
	shaderSetup->addUniformParameter( "soloChannel", new IECore::IntData( -1 ) );

	// Query shader parameters

	// If we have a LUT, load any required OpenGL textures

	if( shaderDesc )
	{
		const unsigned maxTexture3D = shaderDesc->getNum3DTextures();
		for(unsigned idx=0; idx<maxTexture3D; ++idx)
		{
			// Get the information of the 3D LUT.

			const char * textureName = nullptr; // textureName is unused, we load the data using get3DTextureValues
			const char * samplerName = nullptr;
			unsigned edgelen = 0;
			OCIO_NAMESPACE::Interpolation interpolation = OCIO_NAMESPACE::INTERP_LINEAR;
			shaderDesc->get3DTexture(idx, textureName, samplerName, edgelen, interpolation);

			if(
				!textureName || !*textureName || !samplerName || !*samplerName || edgelen == 0
			)
			{
				throw IECore::Exception("OpenColorIOAlgo : Initializing LUT : The texture data is corrupted");
			}

			const float * values = nullptr;
			shaderDesc->get3DTextureValues(idx, values);
			if(!values)
			{
				throw IECore::Exception("OpenColorIOAlgo : Initializing LUT : The texture values are missing");
			}

			// Allocate the 3D LUT.

			GLuint currIndex = shaderSetup->shader()->uniformParameter( samplerName )->textureUnit;
			unsigned texId = 0;
			AllocateTexture3D(currIndex, texId, interpolation, edgelen, values);

			// Store in the shader setup
			// \todo - currently takes advantage of special feature of Shader::Setup where despite
			// IECoreGL::Texture only supporting 2D textures, if a tex id wrapped in Texture is passed
			// to Shader::Setup, it will check the type of the sampler uniform corresponding to it, and
			// if the sampler is 3D, it will assume the texture is 3D.
			IECoreGL::ConstTexturePtr t = new IECoreGL::Texture( texId );
			shaderSetup->addUniformParameter( samplerName, t );

		}

		// Process the 1D LUTs.

		const unsigned maxTexture2D = shaderDesc->getNumTextures();
		for(unsigned idx=0; idx<maxTexture2D; ++idx)
		{
			// Get the information of the 1D LUT.

			const char * textureName = nullptr; // textureName is unused, we load the data using get1DTextureValues
			const char * samplerName = nullptr;
			unsigned width = 0;
			unsigned height = 0;
			OCIO_NAMESPACE::GpuShaderDesc::TextureType channel = OCIO_NAMESPACE::GpuShaderDesc::TEXTURE_RGB_CHANNEL;
			OCIO_NAMESPACE::Interpolation interpolation = OCIO_NAMESPACE::INTERP_LINEAR;
			shaderDesc->getTexture(idx, textureName, samplerName, width, height, channel, interpolation);
			if (
				!textureName || !*textureName || !samplerName || !*samplerName || width == 0
			)
			{
				throw IECore::Exception("OpenColorIOAlgo : Initializing LUT : The texture data is corrupted");
			}

			const float * values = nullptr;
			shaderDesc->getTextureValues(idx, values);
			if(!values)
			{
				throw IECore::Exception("OpenColorIOAlgo : Initializing LUT : The texture values are missing");
			}

			// Allocate the 1D LUT (a 2D texture is needed to hold large LUTs).

			GLuint currIndex = shaderSetup->shader()->uniformParameter( samplerName )->textureUnit;
			unsigned texId = 0;
			AllocateTexture2D(currIndex, texId, width, height, channel, interpolation, values);

			// 3. Keep the texture id & name for the later enabling.

			unsigned type = (height > 1) ? GL_TEXTURE_2D : GL_TEXTURE_1D;
			if( type == GL_TEXTURE_1D )
			{
				if( shaderSetup->shader()->uniformParameter( samplerName )->type != GL_SAMPLER_1D )
				{
					throw IECore::Exception("OpenColorIOAlgo : OCIO failed to set up 1D sampler for 1D texture");
				}
			}

			// \todo - currently takes advantage of special feature of Shader::Setup where despite
			// IECoreGL::Texture only supporting 2D textures, if a tex id wrapped in Texture is passed
			// to Shader::Setup, it will check the type of the sampler uniform corresponding to it, and
			// if the sampler is 1D, it will assume the texture is 1D.
			IECoreGL::ConstTexturePtr t = new IECoreGL::Texture( texId );
			shaderSetup->addUniformParameter( samplerName, t );
		}
	}

	return shaderSetup;
}

} // namespace OpenColorIOAlgo

} // namespace GafferImageUI
