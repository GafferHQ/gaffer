//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "GafferSceneUI/Private/OutputBuffer.h"

#include "IECoreGL/ShaderLoader.h"

#include "IECoreImage/DisplayDriver.h"
#include "IECoreImage/OpenImageIOAlgo.h"

#include "Imath/ImathBoxAlgo.h"

#include "OpenImageIO/imageio.h"

#include "boost/lexical_cast.hpp"

#include <unordered_set>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreGL;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// BufferTexture
//////////////////////////////////////////////////////////////////////////

// IECoreGL::Texture doesn't support buffer textures, so we roll our own.
class OutputBuffer::BufferTexture
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

//////////////////////////////////////////////////////////////////////////
// GLSL source
//////////////////////////////////////////////////////////////////////////

namespace
{

const char *g_vertexSource = R"(

#version 330 compatibility

in vec2 P; // Receives unit quad
out vec2 texCoords;

void main()
{
	vec2 p = P * 2.0 - 1.0;
	gl_Position = vec4( p.x, p.y, 0, 1 );
	texCoords = P * vec2( 1, -1 ) + vec2( 0, 1 );
}

)";

const char *g_fragmentSource = R"(

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

uniform sampler2D rgbaTexture;
uniform sampler2D depthTexture;
uniform usampler2D idTexture;
uniform usamplerBuffer selectionTexture;
uniform bool renderSelection;

in vec2 texCoords;
layout( location=0 ) out vec4 outColor;

void main()
{
	outColor = texture( rgbaTexture, texCoords );
	if( outColor.a == 0.0 )
	{
		discard;
	}

	// Input depth is absolute in camera space (completely
	// unrelated to clipping planes). Convert to the screen
	// space that `GL_fragDepth` needs.
	float depth = texture( depthTexture, texCoords ).r;
	vec4 Pcamera = vec4( 0.0, 0.0, -depth, 1.0 );
	vec4 Pclip = gl_ProjectionMatrix * Pcamera;
	float ndcDepth = Pclip.z / Pclip.w;
	gl_FragDepth = (ndcDepth + 1.0) / 2.0;

	if( renderSelection )
	{
		uint id = texture( idTexture, texCoords ).r;
		outColor = vec4( 0.466, 0.612, 0.741, 1.0 ) * outColor.a * 0.75 * float( contains( selectionTexture, id ) );
	}
}

)";

} // namespace

//////////////////////////////////////////////////////////////////////////
// OutputBuffer
//////////////////////////////////////////////////////////////////////////

OutputBuffer::OutputBuffer( IECoreScenePreview::Renderer *renderer )
	:	m_texturesDirty( false )
{
	IECoreScene::OutputPtr outputTemplate = new IECoreScene::Output( "", "ieDisplay", "" );
	outputTemplate->parameters()["driverType"] = new IECore::StringData( "OutputBuffer::DisplayDriver" );
	outputTemplate->parameters()["buffer"] =  new IECore::StringData( std::to_string( (uintptr_t)this ) );
	outputTemplate->parameters()["updateInteractively"] = new IECore::BoolData( true );

	using OutputDefinition = std::tuple<const char *, const char *, const char *>;
	for(
		auto &[name, data, filter] : {
			OutputDefinition( "beauty", "rgba", "box" ),
			OutputDefinition( "depth", "float Z", "box" ),
			OutputDefinition( "id", "uint id", "closest" ),
		}
	)
	{
		IECoreScene::OutputPtr output = outputTemplate->copy();
		output->setName( name );
		output->setData( data );
		output->parameters()["filter"] = new IECore::StringData( filter );
		renderer->output( string( "__outputBuffer:" ) + name, output.get() );
	}
}

OutputBuffer::~OutputBuffer()
{
}

void OutputBuffer::render() const
{
	renderInternal( /* renderSelection = */ false );
}

void OutputBuffer::renderSelection() const
{
	renderInternal( /* renderSelection = */ true );
}

void OutputBuffer::renderInternal( bool renderSelection ) const
{
	if( m_dataWindow.isEmpty() )
	{
		return;
	}

	if( renderSelection && m_selectionBuffer.size() == 1 && m_selectionBuffer[0] == 0 )
	{
		// Selection is empty, so no need to render.
		return;
	}

	if( !m_rgbaTexture )
	{
		GLuint textures[3];
		glGenTextures( 3, textures );
		m_rgbaTexture = new Texture( textures[0] );
		m_depthTexture = new Texture( textures[1] );
		m_idTexture = new Texture( textures[2] );
		for( auto &texture : { m_rgbaTexture, m_depthTexture, m_idTexture } )
		{
			Texture::ScopedBinding binding( *texture );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE );
		}
		m_selectionTexture = std::make_unique<BufferTexture>();
	}

	// We only update textures during the main render, so that the selection
	// overlay we render next remains in sync with it.
	if( !renderSelection && m_texturesDirty.exchange( false ) )
	{
		std::unique_lock lock( m_bufferReallocationMutex );

		glPixelStorei( GL_UNPACK_ALIGNMENT, 1 );

		Texture::ScopedBinding binding( *m_rgbaTexture );
		glTexImage2D(
			GL_TEXTURE_2D, 0, GL_RGBA16F,
			/* width = */ m_dataWindow.size().x + 1, /* height = */ m_dataWindow.size().y + 1, /* border = */ 0,
			GL_RGBA, GL_FLOAT, m_rgbaBuffer.data()
		);

		Texture::ScopedBinding depthBinding( *m_depthTexture );
		glTexImage2D(
			GL_TEXTURE_2D, 0, GL_R32F,
			/* width = */ m_dataWindow.size().x + 1, /* height = */ m_dataWindow.size().y + 1, /* border = */ 0,
			GL_RED, GL_FLOAT, m_depthBuffer.data()
		);

		Texture::ScopedBinding idBinding( *m_idTexture );
		glTexImage2D(
			GL_TEXTURE_2D, 0, GL_R32UI,
			/* width = */ m_dataWindow.size().x + 1, /* height = */ m_dataWindow.size().y + 1, /* border = */ 0,
			GL_RED_INTEGER, GL_UNSIGNED_INT, m_idBuffer.data()
		);

		m_selectionTexture->updateBuffer( m_selectionBuffer );
	}

	if( !m_shader )
	{
		m_shader = ShaderLoader::defaultShaderLoader()->create( g_vertexSource, "", g_fragmentSource );
		m_shaderSetup = new IECoreGL::Shader::Setup( m_shader );
		m_shaderSetup->addUniformParameter( "rgbaTexture", m_rgbaTexture );
		m_shaderSetup->addUniformParameter( "depthTexture", m_depthTexture );
		m_shaderSetup->addUniformParameter( "idTexture", m_idTexture );
		m_shaderSetup->addVertexAttribute(
			"P", new V2fVectorData( { V2f( 0, 0 ), V2f( 0, 1 ), V2f( 1, 1 ), V2f( 1, 0 ) } )
		);
	}

	IECoreGL::Shader::Setup::ScopedBinding shaderBinding( *m_shaderSetup );

	const IECoreGL::Shader::Parameter *selectionParameter = m_shader->uniformParameter( "selectionTexture" );
	GLuint selectionTextureUnit = selectionParameter->textureUnit;
	if( !selectionTextureUnit )
	{
		// Workaround until IECoreGL assigns units to GL_SAMPLER_BUFFER.
		selectionTextureUnit = 3;
	}

	glActiveTexture( GL_TEXTURE0 + selectionTextureUnit );
	glBindTexture( GL_TEXTURE_BUFFER, m_selectionTexture->texture() );
	glUniform1i( selectionParameter->location, selectionTextureUnit );
	glUniform1i( m_shader->uniformParameter( "renderSelection" )->location, renderSelection );

	glPushAttrib( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_ENABLE_BIT );

		glEnable( GL_DEPTH_TEST );
		glEnable( GL_BLEND );
		glBlendFunc( GL_ONE, GL_ONE_MINUS_SRC_ALPHA );
		glDepthFunc( renderSelection ? GL_LEQUAL : GL_LESS );

		glDrawArrays( GL_TRIANGLE_FAN, 0, 4 );

	glPopAttrib();
}

void OutputBuffer::setSelection( const std::vector<uint32_t> &ids )
{
	m_selectionBuffer = ids;
	if( !m_selectionBuffer.size() )
	{
		/// \todo OpenGL documentation suggests we should be able to
		/// make an empty buffer, so I'm not sure why we do this. Either
		/// because some drivers don't like an empty buffer, or because
		/// `contains()` requires a non-empty array? If the latter, we
		/// could remove this because `renderInternal()` now has an early
		/// return for the no-selection case.
		m_selectionBuffer.push_back( 0 );
	}

	std::sort( m_selectionBuffer.begin(), m_selectionBuffer.end() );

	if( !m_dataWindow.isEmpty() )
	{
		// Don't want to dirty texture when data window is empty
		// because there is nothing to draw anyway, and dirtying
		// would prevent `bufferChangedSignal()` from being emitted
		// when the first bucket arrives.
		dirtyTexture();
	}
}

const std::vector<uint32_t> &OutputBuffer::getSelection() const
{
	return m_selectionBuffer;
}

OutputBuffer::BufferChangedSignal &OutputBuffer::bufferChangedSignal()
{
	return m_bufferChangedSignal;
}

uint32_t OutputBuffer::idAt( const V2f &ndcPosition, float &depth ) const
{
	std::unique_lock lock( m_bufferReallocationMutex );

	if( m_dataWindow.isEmpty() )
	{
		return false;
	}

	const V2i pixelPosition = ndcPosition * (m_dataWindow.size() + V2i( 1 ));
	if( !m_dataWindow.intersects( pixelPosition ) )
	{
		return false;
	}

	const size_t pixelIndex = pixelPosition.x + pixelPosition.y * ( m_dataWindow.size().x + 1 );
	assert( pixelIndex < m_idBuffer.size() );
	if( uint32_t id = m_idBuffer[pixelIndex] )
	{
		depth = m_depthBuffer[pixelIndex];
		return id;
	}
	return 0;
}

std::vector<uint32_t> OutputBuffer::idsAt( const Box2f &ndcBox ) const
{
	std::unique_lock lock( m_bufferReallocationMutex );

	if( m_dataWindow.isEmpty() )
	{
		return {};
	}

	Box2i rasterBox(
		ndcBox.min * ( m_dataWindow.size() + V2i( 1 ) ),
		ndcBox.max * ( m_dataWindow.size() + V2i( 1 ) )
	);
	rasterBox.min = clip( rasterBox.min, m_dataWindow );
	rasterBox.max = clip( rasterBox.max, m_dataWindow );

	std::vector<uint32_t> result;
	for( int y = rasterBox.min.y; y < rasterBox.max.y; ++y )
	{
		for( int x = rasterBox.min.x; x < rasterBox.max.x; ++x )
		{
			const size_t pixelIndex = x + y * ( m_dataWindow.size().x + 1 );
			if( uint32_t id = m_idBuffer[pixelIndex] )
			{
				result.push_back( id );
			}
		}
	}

	std::sort( result.begin(), result.end() );
	result.erase(
		std::unique( result.begin(), result.end() ),
		result.end()
	);
	return result;
}

// Note : Cortex display drivers use the EXR convention for windows, _not_ the Gaffer
// one. This means that the size of the image in pixels is `dataWindow.size() + 1`.
void OutputBuffer::imageFormat( const Imath::Box2i &displayWindow, const Imath::Box2i &dataWindow )
{
	if( dataWindow == m_dataWindow )
	{
		return;
	}

	std::unique_lock lock( m_bufferReallocationMutex );

	m_dataWindow = dataWindow;
	const size_t numPixels = (dataWindow.size().x + 1) * (dataWindow.size().y + 1);
	m_rgbaBuffer.resize( numPixels * 4, 0 );
	m_depthBuffer.resize( numPixels, 0 );
	m_idBuffer.resize( numPixels, 0 );

	lock.unlock();
	dirtyTexture();
}

template<typename T>
void OutputBuffer::updateBuffer( const Imath::Box2i &box, const T *data, int numChannels, vector<T> &buffer )
{
	// We deliberately don't worry about synchronising these writes with the
	// reads from the buffers (such as when transferring to a texture). Worst
	// case, we get a torn read and then `dirtyTexture()` forces us to redo it
	// when the write is complete.
	const int fromStride = ( box.size().x + 1 ) * numChannels;
	const int toStride = ( m_dataWindow.size().x + 1 ) * numChannels;
	const T *from = data;
	T *to = buffer.data() + (box.min.y - m_dataWindow.min.y) * toStride + (box.min.x - m_dataWindow.min.x) * numChannels;
	for( int y = box.min.y; y <= box.max.y; ++y )
	{
		std::copy( from, from + fromStride, to );
		to += toStride;
		from += fromStride;
	}
	dirtyTexture();
}

void OutputBuffer::dirtyTexture()
{
	if( !m_texturesDirty.exchange( true ) )
	{
		bufferChangedSignal()();
	}
}

void OutputBuffer::snapshotToFile(
	const std::filesystem::path &fileName,
	const Box2f &resolutionGate,
	const CompoundData *metadata
)
{
	std::filesystem::create_directories( fileName.parent_path() );

	std::unique_lock lock( m_bufferReallocationMutex );

	OIIO::ImageSpec spec( m_dataWindow.size().x + 1, m_dataWindow.size().y + 1, 4, OIIO::TypeDesc::HALF );

	if( !resolutionGate.isEmpty() )
	{
		spec.x = -resolutionGate.min.x;
		spec.y = -resolutionGate.min.y;

		spec.full_x = 0;
		spec.full_y = 0;
		spec.full_width = resolutionGate.size().x;
		spec.full_height = resolutionGate.size().y;
	}

	const std::vector<float> &rgbaBuffer = m_rgbaBuffer;

	for( const auto &[key, value] : metadata->readable() )
	{
		const IECoreImage::OpenImageIOAlgo::DataView dataView( value.get() );
		if( dataView.data )
		{
			spec.attribute( key.c_str(), dataView.type, dataView.data );
		}
	}

	std::unique_ptr<OIIO::ImageOutput> output = OIIO::ImageOutput::create( fileName.c_str() );
	output->open( fileName.c_str(), spec );
	output->write_image( OIIO::TypeDesc::FLOAT, &rgbaBuffer[0] );
	output->close();
}

//////////////////////////////////////////////////////////////////////////
// DisplayDriver
//////////////////////////////////////////////////////////////////////////

class OutputBuffer::DisplayDriver : public IECoreImage::DisplayDriver
{

	public :

		// Deliberately "borrowing" DisplayDriverTypeId as we don't need an ID for
		// a non-public class.
		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( OutputBuffer::DisplayDriver, IECoreImage::DisplayDriverTypeId, DisplayDriver );

		enum class Type
		{
			RGBA,
			Depth,
			ID
		};

		DisplayDriver( const Imath::Box2i &displayWindow, const Imath::Box2i &dataWindow, const std::vector<std::string> &channelNames, IECore::ConstCompoundDataPtr parameters )
			:	IECoreImage::DisplayDriver( displayWindow, dataWindow, channelNames, parameters )
		{
			auto bufferData = parameters->member<StringData>( "buffer" );
			assert( bufferData );
			assert( channelNames.size() == 4 || channelNames.size() == 1 );
			m_buffer = reinterpret_cast<OutputBuffer *>( boost::lexical_cast<uintptr_t>(bufferData->readable() ) );
			m_buffer->imageFormat( displayWindow, dataWindow );
			if( channelNames.size() == 1 )
			{
				if( channelNames[0] == "Z" )
				{
					m_type = Type::Depth;
				}
				else
				{
					assert( channelNames[0] == "id" );
					m_type = Type::ID;
				}
			}
			else
			{
				m_type = Type::RGBA;
			}
		}

		void imageData( const Imath::Box2i &box, const float *data, size_t dataSize ) override
		{
			switch( m_type )
			{
				case Type::RGBA :
					m_buffer->updateBuffer( box, data, 4, m_buffer->m_rgbaBuffer );
					break;
				case Type::Depth :
					m_buffer->updateBuffer( box, data, 1, m_buffer->m_depthBuffer );
					break;
				case Type::ID :
					// Cortex DisplayDrivers technically only support floats, but we send `uint32_t` data through
					// the API and just do pointer casts at either end.
					m_buffer->updateBuffer( box, reinterpret_cast<const uint32_t *>( data ), 1, m_buffer->m_idBuffer );
					break;
			}
		}

		void imageClose() override
		{
		}

		bool scanLineOrderOnly() const override
		{
			return false;
		}

		bool acceptsRepeatedData() const override
		{
			return true;
		}

	private :

		Type m_type;

		OutputBuffer *m_buffer;
		static DisplayDriverDescription<DisplayDriver> g_description;

};

IECoreImage::DisplayDriver::DisplayDriverDescription<OutputBuffer::DisplayDriver> OutputBuffer::DisplayDriver::g_description;
