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

#include "boost/bind.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/lexical_cast.hpp"

#include "IECoreGL/Selector.h"
#include "IECoreGL/LuminanceTexture.h"
#include "IECoreGL/IECoreGL.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/Shader.h"
#include "IECoreGL/GL.h"

#include "Gaffer/Node.h"
#include "Gaffer/Context.h"

#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

#include "GafferImage/ImagePlug.h"
#include "GafferImage/ImageAlgo.h"

#include "GafferImageUI/ImageGadget.h"

using namespace std;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace IECoreGL;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferImage;
using namespace GafferImageUI;

//////////////////////////////////////////////////////////////////////////
// ImageGadget implementation
//////////////////////////////////////////////////////////////////////////

ImageGadget::ImageGadget()
	:	Gadget( defaultName<ImageGadget>() ),
		m_image( NULL ),
		m_soloChannel( -1 ),
		m_dirtyFlags( AllDirty )
{
	/// \todo Expose accessors to allow the user
	/// to choose which channels are displayed.
	/// What form should this take though? Should they
	/// choose a layer name, or should they choose any
	/// set of 4 channels?
	m_rgbaChannels[0] = "R";
	m_rgbaChannels[1] = "G";
	m_rgbaChannels[2] = "B";
	m_rgbaChannels[3] = "A";

	setContext( new Context() );
}

ImageGadget::~ImageGadget()
{
}

void ImageGadget::setImage( GafferImage::ConstImagePlugPtr image )
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

	m_dirtyFlags = AllDirty;
	requestRender();
}

const GafferImage::ImagePlug *ImageGadget::getImage() const
{
	return m_image.get();
}

void ImageGadget::setContext( Gaffer::ContextPtr context )
{
	if( context == m_context )
	{
		return;
	}

	m_context = context;
	m_contextChangedConnection = m_context->changedSignal().connect( boost::bind( &ImageGadget::contextChanged, this, ::_2 ) );

	m_dirtyFlags = AllDirty;
	requestRender();
}

Gaffer::Context *ImageGadget::getContext()
{
	return m_context.get();
}

const Gaffer::Context *ImageGadget::getContext() const
{
	return m_context.get();
}

void ImageGadget::setSoloChannel( int index )
{
	if( index == m_soloChannel )
	{
		return;
	}
	if( index < -1 || index > 3 )
	{
		throw Exception( "Invalid index" );
	}

	m_soloChannel = index;
	if( m_soloChannel == -1 )
	{
		// Last time we called updateTiles(), we
		// only updated the solo channel, so now
		// we need to trigger a pass over all the
		// channels.
		m_dirtyFlags |= TilesDirty;
	}
	requestRender();
}

int ImageGadget::getSoloChannel() const
{
	return m_soloChannel;
}

Imath::V2f ImageGadget::pixelAt( const IECore::LineSegment3f &lineInGadgetSpace ) const
{
	V3f i;
	if( !lineInGadgetSpace.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return V2f( 0 );
	}

	return V2f( i.x / format().getPixelAspect(), i.y );
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
		m_dirtyFlags |= FormatDirty;
	}
	else if( plug == m_image->dataWindowPlug() )
	{
		m_dirtyFlags |= DataWindowDirty | TilesDirty;
	}
	else if( plug == m_image->channelNamesPlug() )
	{
		m_dirtyFlags |= ChannelNamesDirty | TilesDirty;
	}
	else if( plug == m_image->channelDataPlug() )
	{
		m_dirtyFlags |= TilesDirty;
	}

	if( m_dirtyFlags )
	{
		requestRender();
	}
}

void ImageGadget::contextChanged( const IECore::InternedString &name )
{
	if( !boost::starts_with( name.string(), "ui:" ) )
	{
		m_dirtyFlags = AllDirty;
		requestRender();
	}
}

//////////////////////////////////////////////////////////////////////////
// Image property access.
//////////////////////////////////////////////////////////////////////////

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

// Needed to allow TileIndex to be used as a key in concurrent_unordered_map.
inline size_t GafferImageUI::tbb_hasher( const ImageGadget::TileIndex &tileIndex )
{
	return
		tbb::tbb_hasher( tileIndex.tileOrigin.x ) ^
		tbb::tbb_hasher( tileIndex.tileOrigin.y ) ^
		tbb::tbb_hasher( tileIndex.channelName.c_str() );
}

// Tests to see if a tile needs updating, and if it does, computes
// the channel data to go into it.
struct ImageGadget::TileFunctor
{

	TileFunctor( Tiles &tiles )
		:	m_tiles( tiles )
	{
	}

	void operator()( const ImagePlug *image, const string &channelName, const V2i &tileOrigin )
	{
		Tile &tile = m_tiles[TileIndex(tileOrigin, channelName)];
		ConstFloatVectorDataPtr channelData;
		const IECore::MurmurHash h = image->channelDataPlug()->hash();
		if( !tile.texture || tile.channelDataHash != h )
		{
			tile.channelDataToConvert = image->channelDataPlug()->getValue( &h );
			tile.channelDataHash = h;
		}
	}

	private :

		Tiles &m_tiles;

};

void ImageGadget::updateTiles() const
{
	if( !(m_dirtyFlags & TilesDirty) )
	{
		return;
	}

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
			if( m_soloChannel == -1 || m_rgbaChannels[m_soloChannel] == *it )
			{
				channelsToCompute.push_back( *it );
			}
		}
	}

	// Use parallelGatherTiles() to do the hard work of launching
	// threads and iterating over tiles to get any modified channelData.
	TileFunctor tileFunctor( m_tiles );
	{
		Context::Scope scopedContext( m_context.get() );
		ImageAlgo::parallelProcessTiles( m_image.get(), channelsToCompute, tileFunctor, dataWindow() );
	}

	// Now take the new channelData and convert it into textures for display.
	// We must do this on the main thread because it involves OpenGL.
	for( Tiles::iterator it = m_tiles.begin(); it != m_tiles.end(); ++it )
	{
		if( it->second.channelDataToConvert )
		{
			GLuint texture;
			glGenTextures( 1, &texture );
			it->second.texture = new Texture( texture );
			Texture::ScopedBinding binding( *it->second.texture );

			glPixelStorei( GL_UNPACK_ALIGNMENT, 1 );
			glTexImage2D( GL_TEXTURE_2D, 0, GL_LUMINANCE, ImagePlug::tileSize(), ImagePlug::tileSize(), 0, GL_LUMINANCE,
				GL_FLOAT, &it->second.channelDataToConvert->readable().front() );

			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE );

			it->second.channelDataToConvert = NULL;
		}
	}
	m_dirtyFlags &= ~TilesDirty;
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
		if( !BufferAlgo::intersects( dw, tileBound ) || find( ch.begin(), ch.end(), it->first.channelName.string() ) == ch.end() )
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

namespace
{

const char *vertexSource()
{
	static const char *g_vertexSource =
	"void main()"
	"{"
	"	gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;"
	"	gl_TexCoord[0] = gl_MultiTexCoord0;"
	"}";

	return g_vertexSource;
}

const std::string &fragmentSource()
{
	static std::string g_fragmentSource;
	if( g_fragmentSource.empty() )
	{
		g_fragmentSource =

		"uniform sampler2D redTexture;\n"
		"uniform sampler2D greenTexture;\n"
		"uniform sampler2D blueTexture;\n"
		"uniform sampler2D alphaTexture;\n"

		"#if __VERSION__ >= 330\n"

		"layout( location=0 ) out vec4 outColor;\n"
		"#define OUTCOLOR outColor\n"

		"#else\n"

		"#define OUTCOLOR gl_FragColor\n"

		"#endif\n"

		"void main()"
		"{"
		"	OUTCOLOR = vec4(\n"
		"		texture2D( redTexture, gl_TexCoord[0].xy ).r,\n"
		"		texture2D( greenTexture, gl_TexCoord[0].xy ).r,\n"
		"		texture2D( blueTexture, gl_TexCoord[0].xy ).r,\n"
		"		texture2D( alphaTexture, gl_TexCoord[0].xy ).r\n"
		"	);"
		"}";

		if( glslVersion() >= 330 )
		{
			// the __VERSION__ define is a workaround for the fact that cortex's source preprocessing doesn't
			// define it correctly in the same way as the OpenGL shader preprocessing would.
			g_fragmentSource = "#version 330 compatibility\n #define __VERSION__ 330\n\n" + g_fragmentSource;
		}
	}
	return g_fragmentSource;
}

IECoreGL::Shader *shader()
{
	static IECoreGL::ShaderPtr g_shader;
	if( !g_shader )
	{
		g_shader = ShaderLoader::defaultShaderLoader()->create( vertexSource(), "", fragmentSource() );
	}
	return g_shader.get();
}

IECoreGL::Texture *blackTexture()
{
	static IECoreGL::TexturePtr g_texture;
	if( !g_texture )
	{
		GLuint texture;
		glGenTextures( 1, &texture );
		g_texture = new Texture( texture );
		Texture::ScopedBinding binding( *g_texture );

		const float black = 0;
		glPixelStorei( GL_UNPACK_ALIGNMENT, 1 );
		glTexImage2D( GL_TEXTURE_2D, 0, GL_LUMINANCE, /* width = */ 1, /* height = */ 1, 0, GL_LUMINANCE,
			GL_FLOAT, &black );
	}
	return g_texture.get();
}

} // namespace

void ImageGadget::renderTiles() const
{
	GLint previousProgram;
	glGetIntegerv( GL_CURRENT_PROGRAM, &previousProgram );

	PushAttrib pushAttrib( GL_COLOR_BUFFER_BIT );

	Shader *shader = ::shader();
	glUseProgram( shader->program() );

	glEnable( GL_TEXTURE_2D );

	glEnable( GL_BLEND );
	glBlendFunc( GL_ONE, GL_ONE_MINUS_SRC_ALPHA );

	GLuint textureUnits[4];
	textureUnits[0] = shader->uniformParameter( "redTexture" )->textureUnit;
	textureUnits[1] = shader->uniformParameter( "greenTexture" )->textureUnit;
	textureUnits[2] = shader->uniformParameter( "blueTexture" )->textureUnit;
	textureUnits[3] = shader->uniformParameter( "alphaTexture" )->textureUnit;

	glUniform1i( shader->uniformParameter( "redTexture" )->location, textureUnits[0] );
	glUniform1i( shader->uniformParameter( "greenTexture" )->location, textureUnits[1] );
	glUniform1i( shader->uniformParameter( "blueTexture" )->location, textureUnits[2] );
	glUniform1i( shader->uniformParameter( "alphaTexture" )->location, textureUnits[3] );

	const Box2i dataWindow = this->dataWindow();
	const float pixelAspect = this->format().getPixelAspect();

	V2i tileOrigin = ImagePlug::tileOrigin( dataWindow.min );
	for( ; tileOrigin.y < dataWindow.max.y; tileOrigin.y += ImagePlug::tileSize() )
	{
		for( tileOrigin.x = ImagePlug::tileOrigin( dataWindow.min ).x; tileOrigin.x < dataWindow.max.x; tileOrigin.x += ImagePlug::tileSize() )
		{
			for( int i = 0; i < 4; ++i )
			{
				glActiveTexture( GL_TEXTURE0 + textureUnits[i] );
				const InternedString channelName = m_soloChannel == -1 ? m_rgbaChannels[i] : m_rgbaChannels[m_soloChannel];
				Tiles::const_iterator it = m_tiles.find( TileIndex( tileOrigin, channelName ) );
				if( it != m_tiles.end()  && it->second.texture )
				{
					it->second.texture->bind();
				}
				else
				{
					blackTexture()->bind();
				}
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

				glTexCoord2f( uvBound.min.x, uvBound.min.y  );
				glVertex2f( validBound.min.x * pixelAspect, validBound.min.y );

				glTexCoord2f( uvBound.min.x, uvBound.max.y  );
				glVertex2f( validBound.min.x * pixelAspect, validBound.max.y );

				glTexCoord2f( uvBound.max.x, uvBound.max.y  );
				glVertex2f( validBound.max.x * pixelAspect, validBound.max.y );

				glTexCoord2f( uvBound.max.x, uvBound.min.y  );
				glVertex2f( validBound.max.x * pixelAspect, validBound.min.y );

			glEnd();

		}
	}

	glUseProgram( previousProgram );
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

void ImageGadget::doRender( const GafferUI::Style *style ) const
{
	if( IECoreGL::Selector::currentSelector() )
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
		updateTiles();
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

	glColor3f( 0.0f, 0.0f, 0.0f );
	style->renderSolidRectangle( displayWindowF );
	if( !BufferAlgo::empty( dataWindow ) )
	{
		style->renderSolidRectangle( dataWindowF );
	}

	// Draw the image tiles over the top.

	renderTiles();

	// And add overlays for the display and data windows.

	glColor3f( 0.1f, 0.1f, 0.1f );
	style->renderRectangle( displayWindowF );

	string formatText = Format::name( format );
	const string dimensionsText = lexical_cast<string>( displayWindow.size().x ) + " x " +  lexical_cast<string>( displayWindow.size().y );
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

	if( !BufferAlgo::empty( dataWindow ) && dataWindow != displayWindow )
	{
		glColor3f( 0.5f, 0.5f, 0.5f );
		style->renderRectangle( dataWindowF );

		if( dataWindow.min != displayWindow.min )
		{
			renderText( lexical_cast<string>( dataWindow.min ), dataWindowF.min, V2f( 1, 1.5 ), style );
			renderText( lexical_cast<string>( dataWindow.max ), dataWindowF.max, V2f( 0, -0.5 ), style );
		}
	}
}
