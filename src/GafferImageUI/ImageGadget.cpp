//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferImageUI/ImageGadget.h"

#include "GafferImage/ImageAlgo.h"
#include "GafferImage/ImagePlug.h"
#include "GafferImage/OpenColorIOTransform.h"

#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

#include "Gaffer/BackgroundTask.h"
#include "Gaffer/Context.h"
#include "Gaffer/Node.h"
#include "Gaffer/Process.h"
#include "Gaffer/ScriptNode.h"

#include "IECore/MessageHandler.h"

#include "IECoreGL/GL.h"
#include "IECoreGL/IECoreGL.h"
#include "IECoreGL/Buffer.h"
#include "IECoreGL/LuminanceTexture.h"
#include "IECoreGL/Selector.h"
#include "IECoreGL/Shader.h"
#include "IECoreGL/ShaderLoader.h"

#include "OpenColorIO/OpenColorIO.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"
#include "boost/lexical_cast.hpp"

#include <regex>

using namespace std;
using namespace boost::placeholders;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace IECoreGL;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferImage;
using namespace GafferImageUI;

namespace
{

// These supporting functions, along with RenderTexture itself, contain code copied from ViewportGadget and
// rearranged. It's expressed in such a way that we could use it as a drop-in replacement for the code in
// ViewportGadget if we wanted to avoid the duplication - but this would require exposing it more than we
// are currently comfortable with.
void renderUnitSquare( const IECoreGL::Shader::Parameter *pParameter, const IECoreGL::Shader::Parameter *uvParameter = nullptr )
{
	static float rectPBufferData[12] = { -1, -1, 0,  -1, 1, 0,  1, -1, 0,  1, 1, 0 };
	static float rectUvBufferData[8] = { 0, 0,  0, 1,  1, 0,  1, 1 };
	static IECoreGL::BufferPtr g_rectPBuffer = new IECoreGL::Buffer( rectPBufferData, sizeof( float ) * 12 );
	static IECoreGL::BufferPtr g_rectUvBuffer = new IECoreGL::Buffer( rectUvBufferData, sizeof( float ) * 8 );

	glEnableVertexAttribArrayARB( pParameter->location );
	{
		IECoreGL::Buffer::ScopedBinding bufferBinding( *g_rectPBuffer );
		glVertexAttribPointerARB( pParameter->location, 3, GL_FLOAT, false, 0, nullptr );
	}

	if( uvParameter )
	{
		glEnableVertexAttribArrayARB( uvParameter->location );
		{
			IECoreGL::Buffer::ScopedBinding bufferBinding( *g_rectUvBuffer );
			glVertexAttribPointerARB( uvParameter->location, 2, GL_FLOAT, false, 0, nullptr );
		}
	}

	glDrawArrays( GL_TRIANGLE_STRIP, 0, 4 );

	glDisableVertexAttribArrayARB( pParameter->location );
	if( uvParameter )
	{
		glDisableVertexAttribArrayARB( uvParameter->location );
	}
}

bool checkGLArbTextureFloat()
{
	bool supported = std::regex_match( std::string( (const char*)glGetString( GL_EXTENSIONS ) ), std::regex( R"(.*GL_ARB_texture_float( |\n).*)" ) );
	if( !supported )
	{
		IECore::msg(
			IECore::Msg::Warning, "RenderTexture",
			"Could not find supported floating point texture format in OpenGL. Viewport "
			"display is likely to show banding - please resolve graphics driver issue."
		);
	}
	return supported;
}

GLsizei numSamples()
{
	GLint maxSamples = 0;
	glGetIntegerv( GL_MAX_SAMPLES, &maxSamples );
	return std::min( maxSamples, 8 );
}

V2i glViewportSize()
{
	// This is _not_ the same as `RenderTexture::getViewport()` on high DPI displays.
	// In that case, `getViewport()` returns the GadgetWidget's "virtual" size, which
	// is a factor of the GL viewport's size, which is measured in true pixels.
	int currentViewport[4];
	glGetIntegerv( GL_VIEWPORT, currentViewport );
	return V2i( currentViewport[2] - currentViewport[0], currentViewport[3] - currentViewport[1] );
}

} // namespace

class GafferImageUI::ImageGadget::RenderTexture
{

	public :
		RenderTexture()
			:	m_framebuffer( 0 ),
				m_framebufferSize( -1 ),
				m_colorBuffer( 0 ),
				m_depthBuffer( 0 ),
				m_downsampledFramebuffer( 0 ),
				m_downsampledFramebufferTexture( 0 )
		{
		}

		~RenderTexture()
		{
			// We should technically ensure that the right GL context is current when
			// making these calls, but this seems to work without, because all our GL
			// contexts are sharing the same resources.
			if( m_framebuffer )
			{
				glDeleteFramebuffers( 1, &m_framebuffer );
				glDeleteRenderbuffers( 1, &m_colorBuffer );
				glDeleteRenderbuffers( 1, &m_depthBuffer );
				glDeleteFramebuffers( 1, &m_downsampledFramebuffer );
				glDeleteTextures( 1, &m_downsampledFramebufferTexture );
			}
		}

		// Access the texture that contains everything that has been rendered to this.
		// Note : If we were going to make this a public API, maybe we would want to make this
		// return an IECoreGL::Texture?
		GLint texture()
		{
			return m_downsampledFramebufferTexture;
		}

		/// The RenderScope binds a RenderTexture so that rendering goes to it.
		class GAFFERIMAGEUI_API RenderScope : boost::noncopyable
		{

			public :

				RenderScope( const RenderTexture *framebuffer, bool clearDepth )
					: m_framebuffer( framebuffer )
				{
					glGetIntegerv( GL_DRAW_FRAMEBUFFER_BINDING, &m_defaultFramebuffer );

					// Render to intermediate framebuffer.

					glEnable( GL_BLEND );
					glBindFramebuffer( GL_DRAW_FRAMEBUFFER, m_framebuffer->acquireFramebuffer() );
					glClearColor( 0.0f, 0.0f, 0.0f, 0.0f );
					glClear( GL_COLOR_BUFFER_BIT );
					glEnable( GL_MULTISAMPLE );

					if( clearDepth )
					{
						glClearDepth( 1.0f );
						glClear( GL_DEPTH_BUFFER_BIT );
					}
				}
				~RenderScope()
				{
					// Blit to downsampled framebuffer, to get the image into a texture
					// format we can read from a shader.

					glBindFramebuffer( GL_READ_FRAMEBUFFER, m_framebuffer->m_framebuffer );
					glBindFramebuffer( GL_DRAW_FRAMEBUFFER, m_framebuffer->m_downsampledFramebuffer );
					const V2i size = glViewportSize();
					glBlitFramebuffer( 0, 0, size.x, size.y, 0, 0, size.x, size.y, GL_COLOR_BUFFER_BIT, GL_NEAREST );

					glBindFramebuffer( GL_FRAMEBUFFER, m_defaultFramebuffer );
				}

			private :

				const RenderTexture* m_framebuffer;
				GLint m_defaultFramebuffer;
		};

	private :

		GLuint acquireFramebuffer() const
		{
			const V2i size = glViewportSize();
			if( m_framebuffer && m_framebufferSize == size )
			{
				// Reuse existing buffer.
				return m_framebuffer;
			}

			if( !m_colorBuffer )
			{
				glGenRenderbuffers( 1, &m_colorBuffer );
				glGenRenderbuffers( 1, &m_depthBuffer );

				glGenTextures( 1, &m_downsampledFramebufferTexture );
				glBindTexture( GL_TEXTURE_2D, m_downsampledFramebufferTexture );
				glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST );
				glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST );
				glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE );
				glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE );
			}

			if( m_framebuffer )
			{
				// There is contradictory information out there about whether a
				// framebuffer can handle the attached textures and render buffers being
				// resized - sounds like it depends on the driver. Safer to just
				// recreate it.
				glDeleteFramebuffers( 1, &m_framebuffer );
				glDeleteFramebuffers( 1, &m_downsampledFramebuffer );
			}

			// Create framebuffer
			glGenFramebuffers( 1, &m_framebuffer );
			glBindFramebuffer( GL_DRAW_FRAMEBUFFER, m_framebuffer );

			// Resize color buffer and attach to framebuffer
			static const GLint colorFormat = checkGLArbTextureFloat() ? GL_RGBA16F : GL_RGBA8;
			static const GLsizei samples = numSamples();

			glBindRenderbuffer( GL_RENDERBUFFER, m_colorBuffer );
			glRenderbufferStorageMultisample( GL_RENDERBUFFER, samples, colorFormat, size.x, size.y );
			glFramebufferRenderbuffer( GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, m_colorBuffer );

			// Resize depth buffer and attach to framebuffer
			glBindRenderbuffer( GL_RENDERBUFFER, m_depthBuffer );
			glRenderbufferStorageMultisample( GL_RENDERBUFFER, samples, GL_DEPTH_COMPONENT32F, size.x, size.y );
			glFramebufferRenderbuffer( GL_DRAW_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, m_depthBuffer );

			// Validate framebuffer
			GLenum framebufferStatus = glCheckFramebufferStatus( GL_DRAW_FRAMEBUFFER );
			if( framebufferStatus != GL_FRAMEBUFFER_COMPLETE )
			{
				IECore::msg( IECore::Msg::Warning, "GafferUI::RenderTexture", "Multisampled framebuffer error : " + std::to_string( framebufferStatus ) );
			}

			// Create downsampled framebuffer
			glGenFramebuffers( 1, &m_downsampledFramebuffer );
			glBindFramebuffer( GL_DRAW_FRAMEBUFFER, m_downsampledFramebuffer );

			// Resize color texture and attach to downsampled framebuffer
			glBindTexture( GL_TEXTURE_2D, m_downsampledFramebufferTexture );
			glTexImage2D( GL_TEXTURE_2D, 0, colorFormat, size.x, size.y, 0, GL_RGBA, GL_FLOAT, nullptr );
			glFramebufferTexture2D( GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, m_downsampledFramebufferTexture, 0 );
			// Validate downsampled framebuffer
			framebufferStatus = glCheckFramebufferStatus( GL_DRAW_FRAMEBUFFER );
			if( framebufferStatus != GL_FRAMEBUFFER_COMPLETE )
			{
				IECore::msg( IECore::Msg::Warning, "GafferUI::RenderTexture", "Downsampled framebuffer error : " + std::to_string( framebufferStatus ) );
			}

			m_framebufferSize = size;
			return m_framebuffer;
		}

		// Framebuffer used for intermediate renders before
		// transferring to the output framebuffer using the
		// post-process shaders.
		mutable GLuint m_framebuffer;
		mutable Imath::V2i m_framebufferSize;
		mutable GLuint m_colorBuffer;
		mutable GLuint m_depthBuffer;
		mutable GLuint m_downsampledFramebuffer;
		mutable GLuint m_downsampledFramebufferTexture;
};


namespace
{

struct SelectionPostProcessShader
{
	SelectionPostProcessShader()
		: m_setup( new IECoreGL::Shader::Setup(
			IECoreGL::ShaderLoader::defaultShaderLoader()->create(
				vertexSource(), "", fragmentSource()
			)
		) )
	{
		m_textureParameter = m_setup->shader()->uniformParameter( "framebufferTexture" );
		if( !m_textureParameter || m_textureParameter->type != GL_SAMPLER_2D )
		{
			throw Exception( "Post process shader must have parameter `uniform sampler2D framebufferTexture`" );
		}

		m_pParameter = m_setup->shader()->vertexAttribute( "vertexP" );
		if( !m_pParameter )
		{
			throw Exception( "Post process shader must have parameter `in vec3 vertexP`" );
		}

		m_uvParameter = m_setup->shader()->vertexAttribute( "vertexuv" );
		if( !m_uvParameter )
		{
			throw Exception( "Post process shader must have parameter `in vec2 vertexuv`" );
		}
	}

	static const char *vertexSource()
	{
		static const char *g_vertexSource = R"(
#version 330 compatibility

in vec3 vertexP;
in vec2 vertexuv;
out vec2 fragmentuv;

void main()
{
gl_Position = vec4( vertexP, 1.0 );
fragmentuv = vertexuv;
}
)";
		return g_vertexSource;
	}

	static const std::string &fragmentSource()
	{
		static std::string g_fragmentSource = R"(
#version 330 compatibility

uniform sampler2D framebufferTexture;
in vec2 fragmentuv;

layout( location=0 ) out vec4 outColor;

void main()
{
vec2 pixelWidth = vec2( dFdx( fragmentuv.x ), dFdy( fragmentuv.y ) );

vec2 query = vec2( 0.0 );
ivec2 iP = ivec2( fragmentuv / pixelWidth );

// Minimum number of texel fetches to give us a reasonable looking 2 pixel border.
// In a 5x5 neighbourhood, we sample the following texels for the neighourhood query
// and the centre value:
//
//  QQQ
// QQQQQ
// QQCQQ
// QQQQQ
//  QQQ

for( int iX = -1; iX <= 1; iX++ )
{
	query = max( query, texelFetch( framebufferTexture, iP + ivec2( iX, -2 ), 0 ).rg );
	query = max( query, texelFetch( framebufferTexture, iP + ivec2( iX, 2 ), 0 ).rg );
}
for( int iX = -2; iX <= 2; iX++ )
{
	query = max( query, texelFetch( framebufferTexture, iP + ivec2( iX, -1 ), 0 ).rg );
	query = max( query, texelFetch( framebufferTexture, iP + ivec2( iX, 1 ), 0 ).rg );
}
for( int iX = 1; iX <= 2; iX++ )
{
	query = max( query, texelFetch( framebufferTexture, iP + ivec2( iX, 0 ), 0 ).rg );
	query = max( query, texelFetch( framebufferTexture, iP + ivec2( -iX, 0 ), 0 ).rg );
}
vec4 center = texelFetch( framebufferTexture, ivec2( fragmentuv / pixelWidth ), 0 );

outColor = center.g == 0 && query.g != 0 ? vec4( 0.8, 0.9, 1.0, 1.0 ) : ( center.r != 0 ? 0.25 : query.r ) * vec4( 0.54, 0.72, 0.87, 1.0 );

}
)";
		return g_fragmentSource;
	}


	IECoreGL::Shader::ConstSetupPtr m_setup;
	const IECoreGL::Shader::Parameter *m_textureParameter = nullptr;
	const IECoreGL::Shader::Parameter *m_pParameter = nullptr;
	const IECoreGL::Shader::Parameter *m_uvParameter = nullptr;
};

const SelectionPostProcessShader *selectionPostProcessShader()
{
	static const SelectionPostProcessShader *g_selectionPostProcessShader = new SelectionPostProcessShader();
	return g_selectionPostProcessShader;
}

} // namespace

// NOTE : Copied from GafferSceneUI::OutputBuffer, would be nice if it was somewhere central.
class GafferImageUI::ImageGadget::BufferTexture
{
	public :

		BufferTexture()
		{
			glGenTextures( 1, &m_texture );
			glGenBuffers( 1, &m_buffer );
		}

		~BufferTexture()
		{
			glDeleteBuffers( 1, &m_buffer );
			glDeleteTextures( 1, &m_texture );
		}

		GLuint texture() const
		{
			return m_texture;
		}

		void updateBuffer( const vector<uint32_t> &data )
		{
			glBindBuffer( GL_TEXTURE_BUFFER, m_buffer );
			glBufferData( GL_TEXTURE_BUFFER, sizeof( uint32_t ) * data.size(), data.data(), GL_STREAM_DRAW );

			glBindTexture( GL_TEXTURE_BUFFER, m_texture );
			glTexBuffer( GL_TEXTURE_BUFFER, GL_R32UI, m_buffer );
		}

	private :

		GLuint m_texture;
		GLuint m_buffer;

};


namespace {
void findUsableTextureFormats( GLenum &monochromeFormat, GLenum &colorFormat )
{
	static bool g_textureFormatsInitialized = false;
	static GLenum g_monochromeFormat = GL_RED;
	static GLenum g_colorFormat = GL_RGB;

	if( !g_textureFormatsInitialized )
	{
		std::string extensions( (char*)glGetString( GL_EXTENSIONS ) );
		if( extensions.find( "GL_ARB_texture_float" ) != string::npos )
		{
			g_monochromeFormat = GL_INTENSITY16F_ARB;
			g_colorFormat = GL_RGB16F_ARB;
		}
		g_textureFormatsInitialized = true;
	}

	monochromeFormat = g_monochromeFormat;
	colorFormat = g_colorFormat;
}

uint64_t g_tileUpdateCount;

//////////////////////////////////////////////////////////////////////////
// TileShader
//////////////////////////////////////////////////////////////////////////

// Manages an OpenGL shader suitable for rendering tiles
class TileShader
{

	public :

		TileShader()
		{

			// Build and compile GLSL shader
			std::string combinedFragmentCode;
			if( glslVersion() >= 330 )
			{
				// the __VERSION__ define is a workaround for the fact that cortex's source preprocessing doesn't
				// define it correctly in the same way as the OpenGL shader preprocessing would.
				combinedFragmentCode = "#version 330 compatibility\n #define __VERSION__ 330\n\n";
			}
			combinedFragmentCode += fragmentSource();

			m_shader = ShaderLoader::defaultShaderLoader()->create( vertexSource(), "", combinedFragmentCode );

			// Query shader parameters

			m_channelTextureUnits[0] = m_shader->uniformParameter( "redTexture" )->textureUnit;
			m_channelTextureUnits[1] = m_shader->uniformParameter( "greenTexture" )->textureUnit;
			m_channelTextureUnits[2] = m_shader->uniformParameter( "blueTexture" )->textureUnit;
			m_channelTextureUnits[3] = m_shader->uniformParameter( "alphaTexture" )->textureUnit;

			m_activeParameterLocation = m_shader->uniformParameter( "activeParam" )->location;
		}

		~TileShader()
		{
		}

		// Binds shader and provides `loadTile()` method to update
		// parameters for a specific tile.
		struct ScopedBinding : PushAttrib
		{

			ScopedBinding( const TileShader &tileShader, V2f wipePos, V2f wipeDir, ImageGadget::BlendMode blendMode )
				:	PushAttrib( GL_COLOR_BUFFER_BIT ), m_tileShader( tileShader )
			{
				glGetIntegerv( GL_CURRENT_PROGRAM, &m_previousProgram );
				glUseProgram( m_tileShader.m_shader->program() );

				glEnable( GL_TEXTURE_2D );

				glGetIntegerv( GL_BLEND_SRC, &m_prevBlendSrc );
				glGetIntegerv( GL_BLEND_DST, &m_prevBlendDst );

				bool negative = false;
				if( blendMode == ImageGadget::BlendMode::Over )
				{
					glBlendFunc( GL_ONE, GL_ONE_MINUS_SRC_ALPHA );
				}
				else if( blendMode == ImageGadget::BlendMode::Under )
				{
					glBlendFunc( GL_ONE_MINUS_DST_ALPHA, GL_ONE );
				}
				else if( blendMode == ImageGadget::BlendMode::Difference )
				{
					negative = true;
					glBlendFunc( GL_ONE, GL_ONE );
				}
				else
				{
					glBlendFunc( GL_ONE, GL_ZERO );
				}

				glUniform2f( tileShader.m_shader->uniformParameter( "wipePos" )->location, wipePos.x, wipePos.y );
				glUniform2f( tileShader.m_shader->uniformParameter( "wipeDir" )->location, wipeDir.x, wipeDir.y );

				glUniform1i( tileShader.m_shader->uniformParameter( "redTexture" )->location, tileShader.m_channelTextureUnits[0] );
				glUniform1i( tileShader.m_shader->uniformParameter( "greenTexture" )->location, tileShader.m_channelTextureUnits[1] );
				glUniform1i( tileShader.m_shader->uniformParameter( "blueTexture" )->location, tileShader.m_channelTextureUnits[2] );
				glUniform1i( tileShader.m_shader->uniformParameter( "alphaTexture" )->location, tileShader.m_channelTextureUnits[3] );
				glUniform1i( tileShader.m_shader->uniformParameter( "negative" )->location, negative );

			}

			~ScopedBinding()
			{
				glUseProgram( m_previousProgram );
				glBlendFunc( m_prevBlendSrc, m_prevBlendDst );
			}

			void loadTile( IECoreGL::ConstTexturePtr channelTextures[4], bool active )
			{
				for( int i = 0; i < 4; ++i )
				{
					glActiveTexture( GL_TEXTURE0 + m_tileShader.m_channelTextureUnits[i] );
					channelTextures[i]->bind();
				}
				glUniform1i( m_tileShader.m_activeParameterLocation, active );
			}

			private :

				const TileShader &m_tileShader;
				GLint m_previousProgram;
				GLint m_prevBlendSrc, m_prevBlendDst;
		};

	private :

		IECoreGL::ShaderPtr m_shader;

		GLuint m_channelTextureUnits[4];
		GLint m_activeParameterLocation;

		static const char *vertexSource()
		{
			static const char *g_vertexSource =
			"void main()"
			"{"
			"	gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;"
			"	gl_TexCoord[0] = gl_MultiTexCoord0;"
			"	gl_TexCoord[1] = gl_MultiTexCoord1;"
			"}";

			return g_vertexSource;
		}

		static const std::string &fragmentSource()
		{
			static std::string g_fragmentSource;
			if( g_fragmentSource.empty() )
			{
				g_fragmentSource =

				"uniform sampler2D redTexture;\n"
				"uniform sampler2D greenTexture;\n"
				"uniform sampler2D blueTexture;\n"
				"uniform sampler2D alphaTexture;\n"

				"uniform bool activeParam;\n"
				"uniform bool negative;\n"
				"uniform vec2 wipePos;\n"
				"uniform vec2 wipeDir;\n"

				"#if __VERSION__ >= 330\n"

				"layout( location=0 ) out vec4 outColor;\n"
				"#define OUTCOLOR outColor\n"

				"#else\n"

				"#define OUTCOLOR gl_FragColor\n"

				"#endif\n"

				"#define ACTIVE_CORNER_RADIUS 0.3\n"

				"void main()"
				"{"
				"	if( dot( gl_TexCoord[1].xy - wipePos, wipeDir ) > 0.0 )\n"
				"	{\n"
				"		discard;\n"
				"	}\n"
				"	OUTCOLOR = vec4(\n"
				"		texture2D( redTexture, gl_TexCoord[0].xy ).r,\n"
				"		texture2D( greenTexture, gl_TexCoord[0].xy ).r,\n"
				"		texture2D( blueTexture, gl_TexCoord[0].xy ).r,\n"
				"		texture2D( alphaTexture, gl_TexCoord[0].xy ).r\n"
				"	);\n"
				"	OUTCOLOR *= negative ? -1.0 : 1.0;\n"
				"	if( activeParam )\n"
				"	{\n"
				"		vec2 pixelWidth = vec2( dFdx( gl_TexCoord[0].x ), dFdy( gl_TexCoord[0].y ) );\n"
				"		float aspect = pixelWidth.x / pixelWidth.y;\n"
				"		vec2 p = abs( gl_TexCoord[0].xy - vec2( 0.5 ) );\n"
				"		float eX = step( 0.5 - pixelWidth.x, p.x ) * step( 0.5 - ACTIVE_CORNER_RADIUS, p.y );\n"
				"		float eY = step( 0.5 - pixelWidth.y, p.y ) * step( 0.5 - ACTIVE_CORNER_RADIUS * aspect, p.x );\n"
				"		float e = eX + eY - eX * eY;\n"
				"		OUTCOLOR += vec4( 0.15 ) * e;\n"
				"	}\n"
				"}";
			}
			return g_fragmentSource;
		}

};

const TileShader *tileShader()
{
	static const TileShader *g_tileShader = new TileShader();
	return g_tileShader;
}

class TileShaderSelectedIDs
{

	public :

		TileShaderSelectedIDs()
		{
			m_shader = ShaderLoader::defaultShaderLoader()->create( vertexSource(), "", fragmentSource() );

			// Query shader parameters

			m_idTextureUnit = m_shader->uniformParameter( "idTexture" )->textureUnit;
			m_selectionTextureUnit = m_shader->uniformParameter( "selectionTexture" )->textureUnit;
		}

		~TileShaderSelectedIDs()
		{
		}

		// Binds shader and provides `loadTile()` method to update
		// parameters for a specific tile.
		struct ScopedBinding : PushAttrib
		{

			ScopedBinding( const TileShaderSelectedIDs &tileShader, GLuint idsTexture, uint32_t highlightID, V2f wipePos, V2f wipeDir )
				:	PushAttrib( GL_COLOR_BUFFER_BIT ), m_tileShader( tileShader )
			{
				glGetIntegerv( GL_CURRENT_PROGRAM, &m_previousProgram );
				glUseProgram( m_tileShader.m_shader->program() );

				glEnable( GL_TEXTURE_2D );

				glGetIntegerv( GL_BLEND_SRC, &m_prevBlendSrc );
				glGetIntegerv( GL_BLEND_DST, &m_prevBlendDst );

				glBlendFunc( GL_ONE, GL_ONE_MINUS_SRC_ALPHA );

				glActiveTexture( GL_TEXTURE0 + tileShader.m_selectionTextureUnit );
				glBindTexture( GL_TEXTURE_BUFFER, idsTexture );
				glUniform1i( tileShader.m_shader->uniformParameter( "selectionTexture" )->location, tileShader.m_selectionTextureUnit );

				glUniform1ui( tileShader.m_shader->uniformParameter( "highlightID" )->location, highlightID );

				glUniform1i( tileShader.m_shader->uniformParameter( "idTexture" )->location, tileShader.m_idTextureUnit );

				glUniform2f( tileShader.m_shader->uniformParameter( "wipePos" )->location, wipePos.x, wipePos.y );
				glUniform2f( tileShader.m_shader->uniformParameter( "wipeDir" )->location, wipeDir.x, wipeDir.y );
			}

			~ScopedBinding()
			{
				glUseProgram( m_previousProgram );
				glBlendFunc( m_prevBlendSrc, m_prevBlendDst );
			}

			void loadTile( IECoreGL::ConstTexturePtr idTexture )
			{
				glActiveTexture( GL_TEXTURE0 + m_tileShader.m_idTextureUnit );
				idTexture->bind();
			}

			private :

				const TileShaderSelectedIDs &m_tileShader;
				GLint m_previousProgram;
				GLint m_prevBlendSrc, m_prevBlendDst;
		};

	private :

		IECoreGL::ShaderPtr m_shader;

		GLuint m_idTextureUnit;
		GLuint m_selectionTextureUnit;

		static const char *vertexSource()
		{
			static const char *g_vertexSource = R"(
void main()
{
	gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;
	gl_TexCoord[0] = gl_MultiTexCoord0;
	gl_TexCoord[1] = gl_MultiTexCoord1;
}
			)";

			return g_vertexSource;
		}

		static const std::string &fragmentSource()
		{
			static std::string g_fragmentSource = R"(
#version 330 compatibility

// Assumes texture contains sorted values.
bool contains( usamplerBuffer array, uint value )
{
	int high = textureSize( array ) - 1;
	int low = 0;
	while( low != high )
	{
		int mid = (low + high + 1) / 2;
		if( texelFetch( array, mid ).r > value )
		{
			high = mid - 1;
		}
		else
		{
			low = mid;
		}
	}
	return texelFetch( array, low ).r == value;
}

uniform usamplerBuffer selectionTexture;
uniform usampler2D idTexture;
uniform uint highlightID;
uniform vec2 wipePos;
uniform vec2 wipeDir;

layout( location=0 ) out vec4 outColor;

void main()
{
	if( dot( gl_TexCoord[1].xy - wipePos, wipeDir ) > 0.0 )
	{
		discard;
	}
	uint id = texture( idTexture, gl_TexCoord[0].xy ).r;
	bool selected = contains( selectionTexture, id );
	bool highlighted = highlightID != 0u && id == highlightID;
	outColor = vec4( float( selected ), float( highlighted ), 0.0, 0.0 );
}
)";
			return g_fragmentSource;
		}

};

const TileShaderSelectedIDs *tileShaderSelectedIDs()
{
	static const TileShaderSelectedIDs *g_tileShaderSelectedIDs = new TileShaderSelectedIDs();
	return g_tileShaderSelectedIDs;
}

const std::string g_idChannelInternalName( "__internal_ID_channel__" );

} // namespace

//////////////////////////////////////////////////////////////////////////
// ImageGadget implementation
//////////////////////////////////////////////////////////////////////////

ImageGadget::ImageGadget()
	:	Gadget( defaultName<ImageGadget>() ),
		m_image( nullptr ),
		m_soloChannel( -1 ),
		m_labelsVisible( true ),
		m_paused( false ),
		m_wipeEnabled( false ),
		m_dirtyFlags( AllDirty ),
		m_renderRequestPending( false ),
		m_blendMode( BlendMode::Over ),
		m_highlightID( 0 ),
		m_selectionRenderTexture( std::make_unique<RenderTexture>() )
{
	m_rgbaChannels[0] = "R";
	m_rgbaChannels[1] = "G";
	m_rgbaChannels[2] = "B";
	m_rgbaChannels[3] = "A";

	setContext( new Context() );

	visibilityChangedSignal().connect( boost::bind( &ImageGadget::visibilityChanged, this ) );
}

ImageGadget::~ImageGadget()
{
	// Make sure background task completes before anything
	// it relies on is destroyed.
	m_tilesTask.reset();
}

void ImageGadget::setImage( GafferImage::ImagePlugPtr image )
{
	if( image == m_image )
	{
		return;
	}

	m_image = image;

	if( Gaffer::Node *node = const_cast<Gaffer::Node *>( image->node() ) )
	{
		m_plugDirtiedConnection = node->plugDirtiedSignal().connect( boost::bind( &ImageGadget::plugDirtied, this, ::_1 ) );
	}
	else
	{
		m_plugDirtiedConnection.disconnect();
	}

	dirty( AllDirty );
}

const GafferImage::ImagePlug *ImageGadget::getImage() const
{
	return m_image.get();
}

void ImageGadget::setContext( Gaffer::ConstContextPtr context )
{
	if( context == m_context )
	{
		return;
	}

	m_context = context;
	m_contextChangedConnection = const_cast<Context *>( m_context.get() )->changedSignal().connect(
		boost::bind( &ImageGadget::contextChanged, this, ::_2 )
	);

	dirty( AllDirty );
}

const Gaffer::Context *ImageGadget::getContext() const
{
	return m_context.get();
}

void ImageGadget::setChannels( const Channels &channels )
{
	if( channels == m_rgbaChannels )
	{
		return;
	}

	m_rgbaChannels = channels;
	channelsChangedSignal()( this );
	dirty( TilesDirty );
}

const ImageGadget::Channels &ImageGadget::getChannels() const
{
	return m_rgbaChannels;
}

void ImageGadget::setIDChannel( const IECore::InternedString & idChannel )
{
	if( idChannel == m_idChannel )
	{
		return;
	}

	m_idChannel = idChannel;

	channelsChangedSignal()( this );
	dirty( TilesDirty );
}

const IECore::InternedString ImageGadget::getIDChannel()
{
	return m_idChannel;
}

ImageGadget::ImageGadgetSignal &ImageGadget::channelsChangedSignal()
{
	return m_channelsChangedSignal;
}

void ImageGadget::setSoloChannel( int index )
{
	if( index == m_soloChannel )
	{
		return;
	}
	if( index < -2 || index > 3 )
	{
		throw Exception( "Invalid index" );
	}

	if( m_soloChannel >= 0 )
	{
		// Last time we called updateTiles(), we
		// only updated the solo channel, so now
		// we need to trigger a pass over the
		// channels we're going to use now.
		dirty( TilesDirty );
	}

	m_soloChannel = index;

	Gadget::dirty( DirtyType::Render );
}

int ImageGadget::getSoloChannel() const
{
	return m_soloChannel;
}

void ImageGadget::setLabelsVisible( bool visible )
{
	if( visible == m_labelsVisible )
	{
		return;
	}
	m_labelsVisible = visible;
	Gadget::dirty( DirtyType::Render );
}

bool ImageGadget::getLabelsVisible() const
{
	return m_labelsVisible;
}

void ImageGadget::setPaused( bool paused )
{
	if( paused == m_paused )
	{
		return;
	}
	m_paused = paused;
	if( m_paused )
	{
		m_tilesTask.reset();
	}
	else if( m_dirtyFlags )
	{
		Gadget::dirty( DirtyType::Render );
	}
	stateChangedSignal()( this );
}

bool ImageGadget::getPaused() const
{
	return m_paused;
}

uint64_t ImageGadget::tileUpdateCount()
{
	return g_tileUpdateCount;
}

void ImageGadget::resetTileUpdateCount()
{
	g_tileUpdateCount = 0;
}

void ImageGadget::setBlendMode( BlendMode blendMode )
{
	m_blendMode = blendMode;
}

ImageGadget::BlendMode ImageGadget::getBlendMode() const
{
	return m_blendMode;
}

ImageGadget::State ImageGadget::state() const
{
	if( m_paused )
	{
		return Paused;
	}
	return m_dirtyFlags ? Running : Complete;
}

ImageGadget::ImageGadgetSignal &ImageGadget::stateChangedSignal()
{
	return m_stateChangedSignal;
}

Imath::V2f ImageGadget::pixelAt( const IECore::LineSegment3f &lineInGadgetSpace ) const
{
	V3f i;
	if( !lineInGadgetSpace.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return V2f( 0 );
	}

	Format f;
	try
	{
		f = format();
	}
	catch( ... )
	{
		// Clients wouldn't necessarily expect pixelAt to throw - if the input image is invalid, there
		// should be other indications in the UI, so it's probably safe to silently return a default pixel
		// here.
		return V2f( 0 );
	}

	return V2f( i.x / f.getPixelAspect(), i.y );
}

void ImageGadget::setWipeEnabled( bool enabled )
{
	m_wipeEnabled = enabled;
}

bool ImageGadget::getWipeEnabled() const
{
	return m_wipeEnabled;
}

void ImageGadget::setWipePosition( const Imath::V2f &position )
{
	m_wipePos = position;
}

const Imath::V2f &ImageGadget::getWipePosition() const
{
	return m_wipePos;
}

void ImageGadget::setWipeAngle( float angle )
{
	m_wipeAngle = angle;
}

float ImageGadget::getWipeAngle() const
{
	return m_wipeAngle;
}

void ImageGadget::setSelectedIDs( const std::vector<uint32_t> &ids )
{
	m_selectedIDs = ids;
	std::sort( m_selectedIDs.begin(), m_selectedIDs.end() );
}

const std::vector<uint32_t> &ImageGadget::getSelectedIDs()
{
	return m_selectedIDs;
}

void ImageGadget::setHighlightID( uint32_t id )
{
	m_highlightID = id;
}

uint32_t ImageGadget::getHighlightID()
{
	return m_highlightID;
}

Imath::Box3f ImageGadget::bound() const
{
	Format f;
	try
	{
		f = format();
	}
	catch( ... )
	{
		return Box3f();
	}

	const Box2i &w = f.getDisplayWindow();
	if( BufferAlgo::empty( w ) )
	{
		return Box3f();
	}

	const float a = f.getPixelAspect();
	return Box3f(
		V3f( (float)w.min.x * a, (float)w.min.y, 0 ),
		V3f( (float)w.max.x * a, (float)w.max.y, 0 )
	);
}

void ImageGadget::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == m_image->formatPlug() )
	{
		dirty( FormatDirty );
	}
	else if( plug == m_image->dataWindowPlug() )
	{
		dirty( DataWindowDirty | TilesDirty );
	}
	else if( plug == m_image->channelNamesPlug() )
	{
		dirty( ChannelNamesDirty | TilesDirty );
	}
	else if( plug == m_image->channelDataPlug() )
	{
		dirty( TilesDirty );
	}
}

void ImageGadget::contextChanged( const IECore::InternedString &name )
{
	dirty( AllDirty );
}

//////////////////////////////////////////////////////////////////////////
// Image property access.
//////////////////////////////////////////////////////////////////////////

void ImageGadget::dirty( unsigned flags )
{
	if( (flags & TilesDirty) && !(m_dirtyFlags & TilesDirty) )
	{
		m_tilesTask.reset();
	}

	m_dirtyFlags |= flags;
	Gadget::dirty(
		( FormatDirty | DataWindowDirty ) ? DirtyType::Bound : DirtyType::Render
	);
}

const GafferImage::Format &ImageGadget::format() const
{
	if( m_dirtyFlags & FormatDirty )
	{
		if( !m_image )
		{
			m_format = Format();
		}
		else
		{
			Context::Scope scopedContext( m_context.get() );
			m_format = m_image->formatPlug()->getValue();
		}
		m_dirtyFlags &= ~FormatDirty;
	}

	return m_format;
}

const Imath::Box2i &ImageGadget::dataWindow() const
{
	if( m_dirtyFlags & DataWindowDirty )
	{
		if( !m_image )
		{
			m_dataWindow = Box2i();
		}
		else
		{
			Context::Scope scopedContext( m_context.get() );
			m_dataWindow = m_image->dataWindowPlug()->getValue();
		}
		m_dirtyFlags &= ~DataWindowDirty;
	}

	return m_dataWindow;
}

const std::vector<std::string> &ImageGadget::channelNames() const
{
	if( m_dirtyFlags & ChannelNamesDirty )
	{
		if( !m_image )
		{
			m_channelNames.clear();
		}
		else
		{
			Context::Scope scopedContext( m_context.get() );
			m_channelNames = m_image->channelNamesPlug()->getValue()->readable();
		}
		m_dirtyFlags &= ~ChannelNamesDirty;
	}
	return m_channelNames;
}

//////////////////////////////////////////////////////////////////////////
// Tile storage
//////////////////////////////////////////////////////////////////////////

namespace
{

IECoreGL::Texture *blackTexture()
{
	static IECoreGL::TexturePtr g_texture;
	if( !g_texture )
	{
		GLenum monochromeTextureFormat, colorTextureFormat;
		findUsableTextureFormats( monochromeTextureFormat, colorTextureFormat );

		GLuint texture;
		glGenTextures( 1, &texture );
		g_texture = new Texture( texture );
		Texture::ScopedBinding binding( *g_texture );

		const float black = 0;
		glPixelStorei( GL_UNPACK_ALIGNMENT, 1 );
		glTexImage2D( GL_TEXTURE_2D, 0, monochromeTextureFormat, /* width = */ 1, /* height = */ 1, 0, GL_RED,
			GL_FLOAT, &black );
	}
	return g_texture.get();
}

IECoreGL::Texture *blackIntTexture()
{
	static IECoreGL::TexturePtr g_texture;
	if( !g_texture )
	{
		GLuint texture;
		glGenTextures( 1, &texture );
		g_texture = new Texture( texture );
		Texture::ScopedBinding binding( *g_texture );

		const unsigned int black = 0;
		glPixelStorei( GL_UNPACK_ALIGNMENT, 1 );
		glTexImage2D(
			GL_TEXTURE_2D, 0, GL_R32UI, /* width = */ 1, /* height = */ 1, 0, GL_RED_INTEGER,
			GL_UNSIGNED_INT, &black
		);
	}
	return g_texture.get();
}

} // namespace

ImageGadget::Tile::Tile( const Tile &other )
	:	m_channelDataHash( other.m_channelDataHash ),
		m_channelDataToConvert( other.m_channelDataToConvert ),
		m_texture( other.m_texture ),
		m_active( false )
{
}

ImageGadget::Tile::Update ImageGadget::Tile::computeUpdate( const GafferImage::ImagePlug *image, bool loadAsID )
{
	if( !m_texture )
	{
		m_loadAsID = loadAsID;
	}
	else
	{
		if( loadAsID != m_loadAsID )
		{
			throw Exception( "Cannot switch loadAsID once an ImageGadget tile is initialized." );
		}
	}
	const IECore::MurmurHash h = image->channelDataPlug()->hash();
	Mutex::scoped_lock lock( m_mutex );
	if( m_channelDataHash != MurmurHash() && m_channelDataHash == h )
	{
		return Update{ this, nullptr, MurmurHash() };
	}

	m_active = true;
	m_activeStartTime = std::chrono::steady_clock::now();
	lock.release(); // Release while doing expensive calculation so UI thread doesn't wait.
	ConstFloatVectorDataPtr channelData = image->channelDataPlug()->getValue( &h );
	return Update{ this, channelData, h };
}

void ImageGadget::Tile::applyUpdates( const std::vector<Update> &updates )
{
	for( const auto &u : updates )
	{
		u.tile->m_mutex.lock();
	}

	for( const auto &u : updates )
	{
		if( u.channelData )
		{
			u.tile->m_channelDataToConvert = u.channelData;
			u.tile->m_channelDataHash = u.channelDataHash;
		}
		u.tile->m_active = false;
	}

	for( const auto &u : updates )
	{
		u.tile->m_mutex.unlock();
	}
}

void ImageGadget::Tile::resetActive()
{
	Mutex::scoped_lock lock( m_mutex );
	m_active = false;
}

const IECoreGL::Texture *ImageGadget::Tile::texture( bool &active )
{
	const auto now = std::chrono::steady_clock::now();
	Mutex::scoped_lock lock( m_mutex );
	if( m_active && ( now - m_activeStartTime ) > std::chrono::milliseconds( 20 ) )
	{
		// We don't draw a tile as active until after a short delay, to avoid
		// distractions when the image generation is really fast anyway.
		active = true;
	}

	ConstFloatVectorDataPtr channelDataToConvert = m_channelDataToConvert;
	m_channelDataToConvert = nullptr;
	lock.release(); // Don't hold lock while doing expensive conversion

	if( channelDataToConvert )
	{
		GLenum monochromeTextureFormat, colorTextureFormat;
		findUsableTextureFormats( monochromeTextureFormat, colorTextureFormat );
		if( !m_texture )
		{
			GLuint texture;
			glGenTextures( 1, &texture );
			m_texture = new Texture( texture ); // Lock not needed, because this is only touched on the UI thread.
			Texture::ScopedBinding binding( *m_texture );

			if( m_loadAsID )
			{
				glTexImage2D(
					GL_TEXTURE_2D, 0, GL_R32UI, ImagePlug::tileSize(), ImagePlug::tileSize(), 0, GL_RED_INTEGER,
					GL_UNSIGNED_INT, nullptr
				);
			}
			else
			{
				glTexImage2D(
					GL_TEXTURE_2D, 0, monochromeTextureFormat, ImagePlug::tileSize(), ImagePlug::tileSize(), 0, GL_RED,
					GL_FLOAT, nullptr
				);
			}

			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE );

		}

		Texture::ScopedBinding binding( *m_texture );
		glPixelStorei( GL_UNPACK_ALIGNMENT, 1 );

		if( m_loadAsID )
		{
			glTexSubImage2D(
				GL_TEXTURE_2D, 0, 0, 0, ImagePlug::tileSize(), ImagePlug::tileSize(), GL_RED_INTEGER,
				GL_UNSIGNED_INT, channelDataToConvert->readable().data()
			);
		}
		else
		{
			glTexSubImage2D(
				GL_TEXTURE_2D, 0, 0, 0, ImagePlug::tileSize(), ImagePlug::tileSize(), GL_RED,
				GL_FLOAT, channelDataToConvert->readable().data()
			);
		}

		g_tileUpdateCount++;
	}

	return m_texture ? m_texture.get() : blackTexture();
}

void ImageGadget::updateTiles()
{
	if( !(m_dirtyFlags & TilesDirty) )
	{
		return;
	}

	if( m_paused )
	{
		return;
	}

	if( m_tilesTask )
	{
		const auto status = m_tilesTask->status();
		if( status == BackgroundTask::Pending || status == BackgroundTask::Running )
		{
			return;
		}
	}

	stateChangedSignal()( this );
	removeOutOfBoundsTiles();

	// Decide which channels to compute. This is the intersection
	// of the available channels (channelNames) and the channels
	// we want to display (m_rgbaChannels).
	const vector<string> &channelNames = this->channelNames();
	vector<string> channelsToCompute;
	for( vector<string>::const_iterator it = channelNames.begin(), eIt = channelNames.end(); it != eIt; ++it )
	{
		if( find( m_rgbaChannels.begin(), m_rgbaChannels.end(), *it ) != m_rgbaChannels.end() )
		{
			if( m_soloChannel < 0 || m_rgbaChannels[m_soloChannel] == *it || m_rgbaChannels[3] == *it )
			{
				channelsToCompute.push_back( *it );
			}
		}

		if( *it == m_idChannel.string() )
		{
			channelsToCompute.push_back( g_idChannelInternalName );
		}
	}

	const Box2i dataWindow = this->dataWindow();

	// Do the actual work of generating the tiles asynchronously,
	// in the background.

	auto tileFunctor = [this, channelsToCompute] ( const ImagePlug *image, const V2i &tileOrigin ) {

		try
		{
			vector<Tile::Update> updates;
			ImagePlug::ChannelDataScope channelScope( Context::current() );
			for( auto &channelName : channelsToCompute )
			{
				Tile &tile = m_tiles[TileIndex(tileOrigin, channelName)];
				if( channelName == g_idChannelInternalName )
				{
					channelScope.setChannelName( &m_idChannel.string() );
					updates.push_back( tile.computeUpdate( image, true ) );
				}
				else
				{
					channelScope.setChannelName( &channelName );
					updates.push_back( tile.computeUpdate( image ) );
				}
			}

			Tile::applyUpdates( updates );

			if( refCount() && !m_renderRequestPending.exchange( true ) )
			{
				// Must hold a reference to stop us dying before our UI thread call is scheduled.
				ImageGadgetPtr thisRef = this;
				ParallelAlgo::callOnUIThread(
					[thisRef] {
						thisRef->m_renderRequestPending = false;
						thisRef->Gadget::dirty( DirtyType::Render );
					}
				);
			}
		}
		catch( ... )
		{
			// We don't want to call `Tile::applyUpdates()` because we won't have
			// a complete set of updates for all channels. But we do need to turn off
			// the active flag for each tile.
			for( auto &channelName : channelsToCompute )
			{
				m_tiles[TileIndex(tileOrigin, channelName)].resetActive();
			}
			throw;
		}

	};

	Context::Scope scopedContext( m_context.get() );
	m_tilesTask = ParallelAlgo::callOnBackgroundThread(
		// Subject
		m_image.get(),
		// OK to capture `this` via raw pointer, because ~ImageGadget waits for
		// the background process to complete.
		[ this, channelsToCompute, dataWindow, tileFunctor ] {

			try
			{
				ImageAlgo::parallelProcessTiles( m_image.get(), tileFunctor, dataWindow );
				m_dirtyFlags &= ~TilesDirty;
			}
			catch( const Gaffer::ProcessException & )
			{
				// No point starting a new compute if it's just
				// going to error again.
				m_dirtyFlags &= ~TilesDirty;
			}
			catch( const IECore::Cancelled & )
			{
				// Don't clear dirty flag, so that we restart
				// on the next redraw.
			}

			if( refCount() )
			{
				ImageGadgetPtr thisRef = this;
				ParallelAlgo::callOnUIThread(
					[thisRef] {
						thisRef->stateChangedSignal()( thisRef.get() );
					}
				);
			}

		}
	);

}

void ImageGadget::removeOutOfBoundsTiles() const
{
	// In theory, any given tile we hold could turn out to be valid
	// for some future image we want to display, particularly if the
	// user is switching back and forth between the same images. But
	// we don't want to accumulate unbounded numbers of tiles either,
	// so here we prune out any tiles that we know can't be useful for
	// the current image, because they either have an invalid channel
	// name or are outside the data window.
	const Box2i &dw = dataWindow();
	const vector<string> &ch = channelNames();
	for( Tiles::iterator it = m_tiles.begin(); it != m_tiles.end(); )
	{
		const Box2i tileBound( it->first.tileOrigin, it->first.tileOrigin + V2i( ImagePlug::tileSize() ) );

		const std::string &effectiveChannelName = it->first.channelName.string() == g_idChannelInternalName ? m_idChannel.string() : it->first.channelName.string();
		if( !BufferAlgo::intersects( dw, tileBound ) || find( ch.begin(), ch.end(), effectiveChannelName ) == ch.end() )
		{
			it = m_tiles.unsafe_erase( it );
		}
		else
		{
			++it;
		}
	}
}

//////////////////////////////////////////////////////////////////////////
// Rendering
//////////////////////////////////////////////////////////////////////////

void ImageGadget::visibilityChanged()
{
	if( !visible() )
	{
		m_tilesTask.reset();
	}
}

void ImageGadget::renderTiles( bool ids ) const
{
	float radians = m_wipeAngle * M_PI / 180.0f;
	const Box2i dataWindow = this->dataWindow();

	std::variant<std::monostate, TileShader::ScopedBinding, TileShaderSelectedIDs::ScopedBinding> shaderBinding;

	V2f effectiveWipePos = m_wipeEnabled ? m_wipePos : V2f( dataWindow.min.x, dataWindow.min.y );
	V2f effectiveWipeDir = m_wipeEnabled ? V2f( cosf( radians ), sinf( radians ) ) : V2f( -1, 0 );

	if( !ids )
	{
		shaderBinding.emplace<TileShader::ScopedBinding>(
			*tileShader(),
			effectiveWipePos,
			effectiveWipeDir,
			m_blendMode
		);
	}
	else
	{
		if( !m_selectedIDsBuffer )
		{
			m_selectedIDsBuffer = std::make_unique<BufferTexture>();
		}

		if( m_selectedIDs.size() )
		{
			m_selectedIDsBuffer->updateBuffer( m_selectedIDs );
		}
		else
		{
			// OpenGL doesn't allow bufferData to actually be zero length
			static std::vector<uint32_t> g_emptyBuffer = { std::numeric_limits< uint32_t>::max() };
			m_selectedIDsBuffer->updateBuffer( g_emptyBuffer );
		}

		shaderBinding.emplace<TileShaderSelectedIDs::ScopedBinding>(
			*tileShaderSelectedIDs(),
			m_selectedIDsBuffer->texture(),
			m_highlightID,
			effectiveWipePos,
			effectiveWipeDir
		);

	}

	const float pixelAspect = this->format().getPixelAspect();

	V2i tileOrigin = ImagePlug::tileOrigin( dataWindow.min );
	for( ; tileOrigin.y < dataWindow.max.y; tileOrigin.y += ImagePlug::tileSize() )
	{
		for( tileOrigin.x = ImagePlug::tileOrigin( dataWindow.min ).x; tileOrigin.x < dataWindow.max.x; tileOrigin.x += ImagePlug::tileSize() )
		{

			if( std::holds_alternative<TileShader::ScopedBinding>( shaderBinding ) )
			{
				bool active = false;
				IECoreGL::ConstTexturePtr channelTextures[4];
				for( int i = 0; i < 4; ++i )
				{
					const InternedString channelName = ( m_soloChannel < 0 || i == 3 ) ? m_rgbaChannels[i] : m_rgbaChannels[m_soloChannel];
					Tiles::const_iterator it = m_tiles.find( TileIndex( tileOrigin, channelName ) );
					if( it != m_tiles.end() )
					{
						channelTextures[i] = it->second.texture( active );
					}
					else
					{
						channelTextures[i] = blackTexture();
					}
				}
				std::get<TileShader::ScopedBinding>( shaderBinding ).loadTile( channelTextures, active );
			}
			else
			{
				IECoreGL::ConstTexturePtr idTexture;
				Tiles::const_iterator it = m_tiles.find( TileIndex( tileOrigin, g_idChannelInternalName ) );
				if( it != m_tiles.end() )
				{
					bool unusedActive = false; // We don't have activity indicators for the id AOV
					// \todo : Should we validate that this tile has been loaded as an integer texture?
					idTexture = it->second.texture( unusedActive );
				}
				else
				{
					idTexture = blackIntTexture();
				}
				std::get<TileShaderSelectedIDs::ScopedBinding>( shaderBinding ).loadTile( idTexture );
			}

			const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
			const Box2i validBound = BufferAlgo::intersection( tileBound, dataWindow );
			const Box2f uvBound(
				V2f(
					lerpfactor<float>( validBound.min.x, tileBound.min.x, tileBound.max.x ),
					lerpfactor<float>( validBound.min.y, tileBound.min.y, tileBound.max.y )
				),
				V2f(
					lerpfactor<float>( validBound.max.x, tileBound.min.x, tileBound.max.x ),
					lerpfactor<float>( validBound.max.y, tileBound.min.y, tileBound.max.y )
				)
			);

			glBegin( GL_QUADS );

				glTexCoord2f( uvBound.min.x, uvBound.min.y );
				glMultiTexCoord2f( GL_TEXTURE1, validBound.min.x, validBound.min.y );
				glVertex2f( validBound.min.x * pixelAspect, validBound.min.y );

				glTexCoord2f( uvBound.min.x, uvBound.max.y );
				glMultiTexCoord2f( GL_TEXTURE1, validBound.min.x, validBound.max.y );
				glVertex2f( validBound.min.x * pixelAspect, validBound.max.y );

				glTexCoord2f( uvBound.max.x, uvBound.max.y );
				glMultiTexCoord2f( GL_TEXTURE1, validBound.max.x, validBound.max.y );
				glVertex2f( validBound.max.x * pixelAspect, validBound.max.y );

				glTexCoord2f( uvBound.max.x, uvBound.min.y );
				glMultiTexCoord2f( GL_TEXTURE1, validBound.max.x, validBound.min.y );
				glVertex2f( validBound.max.x * pixelAspect, validBound.min.y );

			glEnd();

		}
	}
}

void ImageGadget::renderText( const std::string &text, const Imath::V2f &position, const Imath::V2f &alignment, const GafferUI::Style *style ) const
{
	const float scale = 10.0f;
	const ViewportGadget *viewport = ancestor<ViewportGadget>();
	const V2f rasterPosition = viewport->gadgetToRasterSpace( V3f( position.x, position.y, 0.0f ), this );
	const Box3f bound = style->textBound( Style::LabelText, text );

	ViewportGadget::RasterScope rasterScope( viewport );
	glTranslate( V2f(
		rasterPosition.x - scale * lerp( bound.min.x, bound.max.x, alignment.x ),
		rasterPosition.y + scale * lerp( bound.min.y, bound.max.y, alignment.y )
	) );

	glScalef( scale, -scale, scale );
	style->renderText( Style::LabelText, text );
}

void ImageGadget::renderLayer( Layer layer, const GafferUI::Style *style, RenderReason reason ) const
{
	if( !( layer == Layer::Back || layer == Layer::Main || layer == Layer::Front ) )
	{
		return;
	}

	// Compute what we need, and abort rendering if
	// there are any computation errors.

	Format format;
	Box2i dataWindow;
	try
	{
		format = this->format();
		dataWindow = this->dataWindow();
		const_cast<ImageGadget *>( this )->updateTiles();
	}
	catch( ... )
	{
		return;
	}

	// Early out if the image has no size.

	const Box2i &displayWindow = format.getDisplayWindow();
	if( BufferAlgo::empty( displayWindow ) )
	{
		return;
	}

	// Render a black background the size of the image.
	// We need to account for the pixel aspect ratio here
	// and in all our drawing. Variables ending in F denote
	// windows corrected for pixel aspect.

	const Box2f displayWindowF(
		V2f( displayWindow.min ) * V2f( format.getPixelAspect(), 1.0f ),
		V2f( displayWindow.max ) * V2f( format.getPixelAspect(), 1.0f )
	);

	const Box2f dataWindowF(
		V2f( dataWindow.min ) * V2f( format.getPixelAspect(), 1.0f ),
		V2f( dataWindow.max ) * V2f( format.getPixelAspect(), 1.0f )
	);

	if( layer == Layer::Back )
	{
		glColor3f( 0.0f, 0.0f, 0.0f );
		style->renderSolidRectangle( displayWindowF );
		if( !BufferAlgo::empty( dataWindow ) )
		{
			style->renderSolidRectangle( dataWindowF );
		}
		return;
	}

	// Draw the image tiles over the top.

	if( isSelectionRender( reason ) )
	{
		// The rectangle we drew above is sufficient for
		// selection rendering.
		return;
	}

	if( layer == Layer::Main )
	{
		renderTiles();
		return;
	}

	// We've already handled Back and Main, so this must be the Front Layer
	// Time for overlays and labels

	// And add overlays for the display and data windows.

	glColor3f( 0.1f, 0.1f, 0.1f );
	style->renderRectangle( displayWindowF );

	if( !BufferAlgo::empty( dataWindow ) && dataWindow != displayWindow )
	{
		glColor3f( 0.5f, 0.5f, 0.5f );
		style->renderRectangle( dataWindowF );
	}

	// If we have an id channel, and there is selection or highlight to render, then we have to do an id
	// pass. This is rendered to a framebuffer, and then rendered from the framebuffer using a post process
	// shader that converts regions to outlines.
	if( m_idChannel != "" && ( m_selectedIDs.size() || m_highlightID != 0 ) )
	{
		{
			RenderTexture::RenderScope bindScope( m_selectionRenderTexture.get(), true );
			renderTiles( true );
		}

		const SelectionPostProcessShader *shader = selectionPostProcessShader();

		IECoreGL::Shader::Setup::ScopedBinding shaderBinding( *shader->m_setup );
		glActiveTexture( GL_TEXTURE0 + shader->m_textureParameter->textureUnit );
		glBindTexture( GL_TEXTURE_2D, m_selectionRenderTexture->texture() );
		glUniform1i( shader->m_textureParameter->location, shader->m_textureParameter->textureUnit );

		GLint prevBlendSrc, prevBlendDst;
		glGetIntegerv( GL_BLEND_SRC, &prevBlendSrc );
		glGetIntegerv( GL_BLEND_DST, &prevBlendDst );

		// The intermediate framebuffer is already premultipled.
		glBlendFunc( GL_ONE, GL_ONE_MINUS_SRC_ALPHA );

		renderUnitSquare( shader->m_pParameter, shader->m_uvParameter );

		glBlendFunc( prevBlendSrc, prevBlendDst );
	}

	// Render labels for resolution and suchlike.

	if( m_labelsVisible )
	{
		string formatText = Format::name( format );
		const string dimensionsText = lexical_cast<string>( displayWindow.size().x ) + " x " + lexical_cast<string>( displayWindow.size().y );
		if( formatText.empty() )
		{
			formatText = dimensionsText;
		}
		else
		{
			formatText += " ( " + dimensionsText + " )";
		}

		renderText( formatText, V2f( displayWindowF.center().x, displayWindowF.min.y ), V2f( 0.5, 1.5 ), style );

		if( displayWindow.min != V2i( 0 ) )
		{
			renderText( lexical_cast<string>( displayWindow.min ), displayWindowF.min, V2f( 1, 1.5 ), style );
			renderText( lexical_cast<string>( displayWindow.max ), displayWindowF.max, V2f( 0, -0.5 ), style );
		}

		if( !BufferAlgo::empty( dataWindow ) && dataWindow.min != displayWindow.min )
		{
			renderText( lexical_cast<string>( dataWindow.min ), dataWindowF.min, V2f( 1, 1.5 ), style );
		}

		if( !BufferAlgo::empty( dataWindow ) && dataWindow.max != displayWindow.max )
		{
			renderText( lexical_cast<string>( dataWindow.max ), dataWindowF.max, V2f( 0, -0.5 ), style );
		}
	}
}

unsigned ImageGadget::layerMask() const
{
	return (unsigned)Layer::Back | Layer::Main | Layer::Front;
}

Imath::Box3f ImageGadget::renderBound() const
{
	// The render bound can extend beyond the display window, and there isn't much to gain by
	// culling ImageGadgets, so just return an infinite bound
	Box3f b;
	b.makeInfinite();
	return b;
}
