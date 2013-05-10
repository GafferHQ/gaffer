//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/Shader.h"
#include "IECoreGL/Camera.h"
#include "IECoreGL/Selector.h"

#include "GafferUI/StandardStyle.h"

using namespace GafferUI;
using namespace IECore;
using namespace IECoreGL;
using namespace Imath;
using namespace std;

IE_CORE_DEFINERUNTIMETYPED( StandardStyle );

StandardStyle::StandardStyle()
{
	setFont( LabelText, FontLoader::defaultFontLoader()->load( "VeraBd.ttf" ) );
	setColor( BackgroundColor, Color3f( 0.1 ) );
	setColor( SunkenColor, Color3f( 0.1 ) );
	setColor( RaisedColor, Color3f( 0.4 ) );
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
	
	glEnable( GL_BLEND );
	glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
	glUseProgram( shader()->program() );
	
	if( IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector() )
	{
		selector->loadIDShader( shader() );
	}
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
	glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_LOD_BIAS, -1.25 );

	glUniform1i( g_bezierParameter, 0 );
	glUniform1i( g_borderParameter, 0 );
	glUniform1i( g_edgeAntiAliasingParameter, 0 );
	glUniform1i( g_textureParameter, 0 );
	/// \todo IECore is currently providing sRGB data in IECore::Font::image() and therefore
	/// in IECoreGL::Font::texture(). Either we should change image() to return linear data,
	/// or use the sRGB texture extension in IECoreGL::Font::texture() to ensure that data is
	/// automatically linearised before arriving in the shader.
	glUniform1i( g_textureTypeParameter, 2 );

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
	glUniform1i( g_bezierParameter, 0 );
	glUniform1i( g_borderParameter, 1 );
	glUniform2f( g_borderRadiusParameter, cornerSizes.x, cornerSizes.y );
	glUniform1i( g_edgeAntiAliasingParameter, 0 );
	glUniform1i( g_textureTypeParameter, 0 );

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
	glUniform1i( g_bezierParameter, 0 );
	glUniform1i( g_borderParameter, 1 );
	glUniform2f( g_borderRadiusParameter, 0.5f, 0.5f );
	glUniform1i( g_edgeAntiAliasingParameter, 0 );
	glUniform1i( g_textureTypeParameter, 0 );

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

void StandardStyle::renderConnection( const Imath::V3f &srcPosition, const Imath::V3f &srcTangent, const Imath::V3f &dstPosition, const Imath::V3f &dstTangent, State state ) const
{
	glUniform1i( g_bezierParameter, 1 );
	glUniform1i( g_borderParameter, 0 );
	glUniform1i( g_edgeAntiAliasingParameter, 1 );
	glUniform1i( g_textureTypeParameter, 0 );
	
	glColor( colorForState( ConnectionColor, state ) );
	
	V3f d = dstPosition - srcPosition;
	
	glUniform3fv( g_v0Parameter, 1, srcPosition.getValue() );
	glUniform3fv( g_v1Parameter, 1, ( srcPosition + srcTangent * d.dot( srcTangent ) * 0.25f ).getValue() ); 
	glUniform3fv( g_v2Parameter, 1, ( dstPosition - dstTangent * d.dot( dstTangent ) * 0.25f ).getValue() ); 
	glUniform3fv( g_v3Parameter, 1, dstPosition.getValue() ); 


	glCallList( connectionDisplayList() );
}

void StandardStyle::renderSolidRectangle( const Imath::Box2f &box ) const
{
	glUniform1i( g_bezierParameter, 0 );
	glUniform1i( g_borderParameter, 0 );
	glUniform1i( g_edgeAntiAliasingParameter, 0 );
	glUniform1i( g_textureTypeParameter, 0 );
	
	glBegin( GL_QUADS );
		
		glVertex2f( box.min.x, box.min.y );
		glVertex2f( box.min.x, box.max.y );
		glVertex2f( box.max.x, box.max.y );
		glVertex2f( box.max.x, box.min.y );

	glEnd();
}

void StandardStyle::renderRectangle( const Imath::Box2f &box ) const
{
	glUniform1i( g_bezierParameter, 0 );
	glUniform1i( g_borderParameter, 0 );
	glUniform1i( g_edgeAntiAliasingParameter, 0 );
	glUniform1i( g_textureTypeParameter, 0 );
	
	glBegin( GL_LINE_LOOP );
		
		glVertex2f( box.min.x, box.min.y );
		glVertex2f( box.min.x, box.max.y );
		glVertex2f( box.max.x, box.max.y );
		glVertex2f( box.max.x, box.min.y );

	glEnd();
}

void StandardStyle::renderSelectionBox( const Imath::Box2f &box ) const
{
	V2f boxSize = box.size();
	float cornerRadius = min( 5.0f, min( boxSize.x, boxSize.y ) / 2.0f );

	V2f cornerSizes = V2f( cornerRadius ) / boxSize;
	glUniform1i( g_bezierParameter, 0 );
	glUniform1i( g_borderParameter, 1 );
	glUniform2f( g_borderRadiusParameter, cornerSizes.x, cornerSizes.y );
	glUniform1i( g_edgeAntiAliasingParameter, 0 );
	glUniform1i( g_textureTypeParameter, 0 );
	
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
	glPushAttrib( GL_COLOR_BUFFER_BIT );
	
	// As the image is already pre-multiplied we need to change our blend mode.
	glEnable( GL_BLEND );
	glBlendFunc( GL_ONE, GL_ONE_MINUS_SRC_ALPHA );

	glEnable( GL_TEXTURE_2D );
	glActiveTexture( GL_TEXTURE0 );
	texture->bind();
	
	glUniform1i( g_bezierParameter, 0 );
	glUniform1i( g_borderParameter, 0 );
	glUniform1i( g_edgeAntiAliasingParameter, 0 );
	glUniform1i( g_textureParameter, 0 );
	glUniform1i( g_textureTypeParameter, 1 );

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
		
	glPopAttrib();
}

void StandardStyle::renderLine( const IECore::LineSegment3f &line ) const
{
	glUniform1i( g_bezierParameter, 1 );
	glUniform1i( g_borderParameter, 0 );
	glUniform1i( g_edgeAntiAliasingParameter, 1 );
	glUniform1i( g_textureTypeParameter, 0 );
	
	glColor( getColor( BackgroundColor ) );
		
	V3f d = line.direction() / 3.0f;

	glUniform3fv( g_v0Parameter, 1, line.p0.getValue() );
	glUniform3fv( g_v1Parameter, 1, ( line.p0 + d ).getValue() ); 
	glUniform3fv( g_v2Parameter, 1, ( line.p1 - d ).getValue() ); 
	glUniform3fv( g_v3Parameter, 1, line.p1.getValue() ); 

	glCallList( connectionDisplayList() );
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

Imath::Color3f StandardStyle::colorForState( Color c, State s ) const
{
	Color3f result = m_colors[c];
	if( s == Style::HighlightedState )
	{
		result = m_colors[HighlightColor];
	}
	
	return result;
}

//////////////////////////////////////////////////////////////////////////
// glsl source
//////////////////////////////////////////////////////////////////////////

static const char *g_vertexSource =
	
	"uniform bool bezier;"
	"uniform vec3 v0;"
	"uniform vec3 v1;"
	"uniform vec3 v2;"
	"uniform vec3 v3;"

	"void main()"
	"{"
	"	if( bezier )"
	"	{"
	"		mat4 basis = mat4("
	"			-1,  3, -3,  1,"
	"			 3, -6,  3,  0,"
	"			-3,  3,  0,  0,"
	"			 1,  0,  0,  0"
	"		);"

	"		vec4 t = vec4("
	"			gl_MultiTexCoord0.y * gl_MultiTexCoord0.y * gl_MultiTexCoord0.y,"
	"			gl_MultiTexCoord0.y * gl_MultiTexCoord0.y,"
	"			gl_MultiTexCoord0.y,"
	"			1.0"
	"		);"

	"		vec4 tDeriv = vec4( t[1] * 3.0, t[2] * 2.0, 1.0, 0.0 );"
	"		vec4 w = basis * t;"
	"		vec4 wDeriv = basis * tDeriv;"

	"		vec3 p = w.x * v0 + w.y * v1 + w.z * v2 + w.w * v3;"
	"		vec3 vTangent = wDeriv.x * v0 + wDeriv.y * v1 + wDeriv.z * v2 + wDeriv.w * v3;"

	"		vec4 camZ = gl_ModelViewMatrixInverse * vec4( 0.0, 0.0, -1.0, 0.0 );"

	"		vec3 uTangent = normalize( cross( camZ.xyz, vTangent ) );"

	"		p += 0.5 * uTangent * ( gl_MultiTexCoord0.x - 0.5 );"

	"		gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * vec4( p, 1 );"
	"	}"
	"	else"
	"	{"
	"		gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;"
	"	}"
	"	gl_FrontColor = gl_Color;"
	"	gl_BackColor = gl_Color;"
	"	gl_TexCoord[0] = gl_MultiTexCoord0;"
	"}";

static const char *g_fragmentSource = 

	"#version 330 compatibility\n"
	
	"#include \"IECoreGL/FilterAlgo.h\"\n"
	"#include \"IECoreGL/ColorAlgo.h\"\n"

	"uniform bool border;"
	"uniform vec2 borderRadius;"

	"uniform bool edgeAntiAliasing;"

	"uniform int textureType;"
	"uniform sampler2D texture;"

	"uniform uint ieCoreGLNameIn;"

	"layout( location=0 ) out vec4 outColor;"
	"layout( location=1 ) out uint ieCoreGLNameOut;"

	"void main()"
	"{"
	"	outColor = gl_Color;"

	"	if( border )"
	"	{"
	"		vec2 v = max( borderRadius - gl_TexCoord[0].xy, vec2( 0.0 ) ) + max( gl_TexCoord[0].xy - vec2( 1.0 ) + borderRadius, vec2( 0.0 ) );"
	"		v /= borderRadius;"
	"		float r = length( v );"

	"		outColor = mix( outColor, vec4( 0.05, 0.05, 0.05, outColor.a ), ieFilteredStep( 0.8, r ) );"
	"		outColor.a *= ( 1.0 - ieFilteredStep( 1.0, r ) );"
	"	}"

	"	if( edgeAntiAliasing )"
	"	{"
	"		outColor.a *= ieFilteredPulse( 0.2, 0.8, gl_TexCoord[0].x );"
	"	}"

	/// \todo Deal with all colourspace nonsense outside of the shader. Ideally the shader would accept only linear"
	/// textures and output only linear data."

	"	if( textureType==1 )"
	"	{"
	"		outColor = texture2D( texture, gl_TexCoord[0].xy );"
	"		outColor = vec4( ieLinToSRGB( outColor.r ), ieLinToSRGB( outColor.g ), ieLinToSRGB( outColor.b ), ieLinToSRGB( outColor.a ) );"
	"	}"
	"	else if( textureType==2 )"
	"	{"
	"		outColor = vec4( outColor.rgb, texture2D( texture, gl_TexCoord[0].xy ).a );"
	"	}"

	"	ieCoreGLNameOut = ieCoreGLNameIn;"

	"}";

int StandardStyle::g_borderParameter;
int StandardStyle::g_borderRadiusParameter;
int StandardStyle::g_edgeAntiAliasingParameter;
int StandardStyle::g_textureParameter;
int StandardStyle::g_textureTypeParameter;
int StandardStyle::g_bezierParameter;
int StandardStyle::g_v0Parameter;
int StandardStyle::g_v1Parameter;
int StandardStyle::g_v2Parameter;
int StandardStyle::g_v3Parameter;
					
IECoreGL::Shader *StandardStyle::shader()
{
	
	static ShaderPtr g_shader = 0;
	
	if( !g_shader )
	{
		g_shader = ShaderLoader::defaultShaderLoader()->create( g_vertexSource, "", g_fragmentSource );
		g_borderParameter = g_shader->uniformParameter( "border" )->location;
		g_borderRadiusParameter = g_shader->uniformParameter( "borderRadius" )->location;
		g_edgeAntiAliasingParameter = g_shader->uniformParameter( "edgeAntiAliasing" )->location;
		g_textureParameter = g_shader->uniformParameter( "texture" )->location;
		g_textureTypeParameter = g_shader->uniformParameter( "textureType" )->location;
		g_bezierParameter = g_shader->uniformParameter( "bezier" )->location;
		g_v0Parameter = g_shader->uniformParameter( "v0" )->location;
		g_v1Parameter = g_shader->uniformParameter( "v1" )->location;
		g_v2Parameter = g_shader->uniformParameter( "v2" )->location;
		g_v3Parameter = g_shader->uniformParameter( "v3" )->location;
	}
	
	return g_shader.get();
}
