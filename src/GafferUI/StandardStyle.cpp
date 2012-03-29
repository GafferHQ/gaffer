//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#include "OpenEXR/ImathVecAlgo.h"

#include "IECore/SearchPath.h"
#include "IECore/Font.h"

#include "IECoreGL/GL.h"
#include "IECoreGL/Font.h"
#include "IECoreGL/FontLoader.h"
#include "IECoreGL/ShaderManager.h"
#include "IECoreGL/Shader.h"
#include "IECoreGL/Camera.h"

#include "GafferUI/StandardStyle.h"

using namespace GafferUI;
using namespace IECore;
using namespace IECoreGL;
using namespace Imath;
using namespace std;

IE_CORE_DEFINERUNTIMETYPED( StandardStyle );

StandardStyle::StandardStyle()
	:	m_shader( 0 )
{
	setFont( LabelText, FontLoader::defaultFontLoader()->load( "Vera.ttf" ) );
	setColor( BackgroundColor, Color3f( 0.2 ) );
	setColor( SunkenColor, Color3f( 0.1 ) );
	setColor( RaisedColor, Color3f( 0.5 ) );
	setColor( ForegroundColor, Color3f( 0.9 ) );
	setColor( HighlightColor, Color3f( 0.466, 0.612, 0.741 ) );
	setColor( ConnectionColor, Color3f( 0.1, 0.1, 0.1 ) );
}

StandardStyle::~StandardStyle()
{
}

void StandardStyle::bind( const Style *currentStyle ) const
{
	if( currentStyle && currentStyle->typeId()==staticTypeId() )
	{
		// binding the shader is actually quite an expensive operation
		// in GL terms, so it's best to avoid it if we know the previous
		// style already bound it anyway.
		return;
	}
	shader()->bind();
}

Imath::Box3f StandardStyle::textBound( TextType textType, const std::string &text ) const
{	
	Imath::Box2f b = m_fonts[textType]->coreFont()->bound( text );
	return Imath::Box3f( Imath::V3f( b.min.x, b.min.y, 0 ), Imath::V3f( b.max.x, b.max.y, 0 ) );
}

void StandardStyle::renderText( TextType textType, const std::string &text, State state ) const
{
	glEnable( GL_TEXTURE_2D );
	glActiveTexture( GL_TEXTURE0 );
	m_fonts[textType]->texture()->bind();
	glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR );
	glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR );

	glUniform1i( m_bezierParameter, 0 );
	glUniform1i( m_borderParameter, 0 );
	glUniform1i( m_edgeAntiAliasingParameter, 0 );
	glUniform1i( m_textureParameter, 0 );
	/// \todo IECore is currently providing sRGB data in IECore::Font::image() and therefore
	/// in IECoreGL::Font::texture(). Either we should change image() to return linear data,
	/// or use the sRGB texture extension in IECoreGL::Font::texture() to ensure that data is
	/// automatically linearised before arriving in the shader.
	glUniform1i( m_textureTypeParameter, 2 );

	glColor( m_colors[ForegroundColor] );

	m_fonts[textType]->renderSprites( text );
}

void StandardStyle::renderFrame( const Imath::Box2f &frame, float borderWidth, State state ) const
{
	
	Box2f b = frame;
	V2f bw( borderWidth );
	b.min -= bw;
	b.max += bw;
	
	V2f cornerSizes = bw / b.size();
	glUniform1i( m_bezierParameter, 0 );
	glUniform1i( m_borderParameter, 1 );
	glUniform2f( m_borderRadiusParameter, cornerSizes.x, cornerSizes.y );
	glUniform1i( m_edgeAntiAliasingParameter, 0 );
	glUniform1i( m_textureTypeParameter, 0 );
	
	glColor( colorForState( RaisedColor, state ) );
	
	glBegin( GL_QUADS );
		
		glTexCoord2f( 0, 0 );
		glVertex2f( b.min.x, b.min.y );
		glTexCoord2f( 0, 1 );
		glVertex2f( b.min.x, b.max.y );
		glTexCoord2f( 1, 1 );
		glVertex2f( b.max.x, b.max.y );
		glTexCoord2f( 1, 0 );
		glVertex2f( b.max.x, b.min.y );

	glEnd();
	
}

void StandardStyle::renderNodule( float radius, State state ) const
{		
	glUniform1i( m_bezierParameter, 0 );
	glUniform1i( m_borderParameter, 1 );
	glUniform2f( m_borderRadiusParameter, 0.5f, 0.5f );
	glUniform1i( m_edgeAntiAliasingParameter, 0 );
	glUniform1i( m_textureTypeParameter, 0 );

	glColor( colorForState( RaisedColor, state ) );

	glBegin( GL_QUADS );
		
		glTexCoord2f( 0, 0 );
		glVertex2f( -radius, -radius );
		glTexCoord2f( 0, 1 );
		glVertex2f( radius, -radius );
		glTexCoord2f( 1, 1 );
		glVertex2f( radius, radius );
		glTexCoord2f( 1, 0 );
		glVertex2f( -radius, radius );

	glEnd();
}

void StandardStyle::renderConnection( const Imath::V3f &src, const Imath::V3f &dst, State state ) const
{
	glUniform1i( m_borderParameter, 0 );
	glUniform1i( m_edgeAntiAliasingParameter, 1 );
	glUniform1i( m_textureTypeParameter, 0 );

	V3f view = IECoreGL::Camera::viewDirectionInObjectSpace();
	V3f o = view.cross( dst - src ).normalized() * 0.2;

	V3f d = V3f( 0, (src.y - dst.y) / 2.0f, 0 );
	
	glUniform1i( m_bezierParameter, 1 );
	glUniform3fv( m_v0Parameter, 1, src.getValue() ); 
	glUniform3fv( m_v1Parameter, 1, (src - d).getValue() ); 
	glUniform3fv( m_v2Parameter, 1, (dst + d).getValue() ); 
	glUniform3fv( m_v3Parameter, 1, dst.getValue() ); 

	glColor( colorForState( ConnectionColor, state ) );

	glCallList( connectionDisplayList() );
}

void StandardStyle::renderSelectionBox( const Imath::Box2f &box ) const
{
	/// \todo It'd be nice to make this a constant size on screen
	/// rather than in Gadget space.
	V2f cornerSizes = V2f( 0.5f ) / box.size();
	glUniform1i( m_bezierParameter, 0 );
	glUniform1i( m_borderParameter, 1 );
	glUniform2f( m_borderRadiusParameter, cornerSizes.x, cornerSizes.y );
	glUniform1i( m_edgeAntiAliasingParameter, 0 );
	glUniform1i( m_textureTypeParameter, 0 );
	
	Color4f c(
		m_colors[HighlightColor][0],
		m_colors[HighlightColor][1],
		m_colors[HighlightColor][2],
		0.25f
	);
	glColor( c );
	
	glBegin( GL_QUADS );
		
		glTexCoord2f( 0, 0 );
		glVertex2f( box.min.x, box.min.y );
		glTexCoord2f( 0, 1 );
		glVertex2f( box.min.x, box.max.y );
		glTexCoord2f( 1, 1 );
		glVertex2f( box.max.x, box.max.y );
		glTexCoord2f( 1, 0 );
		glVertex2f( box.max.x, box.min.y );

	glEnd();

}

void StandardStyle::renderImage( const Imath::Box2f &box, const IECoreGL::Texture *texture ) const
{
	glEnable( GL_TEXTURE_2D );
	glActiveTexture( GL_TEXTURE0 );
	texture->bind();
	/// \todo IECoreGL::ColorTexture doesn't make mipmaps, so we can't do mipmapped filtering here.
	/// Perhaps it should and then perhaps we could.
	glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR );
	glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR );
	
	glUniform1i( m_bezierParameter, 0 );
	glUniform1i( m_borderParameter, 0 );
	glUniform1i( m_edgeAntiAliasingParameter, 0 );
	glUniform1i( m_textureParameter, 0 );
	glUniform1i( m_textureTypeParameter, 1 );

	glColor3f( 1.0f, 1.0f, 1.0f );

	glBegin( GL_QUADS );
		
		glTexCoord2f( 1, 0 );
		glVertex2f( box.max.x, box.min.y );
		glTexCoord2f( 1, 1 );
		glVertex2f( box.max.x, box.max.y );
		glTexCoord2f( 0, 1 );
		glVertex2f( box.min.x, box.max.y );	
		glTexCoord2f( 0, 0 );
		glVertex2f( box.min.x, box.min.y );
		
	glEnd();
}

void StandardStyle::setColor( Color c, Imath::Color3f v )
{
	m_colors[c] = v;
}

const Imath::Color3f &StandardStyle::getColor( Color c ) const
{
	return m_colors[c];
}

void StandardStyle::setFont( TextType textType, IECoreGL::FontPtr font )
{
	m_fonts[textType] = font;
}

const IECoreGL::Font *StandardStyle::getFont( TextType textType ) const
{
	return m_fonts[textType].get();
}

unsigned int StandardStyle::connectionDisplayList()
{
	static unsigned int g_list;
	static bool g_initialised = false;
	if( !g_initialised )
	{
		g_list = glGenLists( 1 );
		
		glNewList( g_list, GL_COMPILE );
		
			glBegin( GL_TRIANGLE_STRIP );
	
				const int numSteps = 50;
				for( int i=0; i<numSteps; i++ )
				{
					float t = i / (float)( numSteps - 1 );
					glTexCoord2f( 0, t );
					glVertex3f( 0, 0, 0 );
					glTexCoord2f( 1, t );
					glVertex3f( 0, 0, 0 );
				}
	
			glEnd();
		
		glEndList();
		
		g_initialised = true;
	}
	return g_list;
}
		
IECoreGL::Shader *StandardStyle::shader() const
{
	if( !m_shader )
	{
		m_shader = ShaderManager::defaultShaderManager()->load( "ui/standardStyle" );
		m_borderParameter = m_shader->uniformParameterIndex( "border" );
		m_borderRadiusParameter = m_shader->uniformParameterIndex( "borderRadius" );
		m_edgeAntiAliasingParameter = m_shader->uniformParameterIndex( "edgeAntiAliasing" );
		m_textureParameter = m_shader->uniformParameterIndex( "texture" );
		m_textureTypeParameter = m_shader->uniformParameterIndex( "textureType" );
		m_bezierParameter = m_shader->uniformParameterIndex( "bezier" );
		m_v0Parameter = m_shader->uniformParameterIndex( "v0" );
		m_v1Parameter = m_shader->uniformParameterIndex( "v1" );
		m_v2Parameter = m_shader->uniformParameterIndex( "v2" );
		m_v3Parameter = m_shader->uniformParameterIndex( "v3" );
	}
	
	return m_shader.get();
}

Imath::Color3f StandardStyle::colorForState( Color c, State s ) const
{
	Color3f result = m_colors[c];
	if( s == Style::HighlightedState )
	{
		result = m_colors[HighlightColor];
	}
	
	return result;
}
