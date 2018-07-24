//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2014, John Haddon. All rights reserved.
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

#include "GafferUI/StandardStyle.h"

#include "IECoreGL/Camera.h"
#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/Font.h"
#include "IECoreGL/FontLoader.h"
#include "IECoreGL/GL.h"
#include "IECoreGL/Group.h"
#include "IECoreGL/IECoreGL.h"
#include "IECoreGL/MeshPrimitive.h"
#include "IECoreGL/Selector.h"
#include "IECoreGL/Shader.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/ShaderStateComponent.h"
#include "IECoreGL/TextureLoader.h"
#include "IECoreGL/ToGLMeshConverter.h"
#include "IECoreGL/TypedStateComponent.h"

#include "IECoreScene/Font.h"
#include "IECoreScene/MeshPrimitive.h"

#include "OpenEXR/ImathVecAlgo.h"

#include "boost/tokenizer.hpp"

using namespace GafferUI;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreGL;
using namespace Imath;
using namespace std;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

const float g_endPointSize = 2.0f;

Imath::Color4f colorForAxes( Style::Axes axes )
{
	switch( axes )
	{
		case Style::X :
			return Color4f( 0.73, 0.17, 0.17, 1.0f );
		case Style::Y :
			return Color4f( 0.2, 0.57, 0.2, 1.0f );
		case Style::Z :
			return Color4f( 0.2, 0.36, 0.74, 1.0f );
		default :
			return Color4f( 0.8, 0.8, 0.8, 0.0f );
	}
}

IECoreGL::GroupPtr line( const V3f &p0, const V3f &p1 )
{
	IntVectorDataPtr vertsPerCurve = new IntVectorData();
	vertsPerCurve->writable().push_back( 2 );
	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( CubicBasisf::linear(), false, vertsPerCurve );
	V3fVectorDataPtr verts = new V3fVectorData();
	verts->writable().push_back( p0 );
	verts->writable().push_back( p1 );
	curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, verts ) );

	IECoreGL::GroupPtr result = new IECoreGL::Group();
	result->addChild( curves );
	result->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
	result->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 2.0f ) );
	result->getState()->add( new IECoreGL::LineSmoothingStateComponent( true ) );

	return result;
}

IECoreGL::MeshPrimitivePtr cylinder()
{
	static IECoreGL::MeshPrimitivePtr result;
	if( result )
	{
		return result;
	}

	/// \todo Move this bit to IECore::MeshPrimitive::createCyclinder().
	IECore::IntVectorDataPtr verticesPerFaceData = new IECore::IntVectorData;
	vector<int> &verticesPerFace = verticesPerFaceData->writable();

	IECore::IntVectorDataPtr vertexIdsData = new IECore::IntVectorData;
	vector<int> &vertexIds = vertexIdsData->writable();

	IECore::V3fVectorDataPtr pData = new IECore::V3fVectorData;
	vector<V3f> &p = pData->writable();

	const float height = 1.0f;
	const float radius = 0.03f;

	const int numDivisions = 30;
	for( int i = 0; i < numDivisions; ++i )
	{
		const float angle = 2 * M_PI * (float)i/(float)(numDivisions-1);

		p.push_back( V3f( radius * cos( angle ), 0, radius * sin( angle ) ) );
		p.push_back( V3f( radius * cos( angle ), height, radius * sin( angle ) ) );

		verticesPerFace.push_back( 4 );

		vertexIds.push_back( i * 2 );
		vertexIds.push_back( i * 2 + 1 );

		const int ii = i == numDivisions - 1 ? 0 : i + 1;

		vertexIds.push_back( ii * 2 + 1 );
		vertexIds.push_back( ii * 2 );
	}

	IECoreScene::MeshPrimitivePtr mesh = new IECoreScene::MeshPrimitive( verticesPerFaceData, vertexIdsData, "linear", pData );
	IECoreGL::ToGLMeshConverterPtr converter = new ToGLMeshConverter( mesh );
	result = runTimeCast<IECoreGL::MeshPrimitive>( converter->convert() );

	return result;
}

IECoreGL::MeshPrimitivePtr torus()
{
	static IECoreGL::MeshPrimitivePtr result;
	if( result )
	{
		return result;
	}

	/// \todo Move this bit to IECore::MeshPrimitive::createTorus().
	IECore::IntVectorDataPtr verticesPerFaceData = new IECore::IntVectorData;
	vector<int> &verticesPerFace = verticesPerFaceData->writable();

	IECore::IntVectorDataPtr vertexIdsData = new IECore::IntVectorData;
	vector<int> &vertexIds = vertexIdsData->writable();

	IECore::V3fVectorDataPtr pData = new IECore::V3fVectorData;
	vector<V3f> &p = pData->writable();

	const float radiusI = 1;
	const float radiusJ = 0.03;

	const int numDivisionsI = 30;
	const int numDivisionsJ = 15;
	for( int i = 0; i < numDivisionsI; ++i )
	{
		const float iAngle = 2 * M_PI * (float)i/(float)(numDivisionsI-1);
		const V3f v( cos( iAngle ), 0, sin( iAngle ) );
		const V3f circleCenter = v * radiusI;

		const int ii = i == numDivisionsI - 1 ? 0 : i + 1;

		for( int j = 0; j < numDivisionsJ; ++j )
		{
			const float jAngle = 2 * M_PI * (float)j/(float)(numDivisionsJ-1);
			p.push_back(
				circleCenter + radiusJ * ( cos( jAngle ) * v + V3f( 0, sin( jAngle ), 0 ) )
			);

			const int jj = j == numDivisionsJ - 1 ? 0 : j + 1;

			verticesPerFace.push_back( 4 );

			vertexIds.push_back( i * numDivisionsJ + j );
			vertexIds.push_back( i * numDivisionsJ + jj );
			vertexIds.push_back( ii * numDivisionsJ + jj );
			vertexIds.push_back( ii * numDivisionsJ + j );
		}
	}

	IECoreScene::MeshPrimitivePtr mesh = new IECoreScene::MeshPrimitive( verticesPerFaceData, vertexIdsData, "linear", pData );
	IECoreGL::ToGLMeshConverterPtr converter = new ToGLMeshConverter( mesh );
	result = runTimeCast<IECoreGL::MeshPrimitive>( converter->convert() );

	return result;
}

IECoreGL::MeshPrimitivePtr cone()
{
	static IECoreGL::MeshPrimitivePtr result;
	if( result )
	{
		return result;
	}

	/// \todo Move this bit to IECore::MeshPrimitive::createCone().
	IECore::IntVectorDataPtr verticesPerFaceData = new IECore::IntVectorData;
	vector<int> &verticesPerFace = verticesPerFaceData->writable();

	IECore::IntVectorDataPtr vertexIdsData = new IECore::IntVectorData;
	vector<int> &vertexIds = vertexIdsData->writable();

	IECore::V3fVectorDataPtr pData = new IECore::V3fVectorData;
	vector<V3f> &p = pData->writable();

	const float height = 1.5f;
	const float radius = 0.5f;

	p.push_back( V3f( 0, height, 0 ) );

	const int numDivisions = 30;
	for( int i = 0; i < numDivisions; ++i )
	{
		const float angle = 2 * M_PI * (float)i/(float)(numDivisions-1);
		p.push_back( radius * V3f( cos( angle ), 0, sin( angle ) ) );
		verticesPerFace.push_back( 3 );
		vertexIds.push_back( 0 );
		vertexIds.push_back( i + 1 );
		vertexIds.push_back( i == numDivisions - 1 ? 1 : i + 2 );
	}

	IECoreScene::MeshPrimitivePtr mesh = new IECoreScene::MeshPrimitive( verticesPerFaceData, vertexIdsData, "linear", pData );
	IECoreGL::ToGLMeshConverterPtr converter = new ToGLMeshConverter( mesh );
	result = runTimeCast<IECoreGL::MeshPrimitive>( converter->convert() );

	return result;
}

IECoreGL::MeshPrimitivePtr cube()
{
	static IECoreGL::MeshPrimitivePtr result;
	if( result )
	{
		return result;
	}

	IECoreScene::MeshPrimitivePtr mesh = IECoreScene::MeshPrimitive::createBox(
		Box3f( V3f( -1 ), V3f( 1 ) )
	);

	IECoreGL::ToGLMeshConverterPtr converter = new ToGLMeshConverter( mesh );
	result = runTimeCast<IECoreGL::MeshPrimitive>( converter->convert() );

	return result;
}

IECoreGL::GroupPtr translateHandle( Style::Axes axes )
{
	if( axes < Style::X || axes > Style::Z )
	{
		throw Exception( "Unsupported axes" );
	}
	const int axis = (int)axes;

	static IECoreGL::GroupPtr handles[3];
	if( handles[axis] )
	{
		return handles[axis];
	}

	IECoreGL::GroupPtr coneGroup = new IECoreGL::Group;
	coneGroup->addChild( cone() );
	coneGroup->setTransform( M44f().scale( V3f( 0.25 ) ) * M44f().translate( V3f( 0, 1, 0 ) ) );

	IECoreGL::GroupPtr group = new IECoreGL::Group;;

	// Line ensures minimum width when very small on screen,
	// like the corner gnomon in the SceneView.
	group->addChild( line( V3f( 0 ), V3f( 0, 1, 0 ) ) );
	// Cylinder provides a chunkier handle for picking when
	// bigger on screen, like the TranslateHandle.
	group->addChild( cylinder() );
	group->addChild( coneGroup );

	group->getState()->add( new IECoreGL::Color( colorForAxes( axes ) ) );
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), "", "", IECoreGL::Shader::constantFragmentSource(), new CompoundObject )
	);

	if( axis == 0 )
	{
		group->setTransform( M44f().rotate( V3f( 0, 0, -M_PI / 2.0f ) ) );
	}
	else if( axis == 2 )
	{
		group->setTransform( M44f().rotate( V3f( M_PI / 2.0f, 0, 0 ) ) );
	}

	handles[axis] = group;
	return group;
}

IECoreGL::GroupPtr rotateHandle( Style::Axes axes )
{
	if( axes < Style::X || axes > Style::Z )
	{
		throw Exception( "Unsupported axes" );
	}
	const int axis = (int)axes;

	static IECoreGL::GroupPtr handles[3];
	if( handles[axis] )
	{
		return handles[axis];
	}

	IECoreGL::GroupPtr group = new IECoreGL::Group;
	group->addChild( torus() );

	group->getState()->add( new IECoreGL::Color( colorForAxes( axes ) ) );
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), "", "", IECoreGL::Shader::constantFragmentSource(), new CompoundObject )
	);

	if( axis == 0 )
	{
		group->setTransform( M44f().rotate( V3f( 0, 0, -M_PI / 2.0f ) ) );
	}
	else if( axis == 2 )
	{
		group->setTransform( M44f().rotate( V3f( M_PI / 2.0f, 0, 0 ) ) );
	}

	handles[axis] = group;
	return group;
}

IECoreGL::GroupPtr scaleHandle( Style::Axes axes )
{
	if( axes < Style::X || axes > Style::XYZ )
	{
		throw Exception( "Unsupported axes" );
	}

	static IECoreGL::GroupPtr handles[4];
	if( handles[axes] )
	{
		return handles[axes];
	}

	IECoreGL::GroupPtr cubeGroup = new IECoreGL::Group;
	cubeGroup->addChild( cube() );
	cubeGroup->setTransform( M44f().scale( V3f( 0.1 ) ) * M44f().translate( V3f( 0, axes == Style::XYZ ? 0 : 1, 0 ) ) );

	IECoreGL::GroupPtr group = new IECoreGL::Group;;

	if( axes <= Style::Z )
	{
		group->addChild( cylinder() );
	}
	group->addChild( cubeGroup );

	group->getState()->add( new IECoreGL::Color( colorForAxes( axes ) ) );
	group->getState()->add(
		new IECoreGL::ShaderStateComponent( ShaderLoader::defaultShaderLoader(), TextureLoader::defaultTextureLoader(), "", "", IECoreGL::Shader::constantFragmentSource(), new CompoundObject )
	);

	if( axes == Style::X )
	{
		group->setTransform( M44f().rotate( V3f( 0, 0, -M_PI / 2.0f ) ) );
	}
	else if( axes == Style::Z )
	{
		group->setTransform( M44f().rotate( V3f( M_PI / 2.0f, 0, 0 ) ) );
	}

	handles[axes] = group;
	return group;
}

IECoreGL::StatePtr disabledState()
{
	static IECoreGL::StatePtr s;
	if( s )
	{
		return s;
	}

	s = new IECoreGL::State( /* complete = */ false );
	s->add( new IECoreGL::Color( Color4f( 0.4, 0.4, 0.4, 1.0 ) ), /* override = */ true );

	return s;
}

// - p is connection destination (guaranteed to be contained within the frame)
// - v is the vector between source and destination
V3f auxiliaryConnectionArrowPosition( const Box2f &dstNodeFrame, const V3f &p, const V3f &v )
{
	const float offset = 1.0;

	float xT = limits<float>::max();
	if( v.x > 0 )
	{
		xT = ( offset + dstNodeFrame.max.x - p.x ) / v.x;
	}
	else if( v.x < 0 )
	{
		xT = ( offset + p.x - dstNodeFrame.min.x ) / -v.x;
	}

	float yT = limits<float>::max();
	if( v.y > 0 )
	{
		yT = ( offset + dstNodeFrame.max.y - p.y ) / v.y;
	}
	else if( v.y < 0 )
	{
		yT = ( offset + p.y - dstNodeFrame.min.y ) / -v.y;
	}

	const float t = min( min( xT, yT ), 1.0f );
	return p + v * t;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// StandardStyle
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( StandardStyle );

StandardStyle::StandardStyle()
	:	m_highlightState( new IECoreGL::State( /* complete = */ false ) )
{
	setFont( LabelText, FontLoader::defaultFontLoader()->load( "VeraBd.ttf" ) );
	setFontScale( LabelText, 1.0f );

	setFont( BodyText, FontLoader::defaultFontLoader()->load( "Vera.ttf" ) );
	setFontScale( BodyText, 1.0f );

	setFont( HeadingText, FontLoader::defaultFontLoader()->load( "VeraBd.ttf" ) );
	setFontScale( HeadingText, 2.0f );

	setColor( BackgroundColor, Color3f( 0.1 ) );
	setColor( SunkenColor, Color3f( 0.1 ) );
	setColor( RaisedColor, Color3f( 0.4 ) );
	setColor( ForegroundColor, Color3f( 0.9 ) );
	setColor( HighlightColor, Color3f( 0.466, 0.612, 0.741 ) );
	setColor( ConnectionColor, Color3f( 0.125, 0.125, 0.125 ) );
	setColor( AuxiliaryConnectionColor, Color3f( 0.3, 0.45, 0.3 ) );
	setColor( CurveColor, Color3f( 1.0, 1.0, 1.0 ) );
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
		if( selector->mode() == Selector::IDRender )
		{
			selector->pushIDShader( shader() );
		}
	}
}

Imath::Box3f StandardStyle::characterBound( TextType textType ) const
{
	Imath::Box2f b = m_fonts[textType]->coreFont()->bound();
	return Imath::Box3f(
		m_fontScales[textType] * Imath::V3f( b.min.x, b.min.y, 0 ),
		m_fontScales[textType] * Imath::V3f( b.max.x, b.max.y, 0 )
	);
}

Imath::Box3f StandardStyle::textBound( TextType textType, const std::string &text ) const
{
	Imath::Box2f b = m_fonts[textType]->coreFont()->bound( text );
	return Imath::Box3f(
		m_fontScales[textType] * Imath::V3f( b.min.x, b.min.y, 0 ),
		m_fontScales[textType] * Imath::V3f( b.max.x, b.max.y, 0 )
	);
}

void StandardStyle::renderText( TextType textType, const std::string &text, State state, const Imath::Color3f *userColor ) const
{
	glEnable( GL_TEXTURE_2D );
	glActiveTexture( GL_TEXTURE0 );
	m_fonts[textType]->texture()->bind();
	glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR );
	glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR );
	glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_LOD_BIAS, -1.25 );

	glUniform1i( g_isCurveParameter, 0 );
	glUniform1i( g_borderParameter, 0 );
	glUniform1i( g_edgeAntiAliasingParameter, 0 );
	glUniform1i( g_textureParameter, 0 );
	/// \todo IECore is currently providing sRGB data in IECore::Font::image() and therefore
	/// in IECoreGL::Font::texture(). Either we should change image() to return linear data,
	/// or use the sRGB texture extension in IECoreGL::Font::texture() to ensure that data is
	/// automatically linearised before arriving in the shader.
	glUniform1i( g_textureTypeParameter, 2 );

	glColor( colorForState( ForegroundColor, state, userColor ) );

	glPushMatrix();

		glScalef( m_fontScales[textType], m_fontScales[textType], m_fontScales[textType] );
		m_fonts[textType]->renderSprites( text );

	glPopMatrix();
}

void StandardStyle::renderWrappedText( TextType textType, const std::string &text, const Imath::Box2f &bound, State state ) const
{
	IECoreGL::Font *glFont = m_fonts[textType].get();
	const IECoreScene::Font *coreFont = glFont->coreFont();

	const float spaceWidth = coreFont->bound().size().x * 0.25;
	const float descent = coreFont->bound().min.y;
	const float newlineHeight = coreFont->bound().size().y * 1.2;

	V2f cursor( bound.min.x, bound.max.y - coreFont->bound().size().y );

	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
	boost::char_separator<char> separator( "", " \n\t" );
	Tokenizer tokenizer( text, separator );
	Tokenizer::iterator it = tokenizer.begin();
	while( it != tokenizer.end() && ( cursor.y + descent ) > bound.min.y )
	{
		if( *it == "\n" )
		{
			cursor.x = bound.min.x;
			cursor.y -= newlineHeight;
		}
		else if( *it == " " )
		{
			cursor.x += spaceWidth;
		}
		else if( *it == "\t" )
		{
			cursor.x += spaceWidth	* 4;
		}
		else
		{
			const float width = coreFont->bound( *it ).size().x;
			if( cursor.x + width > bound.max.x )
			{
				cursor.x = bound.min.x;
				cursor.y -= newlineHeight;
				// moving the cursor down might have sent us
				// out of the bound, in which case we must stop.
				if( ( cursor.y + descent ) < bound.min.y )
				{
					break;
				}
			}

			glPushMatrix();
				glTranslatef( cursor.x, cursor.y, 0.0f );
				renderText( textType, *it, state );
				cursor.x += width;
			glPopMatrix();
		}

		++it;
	}
}

void StandardStyle::renderFrame( const Imath::Box2f &frame, float borderWidth, State state ) const
{
	renderNodeFrame( frame, borderWidth, state );
}

void StandardStyle::renderNodeFrame( const Imath::Box2f &contents, float borderWidth, State state, const Imath::Color3f *userColor ) const
{

	Box2f b = contents;
	V2f bw( borderWidth );
	b.min -= bw;
	b.max += bw;

	V2f cornerSizes = bw / b.size();
	glUniform1i( g_isCurveParameter, 0 );
	glUniform1i( g_borderParameter, 1 );
	glUniform2f( g_borderRadiusParameter, cornerSizes.x, cornerSizes.y );
	glUniform1f( g_borderWidthParameter, 0.15f / borderWidth );
	glUniform1i( g_edgeAntiAliasingParameter, 0 );
	glUniform1i( g_textureTypeParameter, 0 );

	glColor( colorForState( RaisedColor, state, userColor ) );

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

void StandardStyle::renderNodule( float radius, State state, const Imath::Color3f *userColor ) const
{
	glUniform1i( g_isCurveParameter, 0 );
	glUniform1i( g_borderParameter, 1 );
	glUniform2f( g_borderRadiusParameter, 0.5f, 0.5f );
	glUniform1f( g_borderWidthParameter, 0.2f );
	glUniform1i( g_edgeAntiAliasingParameter, 0 );
	glUniform1i( g_textureTypeParameter, 0 );

	glColor( colorForState( RaisedColor, state, userColor ) );

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

void StandardStyle::renderConnection( const Imath::V3f &srcPosition, const Imath::V3f &srcTangent, const Imath::V3f &dstPosition, const Imath::V3f &dstTangent, State state, const Imath::Color3f *userColor ) const
{
	glUniform1f( g_lineWidthParameter, 0.5 );
	glColor( colorForState( ConnectionColor, state, userColor ) );

	renderConnectionInternal( srcPosition, srcTangent, dstPosition, dstTangent );
}

void StandardStyle::renderAuxiliaryConnection( const Imath::Box2f &srcNodeFrame, const Imath::Box2f &dstNodeFrame, State state ) const
{
	glUniform1i( g_isCurveParameter, 1 );
	glUniform1i( g_borderParameter, 0 );
	glUniform1i( g_edgeAntiAliasingParameter, 1 );
	glUniform1i( g_textureTypeParameter, 0 );
	glUniform1f( g_lineWidthParameter, 0.2 );

	glColor( colorForState( AuxiliaryConnectionColor, state ) );

	// Get basic properties of a line between the src and dst nodes

	V3f p0( srcNodeFrame.center().x, srcNodeFrame.center().y, 0 );
	V3f p1( dstNodeFrame.center().x, dstNodeFrame.center().y, 0 );

	const V3f direction = ( p1 - p0 ).normalized();
	const V3f normal( direction.y, -direction.x, 0 );

	// Offset the line slightly to one side. This separates connections
	// going in opposite directions between the same two nodes.

	p0 += normal * 0.3f;
	p1 += normal * 0.3f;

	// Draw the line

	glUniform3fv( g_v0Parameter, 1, ( p0 ).getValue() );
	glUniform3fv( g_v1Parameter, 1, ( p1 ).getValue() );
	glUniform3fv( g_t0Parameter, 1, ( direction ).getValue() );
	glUniform3fv( g_t1Parameter, 1, ( -direction ).getValue() );

	glCallList( connectionDisplayList() );

	// Draw a little arrow to indicate connection direction.

	const V3f tip = auxiliaryConnectionArrowPosition( dstNodeFrame, p1, p0 - p1 );

	const V3f leftDir = -direction + normal * 0.5f;
	const V3f rightDir = -direction - normal * 0.5f;

	glUniform3fv( g_v0Parameter, 1, ( tip ).getValue() );
	glUniform3fv( g_v1Parameter, 1, ( tip + leftDir * 0.75 ).getValue() );
	glUniform3fv( g_t0Parameter, 1, ( leftDir ).getValue() );
	glUniform3fv( g_t1Parameter, 1, ( -leftDir ).getValue() );

	glCallList( connectionDisplayList() );

	glUniform3fv( g_v1Parameter, 1, ( tip + rightDir * 0.75 ).getValue() );
	glUniform3fv( g_t0Parameter, 1, ( rightDir ).getValue() );
	glUniform3fv( g_t1Parameter, 1, ( -rightDir ).getValue() );

	glCallList( connectionDisplayList() );

}

void StandardStyle::renderAuxiliaryConnection( const Imath::V2f &srcPosition, const Imath::V2f &srcTangent, const Imath::V2f &dstPosition, const Imath::V2f &dstTangent, State state ) const
{
	glUniform1f( g_lineWidthParameter, 0.2 );
	glColor( colorForState( AuxiliaryConnectionColor, state ) );

	const V3f p0( srcPosition.x, srcPosition.y, 0 );
	const V3f p1( dstPosition.x, dstPosition.y, 0 );
	const V3f t0( srcTangent.x, srcTangent.y, 0 );
	const V3f t1( dstTangent.x, dstTangent.y, 0 );

	renderConnectionInternal( p0, t0, p1, t1 );
}

Imath::V3f StandardStyle::closestPointOnConnection( const Imath::V3f &p, const Imath::V3f &srcPosition, const Imath::V3f &srcTangent, const Imath::V3f &dstPosition, const Imath::V3f &dstTangent ) const
{
	V3f dir = ( dstPosition - srcPosition ).normalized();

	V3f offsetCenter0 = srcPosition + ( srcTangent != V3f( 0 ) ? srcTangent :  dir ) * g_endPointSize;
	V3f offsetCenter1 = dstPosition + ( dstTangent != V3f( 0 ) ? dstTangent :  -dir ) * g_endPointSize;

	float straightSegmentLength = ( offsetCenter0 - offsetCenter1 ).length();

	if( straightSegmentLength < 2.0f * g_endPointSize )
	{
		// The curve is short enough that there is no straight segment, and the rendering code will
		// have to do something a bit fancier to compute the actual curve radius, but inserting dots into
		// exceedingly short curves isn't that common, lets just do a simple and fairly reasonable thing,
		// and take the center point.
		return 0.5f * ( dstPosition + srcPosition );
	}
	else
	{
		V3f straightSegmentCenter = 0.5f * ( offsetCenter0 + offsetCenter1 );
		V3f straightSegmentDir = ( offsetCenter0 - offsetCenter1 ).normalized();

		float alongSegment = ( p - straightSegmentCenter ).dot( straightSegmentDir );
		float clampDist = straightSegmentLength * 0.5f - g_endPointSize;
		alongSegment = std::max( -clampDist, std::min( clampDist, alongSegment ) );

		return straightSegmentCenter + alongSegment * straightSegmentDir;
	}

}

void StandardStyle::renderSolidRectangle( const Imath::Box2f &box ) const
{
	glUniform1i( g_isCurveParameter, 0 );
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
	glUniform1i( g_isCurveParameter, 0 );
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

void StandardStyle::renderCurveSegment( const Imath::V2f &start, const Imath::V2f &end, const Imath::V2f &startTangent, const Imath::V2f &endTangent, State state, const Imath::Color3f *userColor ) const
{
	glUniform1i( g_isCurveParameter, 1 );
	glUniform1i( g_borderParameter, 0 );
	glUniform1f( g_edgeAntiAliasingParameter, 1 );
	glUniform1i( g_textureTypeParameter, 0 );
	glUniform1f( g_lineWidthParameter, 3.0 );

	glColor( colorForState( CurveColor, state, userColor ) );

	// \todo: The rendering interface here should probably eventually work on V2f's instead?
	//        The function signature anticipates that eventual switch,
	//        but that's easy enough to revert if not desired. For now, do a conversion...
	Imath::V3f _start = Imath::V3f( start.x, start.y, 0 );
	Imath::V3f _end = Imath::V3f( end.x, end.y, 0 );
	Imath::V3f _startTangent = Imath::V3f( startTangent.x, startTangent.y, 0 );
	Imath::V3f _endTangent = Imath::V3f( endTangent.x, endTangent.y, 0 );

	V3f dir = ( _end - _start ).normalized();

	glUniform3fv( g_v0Parameter, 1, _start.getValue() );
	glUniform3fv( g_v1Parameter, 1, _end.getValue() );
	glUniform3fv( g_t0Parameter, 1, ( _startTangent != V3f( 0 ) ? _startTangent :  dir ).getValue() );
	glUniform3fv( g_t1Parameter, 1, ( _endTangent != V3f( 0 ) ? _endTangent : -dir ).getValue() );

	glUniform1f( g_endPointSizeParameter, g_endPointSize );

	glCallList( connectionDisplayList() );
}

void StandardStyle::renderKeyFrame( const Imath::V2f &position, State state, float size, const Imath::Color3f *userColor ) const
{
	glColor( colorForState( CurveColor, state, userColor ) );
	renderSolidRectangle( Box2f( position - V2f( size ), position + V2f( size ) ) );
}

void StandardStyle::renderBackdrop( const Imath::Box2f &box, State state, const Imath::Color3f *userColor ) const
{
	glColor( userColor ? *userColor : m_colors[RaisedColor] );

	renderSolidRectangle( box );
	if( state == HighlightedState )
	{
		glColor( m_colors[HighlightColor] );
		renderRectangle( box );
	}
}

void StandardStyle::renderSelectionBox( const Imath::Box2f &box ) const
{
	V2f boxSize = box.size();
	float cornerRadius = min( 5.0f, min( boxSize.x, boxSize.y ) / 2.0f );

	V2f cornerSizes = V2f( cornerRadius ) / boxSize;
	glUniform1i( g_isCurveParameter, 0 );
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

void StandardStyle::renderHorizontalRule( const Imath::V2f &center, float length, State state ) const
{

	glColor( state == HighlightedState ? m_colors[HighlightColor] : m_colors[ForegroundColor] );

	glUniform1i( g_isCurveParameter, 0 );
	glUniform1i( g_borderParameter, 0 );
	glUniform1i( g_edgeAntiAliasingParameter, 0 );
	glUniform1i( g_textureTypeParameter, 0 );

	glBegin( GL_LINES );

		glVertex2f( center.x - length / 2.0f, center.y );
		glVertex2f( center.x + length / 2.0f, center.y );

	glEnd();

}

void StandardStyle::renderTranslateHandle( Axes axes, State state ) const
{
	IECoreGL::State::bindBaseState();
	IECoreGL::State *glState = const_cast<IECoreGL::State *>( IECoreGL::State::defaultState() );
	IECoreGL::State::ScopedBinding highlight( *m_highlightState, *glState, state == HighlightedState );
	IECoreGL::State::ScopedBinding disabled( *disabledState(), *glState, state == DisabledState );
	translateHandle( axes )->render( glState );
}

void StandardStyle::renderRotateHandle( Axes axes, State state ) const
{
	IECoreGL::State::bindBaseState();
	IECoreGL::State *glState = const_cast<IECoreGL::State *>( IECoreGL::State::defaultState() );
	IECoreGL::State::ScopedBinding highlight( *m_highlightState, *glState, state == HighlightedState );
	IECoreGL::State::ScopedBinding disabled( *disabledState(), *glState, state == DisabledState );
	rotateHandle( axes )->render( glState );
}

void StandardStyle::renderScaleHandle( Axes axes, State state ) const
{
	IECoreGL::State::bindBaseState();
	IECoreGL::State *glState = const_cast<IECoreGL::State *>( IECoreGL::State::defaultState() );
	IECoreGL::State::ScopedBinding highlight( *m_highlightState, *glState, state == HighlightedState );
	IECoreGL::State::ScopedBinding disabled( *disabledState(), *glState, state == DisabledState );
	scaleHandle( axes )->render( glState );
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

	glUniform1i( g_isCurveParameter, 0 );
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


void StandardStyle::renderLine( const IECore::LineSegment3f &line, float width, const Imath::Color3f *userColor ) const
{
	glUniform1i( g_isCurveParameter, 1 );
	glUniform1i( g_borderParameter, 0 );
	glUniform1i( g_edgeAntiAliasingParameter, 1 );
	glUniform1i( g_textureTypeParameter, 0 );
	glUniform1f( g_lineWidthParameter, width );

	if( userColor )
	{
		glColor( *userColor );
	}
	else
	{
		glColor( getColor( BackgroundColor ) );
	}

	V3f d = line.normalizedDirection();

	glUniform3fv( g_v0Parameter, 1, line.p0.getValue() );
	glUniform3fv( g_v1Parameter, 1, line.p1.getValue() );
	glUniform3fv( g_t0Parameter, 1, ( d ).getValue() );
	glUniform3fv( g_t1Parameter, 1, ( -d ).getValue() );

	glCallList( connectionDisplayList() );
}

void StandardStyle::setColor( Color c, Imath::Color3f v )
{
	if( m_colors[c] == v )
	{
		return;
	}

	m_colors[c] = v;
	if( c == HighlightColor )
	{
		m_highlightState->add( new IECoreGL::Color( Color4f( v[0], v[1], v[2], 1.0f ) ), /* override = */ true );
	}

	changedSignal()( this );
}

const Imath::Color3f &StandardStyle::getColor( Color c ) const
{
	return m_colors[c];
}

void StandardStyle::setFont( TextType textType, IECoreGL::FontPtr font )
{
	if( m_fonts[textType] == font )
	{
		return;
	}
	m_fonts[textType] = font;
	changedSignal()( this );
}

const IECoreGL::Font *StandardStyle::getFont( TextType textType ) const
{
	return m_fonts[textType].get();
}

void StandardStyle::setFontScale( TextType textType, float scale )
{
	if( m_fontScales[textType] == scale )
	{
		return;
	}
	m_fontScales[textType] = scale;
	changedSignal()( this );
}

float StandardStyle::getFontScale( TextType textType ) const
{
	return m_fontScales[textType];
}

void StandardStyle::renderConnectionInternal( const Imath::V3f &srcPosition, const Imath::V3f &srcTangent, const Imath::V3f &dstPosition, const Imath::V3f &dstTangent ) const
{
	glUniform1i( g_isCurveParameter, 1 );
	glUniform1i( g_borderParameter, 0 );
	glUniform1i( g_edgeAntiAliasingParameter, 1 );
	glUniform1i( g_textureTypeParameter, 0 );

	// To guarantee straight curve sections we add an offset when computing
	// tangents. This is done because the effective end point is slightly shifted
	// due to how we draw curves at where they hit a node.
	V3f adjustedSrcPosition( srcPosition );
	if( dstTangent == V3f( 0 ) && srcTangent != V3f( 0 ) )
	{
		adjustedSrcPosition += srcTangent * g_endPointSize;
	}

	V3f adjustedDstPosition( dstPosition );
	if( srcTangent == V3f( 0 ) && dstTangent != V3f( 0 ) )
	{
		adjustedDstPosition += dstTangent * g_endPointSize;
	}

	V3f dir = ( adjustedDstPosition - adjustedSrcPosition ).normalized();

	glUniform3fv( g_v0Parameter, 1, srcPosition.getValue() );
	glUniform3fv( g_v1Parameter, 1, dstPosition.getValue() );
	glUniform3fv( g_t0Parameter, 1, ( srcTangent != V3f( 0 ) ? srcTangent :  dir ).getValue() );
	glUniform3fv( g_t1Parameter, 1, ( dstTangent != V3f( 0 ) ? dstTangent : -dir ).getValue() );

	glUniform1f( g_endPointSizeParameter, g_endPointSize );

	glCallList( connectionDisplayList() );
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

Imath::Color3f StandardStyle::colorForState( Color c, State s, const Imath::Color3f *userColor ) const
{
	Color3f result = userColor ? *userColor : m_colors[c];
	if( s == Style::HighlightedState )
	{
		result = m_colors[HighlightColor];
	}

	return result;
}

//////////////////////////////////////////////////////////////////////////
// glsl source
//////////////////////////////////////////////////////////////////////////

static const std::string &vertexSource()
{
	// When isCurve is set, this renders a curve defined by start and end points, and start and end tangents.
	// See contrib/dd/notes/noodleShapes.svg for explanation.
	static const std::string g_vertexSource =

		"uniform bool isCurve;"
		"uniform vec3 v0;"
		"uniform vec3 v1;"
		"uniform vec3 t0;"
		"uniform vec3 t1;"
		"uniform float endPointSize;"
		"uniform float lineWidth;"

		"void main()"
		"{"
		"	if( isCurve )"
		"	{"
				// Compute the largest possible end point size that doesn't create overlapping endPointCircles
		"		float a = dot( t0 - t1, t0 - t1 ) - 4.0;"
		"		float b = 2.0 *  dot( v0 - v1, t0 - t1 );"
		"		float c = dot( v0 - v1, v0 - v1 );"
		"		float maxEndPointSize = abs( a ) < 0.0001 ? abs( c / b ) : ( -b - sqrt( b * b - 4.0 * a * c ) ) / ( 2.0 * a );"
				// If the end point size would create overlapping circles, clamp it
		"		float effectiveEndPointSize = min( endPointSize, maxEndPointSize );"

		"		vec3 offsetCenter0 = v0 + effectiveEndPointSize * t0;"
		"		vec3 offsetCenter1 = v1 + effectiveEndPointSize * t1;"
		"		vec3 straight = normalize( offsetCenter0 - offsetCenter1 );"

				// The remainder of the math doesn't need to be done for both ends of the curve,
				// only the end we're on.
		"		vec3 endPoint = gl_MultiTexCoord0.y > 0.5 ? v1 : v0;"
		"		vec3 endTangent = gl_MultiTexCoord0.y > 0.5 ? t1 : t0;"
		"		vec3 straightDir = gl_MultiTexCoord0.y > 0.5 ? straight : -straight;"
		"		float t = min( gl_MultiTexCoord0.y, 1.0 - gl_MultiTexCoord0.y ) * 2.0;"

		"		vec4 camZ = gl_ModelViewMatrixInverse * vec4( 0.0, 0.0, -1.0, 0.0 );"

		"		vec3 endTangentPerp = normalize( cross( camZ.xyz, endTangent ) );"
		"		float cosAngle = dot( endTangent, straightDir );"
		"		float angle = acos( cosAngle );"

				// Calculate the radius of a circle defined by the endPoint / endTangent and the location
				// and tangent of the line between the offsetCenters
		"		float radius = effectiveEndPointSize * ( 1.0 + cosAngle ) / sqrt( 1.0 - cosAngle * cosAngle );"
		"		float bendDir = sign( dot( endTangentPerp, straightDir ) );"

		"		vec3 p = abs(cosAngle) > 0.9999 ? endPoint + 2.0 * t * effectiveEndPointSize * endTangent : endPoint + radius * ( ( 1.0 - cos( angle * t ) ) * bendDir * endTangentPerp + sin( angle * t ) * endTangent );"
		"		vec3 uTangent = ( gl_MultiTexCoord0.y > 0.5 ? 1.0 : -1.0 ) * ( abs(cosAngle) > 0.9999 ? -endTangentPerp : bendDir * normalize( p - ( endPoint + radius * bendDir * endTangentPerp) ) );"

		"		p += lineWidth * uTangent * ( gl_MultiTexCoord0.x - 0.5 );"

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

	return g_vertexSource;
}

static const std::string &fragmentSource()
{

	static std::string g_fragmentSource;
	if( g_fragmentSource.empty() )
	{

		g_fragmentSource =

		"#include \"IECoreGL/FilterAlgo.h\"\n"
		"#include \"IECoreGL/ColorAlgo.h\"\n"

		"uniform bool border;"
		"uniform vec2 borderRadius;"
		"uniform float borderWidth;"

		"uniform bool edgeAntiAliasing;"

		"uniform int textureType;"
		"uniform sampler2D texture;\n"

		"#if __VERSION__ >= 330\n"

		"uniform uint ieCoreGLNameIn;\n"
		"layout( location=0 ) out vec4 outColor;\n"
		"layout( location=1 ) out uint ieCoreGLNameOut;\n"
		"#define OUTCOLOR outColor\n"

		"#else\n"

		"#define OUTCOLOR gl_FragColor\n"

		"#endif\n"

		"void main()"
		"{"
		"	OUTCOLOR = gl_Color;"

		"	if( border )"
		"	{"
		"		vec2 v = max( borderRadius - gl_TexCoord[0].xy, vec2( 0.0 ) ) + max( gl_TexCoord[0].xy - vec2( 1.0 ) + borderRadius, vec2( 0.0 ) );"
		"		v /= borderRadius;"
		"		float r = length( v );"

		"		OUTCOLOR = mix( OUTCOLOR, vec4( 0.15, 0.15, 0.15, OUTCOLOR.a ), ieFilteredStep( 1.0 - borderWidth, r ) );"
		"		OUTCOLOR.a *= ( 1.0 - ieFilteredStep( 1.0, r ) );"
		"	}"

		"	if( edgeAntiAliasing )"
		"	{"
		"		OUTCOLOR.a *= ieFilteredPulse( 0.2, 0.8, gl_TexCoord[0].x );"
		"	}"

		"	if( OUTCOLOR.a == 0.0 )"
		"	{"
		"		discard;"
		"	}"

		/// \todo Deal with all colourspace nonsense outside of the shader. Ideally the shader would accept only linear"
		/// textures and output only linear data."

		"	if( textureType==1 )"
		"	{"
		"		OUTCOLOR = texture2D( texture, gl_TexCoord[0].xy );"
		"		OUTCOLOR = vec4( ieLinToSRGB( OUTCOLOR.r ), ieLinToSRGB( OUTCOLOR.g ), ieLinToSRGB( OUTCOLOR.b ), ieLinToSRGB( OUTCOLOR.a ) );"
		"	}"
		"	else if( textureType==2 )"
		"	{"
		"		OUTCOLOR = vec4( OUTCOLOR.rgb, texture2D( texture, gl_TexCoord[0].xy ).a );"
		"	}\n"

		"#if __VERSION__ >= 330\n"
		"	ieCoreGLNameOut = ieCoreGLNameIn;\n"
		"#endif\n"
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

int StandardStyle::g_borderParameter;
int StandardStyle::g_borderRadiusParameter;
int StandardStyle::g_borderWidthParameter;
int StandardStyle::g_edgeAntiAliasingParameter;
int StandardStyle::g_textureParameter;
int StandardStyle::g_textureTypeParameter;
int StandardStyle::g_isCurveParameter;
int StandardStyle::g_endPointSizeParameter;
int StandardStyle::g_v0Parameter;
int StandardStyle::g_v1Parameter;
int StandardStyle::g_t0Parameter;
int StandardStyle::g_t1Parameter;
int StandardStyle::g_lineWidthParameter;

IECoreGL::Shader *StandardStyle::shader()
{

	static ShaderPtr g_shader = nullptr;

	if( !g_shader )
	{
		g_shader = ShaderLoader::defaultShaderLoader()->create( vertexSource(), "", fragmentSource() );
		g_borderParameter = g_shader->uniformParameter( "border" )->location;
		g_borderRadiusParameter = g_shader->uniformParameter( "borderRadius" )->location;
		g_borderWidthParameter = g_shader->uniformParameter( "borderWidth" )->location;
		g_edgeAntiAliasingParameter = g_shader->uniformParameter( "edgeAntiAliasing" )->location;
		g_textureParameter = g_shader->uniformParameter( "texture" )->location;
		g_textureTypeParameter = g_shader->uniformParameter( "textureType" )->location;
		g_isCurveParameter = g_shader->uniformParameter( "isCurve" )->location;
		g_endPointSizeParameter = g_shader->uniformParameter( "endPointSize" )->location;
		g_v0Parameter = g_shader->uniformParameter( "v0" )->location;
		g_v1Parameter = g_shader->uniformParameter( "v1" )->location;
		g_t0Parameter = g_shader->uniformParameter( "t0" )->location;
		g_t1Parameter = g_shader->uniformParameter( "t1" )->location;
		g_lineWidthParameter = g_shader->uniformParameter( "lineWidth" )->location;
	}

	return g_shader.get();
}
