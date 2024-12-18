//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferSceneUI/Private/VisualiserTool.h"

#include "GafferSceneUI/SceneView.h"
#include "GafferSceneUI/ScriptNodeAlgo.h"

#include "GafferUI/Gadget.h"
#include "GafferUI/Pointer.h"
#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

#include "IECoreScene/MeshAlgo.h"
#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/MeshPrimitiveEvaluator.h"
#include "IECoreScene/PrimitiveVariable.h"

#include "IECoreGL/Buffer.h"
#include "IECoreGL/CachedConverter.h"
#include "IECoreGL/Export.h"
#include "IECoreGL/GL.h"
#include "IECoreGL/MeshPrimitive.h"
#include "IECoreGL/Primitive.h"
#include "IECoreGL/Renderable.h"
#include "IECoreGL/Selector.h"
#include "IECoreGL/Shader.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/TypedStateComponent.h"
#include "IECoreGL/TypeIds.h"

#include "IECore/Export.h"
#include "IECore/LRUCache.h"
#include "IECore/RunTimeTyped.h"
#include "IECore/VectorTypedData.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "Imath/ImathBox.h"
#include "Imath/ImathColor.h"
IECORE_POP_DEFAULT_VISIBILITY

#include "boost/bind/bind.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/preprocessor/stringize.hpp"

#include <algorithm>
#include <cassert>
#include <limits>
#include <sstream>
#include <string>

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace GafferScene;
using namespace GafferSceneUI;
using namespace GafferUI;
using namespace Gaffer;

namespace
{

// Text and size constants
const float g_textSizeDefault = 9.0f;
const float g_textSizeMin = 6.0f;
const float g_textSizeInc = 0.5f;

// Opacity and value constants
const float g_opacityDefault = 1.0f;
const float g_opacityMin = 0.0f;
const float g_opacityMax = 1.0f;

const V3f g_valueMinDefault( 0.f );
const V3f g_valueMaxDefault( 1.f );

// Name of P primitive variable
const std::string g_pName = "P";

const Color4f g_textShadowColor( 0.2f, 0.2f, 0.2f, 1.f );
const float g_textShadowOffset = 0.1f;

// Uniform block structure (std140 layout)
struct UniformBlockColorShader
{
	alignas( 16 ) M44f o2c;
	alignas( 16 ) V3f valueMin;
	alignas( 16 ) V3f valueRange;
	alignas( 4 ) float opacity;
};

const GLuint g_uniformBlockBindingIndex = 0;

#define UNIFORM_BLOCK_COLOR_SHADER_GLSL_SOURCE \
	"layout( std140, row_major ) uniform UniformBlock\n" \
	"{\n" \
	"   mat4 o2c;\n" \
	"   vec3 valueMin;\n" \
	"   vec3 valueRange;\n" \
	"   float opacity;\n" \
	"} uniforms;\n"

#define ATTRIB_GLSL_LOCATION_PS 0
#define ATTRIB_GLSL_LOCATION_VSX 1
#define ATTRIB_GLSL_LOCATION_VSY 2
#define ATTRIB_GLSL_LOCATION_VSZ 3

#define ATTRIB_COLOR_SHADER_GLSL_SOURCE \
	"layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_PS ) " ) in vec3 ps;\n" \
	"layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_VSX ) " ) in float vsx;\n" \
	"layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_VSY ) " ) in float vsy;\n" \
	"layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_VSZ ) " ) in float vsz;\n" \

#define INTERFACE_BLOCK_COLOR_SHADER_GLSL_SOURCE( STORAGE, NAME ) \
	BOOST_PP_STRINGIZE( STORAGE ) " InterfaceBlock\n" \
	"{\n" \
	"   smooth vec3 value;\n" \
	"} " BOOST_PP_STRINGIZE( NAME ) ";\n"

// Opengl vertex shader code

const std::string g_colorShaderVertSource(
	"#version 330\n"

	UNIFORM_BLOCK_COLOR_SHADER_GLSL_SOURCE

	ATTRIB_COLOR_SHADER_GLSL_SOURCE

	INTERFACE_BLOCK_COLOR_SHADER_GLSL_SOURCE( out, outputs )

	"void main()\n"
	"{\n"
	"   outputs.value = clamp( ( vec3( vsx, vsy, vsz ) - uniforms.valueMin )\n"
	"       * uniforms.valueRange, 0.0, 1.0 );\n"
	"   gl_Position = vec4( ps, 1.0 ) * uniforms.o2c;\n"
	"}\n"
);

// Opengl fragment shader code

const std::string g_colorShaderFragSource
(
	"#version 330\n"

	UNIFORM_BLOCK_COLOR_SHADER_GLSL_SOURCE

	INTERFACE_BLOCK_COLOR_SHADER_GLSL_SOURCE( in, inputs )

	"layout( location = 0 ) out vec4 cs;\n"

	"void main()\n"
	"{\n"
	"   cs = vec4( inputs.value, uniforms.opacity );\n"
	"}\n"
);

// The gadget that does the actual opengl drawing of the shaded primitive
class VisualiserGadget : public Gadget
{

	public :

		explicit VisualiserGadget( const VisualiserTool &tool, const std::string &name = defaultName<VisualiserGadget>() )
			:	Gadget( name ), m_tool( &tool ), m_shader(), m_uniformBuffer()
		{
		}

		void resetTool()
		{
			m_tool = nullptr;
		}

	protected:

		void renderLayer( Gadget::Layer layer, const Style *style, Gadget::RenderReason reason ) const override
		{
			if(
				( layer != Gadget::Layer::MidFront && layer != Gadget::Layer::Front ) ||
				Gadget::isSelectionRender( reason )
			)
			{
				return;
			}

			// Check tool reference valid
			if( m_tool == nullptr )
			{
				return;
			}

			// Get parent viewport gadget
			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();

			if( layer == Gadget::Layer::MidFront )
			{
				renderColorVisualiser( viewportGadget );
			}

			else if( layer == Gadget::Layer::Front )
			{
				renderColorValue( viewportGadget, style );
			}
		}

		Box3f renderBound() const override
		{
			// NOTE : for now just return an infinite box

			Box3f b;
			b.makeInfinite();
			return b;
		}

		unsigned layerMask() const override
		{
			return m_tool ? static_cast< unsigned >( Gadget::Layer::MidFront | Gadget::Layer::Front ) : static_cast< unsigned >( 0 );
		}

	private:

		void buildShader() const
		{
			if( !m_shader )
			{
				m_shader = IECoreGL::ShaderLoader::defaultShaderLoader()->create(
					g_colorShaderVertSource, std::string(), g_colorShaderFragSource
				);
				if( m_shader )
				{
					const GLuint program = m_shader->program();
					const GLuint blockIndex = glGetUniformBlockIndex( program, "UniformBlock" );
					if( blockIndex != GL_INVALID_INDEX )
					{
						glUniformBlockBinding( program, blockIndex, g_uniformBlockBindingIndex );
					}
				}
			}
		}

		void renderColorVisualiser( const ViewportGadget *viewportGadget ) const
		{
			// Bootleg shader
			buildShader();

			if( !m_shader )
			{
				return;
			}

			// Get the cached converter from IECoreGL, this is used to convert primitive
			// variable data to opengl buffers which will be shared with the IECoreGL renderer
			IECoreGL::CachedConverter *converter = IECoreGL::CachedConverter::defaultCachedConverter();

			// Bootleg uniform buffer
			GLint uniformBinding;
			glGetIntegerv( GL_UNIFORM_BUFFER_BINDING, &uniformBinding );

			if( !m_uniformBuffer )
			{
				GLuint buffer = 0u;
				glGenBuffers( 1, &buffer );
				glBindBuffer( GL_UNIFORM_BUFFER, buffer );
				glBufferData( GL_UNIFORM_BUFFER, sizeof( UniformBlockColorShader ), 0, GL_DYNAMIC_DRAW );
				m_uniformBuffer.reset( new IECoreGL::Buffer( buffer ) );
			}

			glBindBufferBase( GL_UNIFORM_BUFFER, g_uniformBlockBindingIndex, m_uniformBuffer->buffer() );

			// Get the name of the primitive variable to visualise
			const std::string &name = m_tool->dataNamePlug()->getValue();

			// Get min/max values and colors and opacity
			UniformBlockColorShader uniforms;
			const VisualiserTool::Mode mode = (VisualiserTool::Mode)m_tool->modePlug()->getValue();
			const V3f valueMin = m_tool->valueMinPlug()->getValue();
			const V3f valueMax = m_tool->valueMaxPlug()->getValue();
			uniforms.opacity = m_tool->opacityPlug()->getValue();

			// Compute value range reciprocal
			//
			// NOTE : when range is <= 0 set the reciprocal to 0 so that value becomes 0 (minimum)
			std::optional<V3f> valueRange;
			if( mode == VisualiserTool::Mode::Color )
			{
				valueRange = ( valueMax - valueMin );
				for( int i = 0; i < 3; ++i )
				{
					valueRange.value()[i] = ( valueRange.value()[i] > 0.f ) ? ( 1.f / valueRange.value()[i] ) : 0.f;
				}
			}

			// Get the world to clip space matrix
			M44f v2c;
			glGetFloatv( GL_PROJECTION_MATRIX, v2c.getValue() );
			const M44f w2c = viewportGadget->getCameraTransform().gjInverse() * v2c;

			// Set opengl polygon and blend state
			//
			// NOTE : use polygon offset to ensure that any discrepancies between the transform
			//        from object to clip space do not cause z-fighting. This is necessary as
			//        the shader uses an object to clip matrix which may give slighly different
			//        depth results to the transformation used in the IECoreGL renderer.
			GLint blendEqRgb;
			GLint blendEqAlpha;
			glGetIntegerv( GL_BLEND_EQUATION_RGB, &blendEqRgb );
			glGetIntegerv( GL_BLEND_EQUATION_ALPHA, &blendEqAlpha );
			glBlendEquation( GL_FUNC_ADD );

			GLint blendSrcRgb;
			GLint blendSrcAlpha;
			GLint blendDstRgb;
			GLint blendDstAlpha;
			glGetIntegerv( GL_BLEND_SRC_RGB, &blendSrcRgb );
			glGetIntegerv( GL_BLEND_SRC_ALPHA, &blendSrcAlpha );
			glGetIntegerv( GL_BLEND_DST_RGB, &blendDstRgb );
			glGetIntegerv( GL_BLEND_DST_ALPHA, &blendDstAlpha );
			glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );

			const GLboolean depthEnabled = glIsEnabled( GL_DEPTH_TEST );
			if( !depthEnabled )
			{
				glEnable( GL_DEPTH_TEST );
			}

			GLint depthFunc;
			glGetIntegerv( GL_DEPTH_FUNC, &depthFunc );
			glDepthFunc( GL_LEQUAL );

			GLboolean depthWriteEnabled;
			glGetBooleanv( GL_DEPTH_WRITEMASK, &depthWriteEnabled );
			if( depthWriteEnabled )
			{
				glDepthMask( GL_FALSE );
			}

			const GLboolean blendEnabled = glIsEnabled( GL_BLEND );
			if( !blendEnabled )
			{
				glEnable( GL_BLEND );
			}

			// MSVC appears to be doing an optimization that causes the call to
			// `glPolygonMode( GL_FRONT_AND_BACK, polygonMode )` to fail with an
			// "invalid enum" error. Initializing the value even when we are going
			// to immediately set it via `glGetIntegerv()` prevents that optimization
			// and allows us to successfully reset the value.
			GLint polygonMode = GL_FILL;
			glGetIntegerv( GL_POLYGON_MODE, &polygonMode );
			glPolygonMode( GL_FRONT_AND_BACK, GL_FILL );

			const GLboolean cullFaceEnabled = glIsEnabled( GL_CULL_FACE );
			if( cullFaceEnabled )
			{
				glDisable( GL_CULL_FACE );
			}

			const GLboolean polgonOffsetFillEnabled = glIsEnabled( GL_POLYGON_OFFSET_FILL );
			if( !polgonOffsetFillEnabled )
			{
				glEnable( GL_POLYGON_OFFSET_FILL );
			}

			GLfloat polygonOffsetFactor, polygonOffsetUnits;
			glGetFloatv( GL_POLYGON_OFFSET_FACTOR, &polygonOffsetFactor );
			glGetFloatv( GL_POLYGON_OFFSET_UNITS, &polygonOffsetUnits );
			glPolygonOffset( -1, -1 );

			// Enable shader program

			GLint shaderProgram;
			glGetIntegerv( GL_CURRENT_PROGRAM, &shaderProgram );
			glUseProgram( m_shader->program() );

			// Set opengl vertex attribute array state

			GLint arrayBinding;
			glGetIntegerv( GL_ARRAY_BUFFER_BINDING, &arrayBinding );

			glPushClientAttrib( GL_CLIENT_VERTEX_ARRAY_BIT );

			glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_PS, 0 );
			glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_PS );
			glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_VSX, 0 );
			glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_VSX );
			glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_VSY, 0 );
			glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_VSY );
			glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_VSZ, 0 );

			// Loop through current selection

			for( const auto &location : m_tool->selection() )
			{
				ScenePlug::PathScope scope( &location.context(), &location.path() );

				// Check path exists
				if( !location.scene().existsPlug()->getValue() )
				{
					continue;
				}

				// Extract mesh primitive
				auto mesh = runTimeCast<const MeshPrimitive>( location.scene().objectPlug()->getValue() );
				if( !mesh )
				{
					continue;
				}

				// Retrieve cached IECoreGL mesh primitive
				auto meshGL = runTimeCast<const IECoreGL::MeshPrimitive>( converter->convert( mesh.get() ) );
				if( !meshGL )
				{
					continue;
				}

				// Find opengl "P" buffer data

				IECoreGL::ConstBufferPtr pBuffer = meshGL->getVertexBuffer( g_pName );
				if( !pBuffer )
				{
					continue;
				}

				// Find opengl named buffer data
				//
				// NOTE : conversion to IECoreGL mesh may generate vertex attributes (eg. "N")
				//        so check named primitive variable exists on IECore mesh primitive.

				const auto vIt = mesh->variables.find( name );
				if( vIt == mesh->variables.end() )
				{
					continue;
				}

				ConstDataPtr vData = vIt->second.data;
				GLsizei stride = 0;
				GLenum type = GL_FLOAT;
				bool offset = false;
				bool enableVSZ = false;
				switch( vData->typeId() )
				{
					case IntVectorDataTypeId:
						type = GL_INT;
						[[fallthrough]];
					case FloatVectorDataTypeId:
						enableVSZ = true;
						uniforms.valueMin = valueRange ? V3f( valueMin.x ) : V3f( 0.f );
						uniforms.valueRange = valueRange ? V3f( valueRange.value().x ) : V3f( 1.f );
						break;
					case V2fVectorDataTypeId:
						stride = 2;
						offset = true;
						uniforms.valueMin = valueRange ? V3f( valueMin.x, valueMin.y, 0.f ) : V3f( 0.f );
						uniforms.valueRange = valueRange ? V3f( valueRange.value().x, valueRange.value().y, 0.f ) : V3f( 1.f, 1.f, 0.f );
						break;
					case Color3fVectorDataTypeId:
						stride = 3;
						offset = true;
						enableVSZ = true;
						uniforms.valueMin = valueRange ? valueMin : V3f( 0.f );
						uniforms.valueRange = valueRange ? valueRange.value() : V3f( 1.f );
						break;
					case V3fVectorDataTypeId:
						stride = 3;
						offset = true;
						enableVSZ = true;
						uniforms.valueMin = valueRange ? valueMin : V3f( -1.f );
						// Use 0.5 instead of 2.0 to account for reciprocal in `valueRange` above
						uniforms.valueRange = valueRange ? valueRange.value() : V3f( 0.5f );
						break;
					default:
						continue;
				}

				IECoreGL::ConstBufferPtr vBuffer = meshGL->getVertexBuffer( name );
				if( !vBuffer )
				{
					continue;
				}

				// Get the object to world transform

				M44f o2w;
				ScenePlug::ScenePath path( location.path() );
				while( !path.empty() )
				{
					scope.setPath( &path );
					o2w = o2w * location.scene().transformPlug()->getValue();
					path.pop_back();
				}

				// Compute object to clip matrix
				uniforms.o2c = o2w * w2c;

				// Upload opengl uniform block data

				glBufferData( GL_UNIFORM_BUFFER, sizeof( UniformBlockColorShader ), &uniforms, GL_DYNAMIC_DRAW );

				// Draw primitive
				glBindBuffer( GL_ARRAY_BUFFER, pBuffer->buffer() );
				glVertexAttribPointer( ATTRIB_GLSL_LOCATION_PS, 3, GL_FLOAT, GL_FALSE, 0, nullptr );
				glBindBuffer( GL_ARRAY_BUFFER, vBuffer->buffer() );
				glVertexAttribPointer( ATTRIB_GLSL_LOCATION_VSX, 1, type, GL_FALSE, stride * sizeof( GLfloat ), nullptr );
				glVertexAttribPointer(
					ATTRIB_GLSL_LOCATION_VSY,
					1,
					type,
					GL_FALSE,
					stride * sizeof( GLfloat ),
					( void const *)( ( offset ? 1 : 0 ) * sizeof( GLfloat ) )
				);
				if( enableVSZ )
				{
					glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_VSZ );
					glVertexAttribPointer(
						ATTRIB_GLSL_LOCATION_VSZ,
						1,
						type,
						GL_FALSE,
						stride * sizeof( GLfloat ),
						( void const *)( ( offset ? 2 : 0 ) * sizeof( GLfloat ) )
					);
				}
				else
				{
					glDisableVertexAttribArray( ATTRIB_GLSL_LOCATION_VSZ );
					glVertexAttrib1f( ATTRIB_GLSL_LOCATION_VSZ, 0.f );
				}

				meshGL->renderInstances( 1 );
			}

			// Restore opengl state

			glPopClientAttrib();
			glBindBuffer( GL_ARRAY_BUFFER, arrayBinding );
			glBindBuffer( GL_UNIFORM_BUFFER, uniformBinding );

			glDepthFunc( depthFunc );
			glBlendEquationSeparate( blendEqRgb, blendEqAlpha );
			glBlendFuncSeparate( blendSrcRgb, blendDstRgb, blendSrcAlpha, blendDstAlpha );
			glPolygonMode( GL_FRONT_AND_BACK, polygonMode );
			if( cullFaceEnabled )
			{
				glEnable( GL_CULL_FACE );
			}
			if( !polgonOffsetFillEnabled )
			{
				glDisable( GL_POLYGON_OFFSET_FILL );
			}
			glPolygonOffset( polygonOffsetFactor, polygonOffsetUnits );

			if( !blendEnabled )
			{
				glDisable( GL_BLEND );
			}
			if( !depthEnabled )
			{
				glDisable( GL_DEPTH_TEST );
			}
			if( depthWriteEnabled )
			{
				glDepthMask( GL_TRUE );
			}
			glUseProgram( shaderProgram );
		}

		void renderColorValue( const ViewportGadget *viewportGadget, const Style *style ) const
		{
			// Display value at cursor as text

			const Data *value = m_tool->cursorValue();
			if( value )
			{
				std::ostringstream oss;
				switch( value->typeId() )
				{
					case IntDataTypeId:
						oss << ( assertedStaticCast<const IntData>( value )->readable() );
						break;
					case FloatDataTypeId:
						oss << ( assertedStaticCast<const FloatData>( value )->readable() );
						break;
					case V2fDataTypeId:
						oss << ( assertedStaticCast<const V2fData>( value )->readable() );
						break;
					case V3fDataTypeId:
						oss << ( assertedStaticCast<const V3fData>( value )->readable() );
						break;
					case Color3fDataTypeId:
						oss << ( assertedStaticCast<const Color3fData>( value )->readable() );
						break;
					default:
						break;
				}

				const std::string text = oss.str();
				if( !text.empty() )
				{
					// Draw in raster space
					//
					// NOTE : It seems that Gaffer defines the origin of raster space as the top left corner
					//        of the viewport, however the style text drawing functions assume that y increases
					//        "up" the screen rather than "down", so invert y to ensure text is not upside down.

					ViewportGadget::RasterScope raster( viewportGadget );
					const float size = m_tool->sizePlug()->getValue();
					const V3f scale( size, -size, 1.f );
					const V2f &rp = m_tool->cursorPos();

					glPushMatrix();
					glTranslatef( rp.x, rp.y, 0.f );
					glScalef( scale.x, scale.y, scale.z );

					/// Shadow text
					glTranslatef( g_textShadowOffset, 0.f, 0.f );
					style->renderText( Style::LabelText, text, GafferUI::Style::State::NormalState, &g_textShadowColor );

					glTranslatef( -g_textShadowOffset * 2.f, 0.f, 0.f );
					style->renderText( Style::LabelText, text, GafferUI::Style::State::NormalState, &g_textShadowColor );

					glTranslatef( g_textShadowOffset, g_textShadowOffset, 0.f );
					style->renderText( Style::LabelText, text, GafferUI::Style::State::NormalState, &g_textShadowColor );

					glTranslatef( 0.f, -g_textShadowOffset * 2.f, 0.f );
					style->renderText( Style::LabelText, text, GafferUI::Style::State::NormalState, &g_textShadowColor );

					/// Primary text
					glTranslatef( 0.f, g_textShadowOffset, 0.f );
					style->renderText( Style::LabelText, text );

					glPopMatrix();
				}
			}
		}

		const VisualiserTool *m_tool;
		mutable IECoreGL::ConstShaderPtr m_shader;
		mutable IECoreGL::ConstBufferPtr m_uniformBuffer;
};

// Cache for mesh evaluators
struct EvaluationData
{
	ConstMeshPrimitivePtr triMesh;
	ConstMeshPrimitiveEvaluatorPtr evaluator;
};

LRUCache<ConstMeshPrimitivePtr, EvaluationData> g_evaluatorCache(
	[] ( ConstMeshPrimitivePtr mesh, size_t &cost ) -> EvaluationData
	{
		cost = 1;
		EvaluationData data;
		data.triMesh = mesh->copy();
		data.triMesh = MeshAlgo::triangulate( data.triMesh.get() );
		data.evaluator = new MeshPrimitiveEvaluator( data.triMesh );
		return data;
	},
	10
);

} // namespace

GAFFER_NODE_DEFINE_TYPE( VisualiserTool )

Tool::ToolDescription<VisualiserTool, SceneView> VisualiserTool::m_toolDescription;

size_t VisualiserTool::g_firstPlugIndex = 0;

VisualiserTool::VisualiserTool( SceneView *view, const std::string &name ) : SelectionTool( view, name ),
	m_preRenderConnection(),
	m_buttonPressConnection(),
	m_dragBeginConnection(),
	m_gadget( new VisualiserGadget( *this ) ),
	m_selection(),
	m_cursorPos( -1, -1 ),
	m_cursorPosValid( false ),
	m_cursorValue(),
	m_gadgetDirty( true ),
	m_selectionDirty( true ),
	m_priorityPathsDirty( true ),
	m_valueAtButtonPress(),
	m_initiatedDrag( false )
{
	view->viewportGadget()->addChild( m_gadget );
	// We want to draw the visualiser gadget before other gadgets
	// like transform handles.
	makeGadgetFirst();
	m_gadget->setVisible( false );

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "dataName", Plug::In, "uv" ) );
	addChild( new FloatPlug( "opacity", Plug::In, g_opacityDefault, g_opacityMin, g_opacityMax ) );
	addChild( new IntPlug( "mode", Plug::In, (int)Mode::Auto, (int)Mode::First, (int)Mode::Last ) );
	addChild( new V3fPlug( "valueMin", Plug::In, g_valueMinDefault ) );
	addChild( new V3fPlug( "valueMax", Plug::In, g_valueMaxDefault ) );
	addChild( new FloatPlug( "size", Plug::In, g_textSizeDefault, g_textSizeMin ) );
	addChild( new ScenePlug( "__scene", Plug::In ) );

	internalScenePlug()->setInput( view->inPlug<ScenePlug>() );

	// Connect signal handlers
	//
	// NOTE : connecting to the viewport gadget means we will get called for all events
	//        which makes sense for key events, however we do not want to display value
	//        text when the mouse is over another gadget, (eg. Transform Tool handle)
	//        so instead connect to scene gadget signal.
	// NOTE : There are other handlers that will attempt to consume button and drag
	//        events so connect handlers at the front of button/drag signal handler queues.

	view->viewportGadget()->keyPressSignal().connect(
		boost::bind( &VisualiserTool::keyPress, this, boost::placeholders::_2 )
	);

	// NOTE : drag end and button release handlers remain whilst tool inactive in case tool
	//        is made inactive after button pressed or drag initiated in which case these
	//        handlers still need to tidy up state.

	sceneGadget()->buttonReleaseSignal().connectFront(
		boost::bind( &VisualiserTool::buttonRelease, this, boost::placeholders::_2 )
	);

	sceneGadget()->dragEndSignal().connectFront(
		boost::bind( &VisualiserTool::dragEnd, this, boost::placeholders::_2 )
	);

	// NOTE : mouse tracking handlers remain connected whilst tool inactive as they track the cursor
	//        line and whether its valid or not. This prevents the value display from "sticking" to
	//        edge of viewport when cursor leaves viewport's screen space. It also means that we do
	//        not have to work out the cursor line and whether its valid when tool is made active.

	sceneGadget()->enterSignal().connect(
		boost::bind( &VisualiserTool::enter, this, boost::placeholders::_2 )
	);
	sceneGadget()->leaveSignal().connect(
		boost::bind( &VisualiserTool::leave, this, boost::placeholders::_2 )
	);
	sceneGadget()->mouseMoveSignal().connect(
		boost::bind( &VisualiserTool::mouseMove, this, boost::placeholders::_2 )
	);

	plugDirtiedSignal().connect(
		boost::bind( &VisualiserTool::plugDirtied, this, boost::placeholders::_1 )
	);
	plugSetSignal().connect(
		boost::bind( &VisualiserTool::plugSet, this, boost::placeholders::_1 )
	);

	view->contextChangedSignal().connect( boost::bind( &VisualiserTool::contextChanged, this ) );
	ScriptNodeAlgo::selectedPathsChangedSignal( view->scriptNode() ).connect(
		boost::bind( &VisualiserTool::selectedPathsChanged, this )
	);

}

VisualiserTool::~VisualiserTool()
{
	// NOTE : ensure that the gadget's reference to the tool is reset

	static_cast<VisualiserGadget *>( m_gadget.get() )->resetTool();
}

StringPlug *VisualiserTool::dataNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const StringPlug *VisualiserTool::dataNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

FloatPlug *VisualiserTool::opacityPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const FloatPlug *VisualiserTool::opacityPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

IntPlug *VisualiserTool::modePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const IntPlug *VisualiserTool::modePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

V3fPlug *VisualiserTool::valueMinPlug()
{
	return getChild<V3fPlug>( g_firstPlugIndex + 3 );
}

const V3fPlug *VisualiserTool::valueMinPlug() const
{
	return getChild<V3fPlug>( g_firstPlugIndex + 3 );
}

V3fPlug *VisualiserTool::valueMaxPlug()
{
	return getChild<V3fPlug>( g_firstPlugIndex + 4 );
}

const V3fPlug *VisualiserTool::valueMaxPlug() const
{
	return getChild<V3fPlug>( g_firstPlugIndex + 4 );
}

FloatPlug *VisualiserTool::sizePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 5 );
}

const FloatPlug *VisualiserTool::sizePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 5 );
}

ScenePlug *VisualiserTool::internalScenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 6 );
}

const ScenePlug *VisualiserTool::internalScenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 6 );
}

const std::vector<VisualiserTool::Selection> &VisualiserTool::selection() const
{
	return m_selection;
}

V2f VisualiserTool::cursorPos() const
{
	return m_cursorPos;
}

const Data *VisualiserTool::cursorValue() const
{
	return m_cursorValue.get();
}

void VisualiserTool::connectOnActive()
{
	// NOTE : There are other handlers that will attempt to consume button and drag events
	//        so connect handlers at the front of button/drag signal handler queues.

	m_buttonPressConnection = sceneGadget()->buttonPressSignal().connectFront(
		boost::bind( &VisualiserTool::buttonPress, this, boost::placeholders::_2 )
	);
	m_dragBeginConnection = sceneGadget()->dragBeginSignal().connectFront(
		boost::bind( &VisualiserTool::dragBegin, this, boost::placeholders::_2 )
	);

	m_preRenderConnection = view()->viewportGadget()->preRenderSignal().connect(
		boost::bind( &VisualiserTool::preRender, this )
	);

	// NOTE : redraw necessary to ensure value display updated.

	view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
}

void VisualiserTool::disconnectOnInactive()
{
	m_preRenderConnection.disconnect();
	m_buttonPressConnection.disconnect();
	m_dragBeginConnection.disconnect();
}

void VisualiserTool::contextChanged()
{
	// Context changes can change the scene, which in turn
	// dirties our selection.
	selectedPathsChanged();
}

void VisualiserTool::selectedPathsChanged()
{
	m_selectionDirty = true;
	m_gadgetDirty = true;
	m_priorityPathsDirty = true;
}

bool VisualiserTool::mouseMove( const ButtonEvent &event )
{
	if( m_initiatedDrag )
	{
		return false;
	}

	updateCursorPos( event );
	m_cursorPosValid = true;

	// NOTE : only schedule redraw if tool active

	if( activePlug()->getValue() )
	{
		view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	}

	return false;
}

void VisualiserTool::enter( const ButtonEvent &event )
{
	updateCursorPos( event );
	m_cursorPosValid = true;

	// NOTE : only schedule redraw if tool active

	if( activePlug()->getValue() )
	{
		view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	}
}

void VisualiserTool::leave( const ButtonEvent &event )
{
	updateCursorPos( event );
	m_cursorPosValid = false;

	// NOTE : only schedule redraw if tool active

	if( activePlug()->getValue() )
	{
		view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	}
}

bool VisualiserTool::keyPress( const KeyEvent &event )
{
	if( !activePlug()->getValue() )
	{
		return false;
	}

	// allow user to scale text with +/- keys

	if( event.key == "Plus" || event.key == "Equal" )
	{
		sizePlug()->setValue( sizePlug()->getValue() + g_textSizeInc );
	}
	else if( event.key == "Minus" || event.key == "Underscore" )
	{
		sizePlug()->setValue( std::max( sizePlug()->getValue() - g_textSizeInc, g_textSizeMin ) );
	}

	return false;
}

bool VisualiserTool::buttonPress( const ButtonEvent &event )
{
	m_valueAtButtonPress.reset();
	m_initiatedDrag = false;

	if( event.button & ButtonEvent::Left && !( event.modifiers & GafferUI::ButtonEvent::Modifiers::Control ) )
	{
		updateCursorValue();
		if( m_cursorValue )
		{
			m_valueAtButtonPress = m_cursorValue->copy();
			return true;
		}
	}

	return false;
}

bool VisualiserTool::buttonRelease( const ButtonEvent &event )
{
	m_valueAtButtonPress.reset();
	m_initiatedDrag = false;

	return false;
}

RunTimeTypedPtr VisualiserTool::dragBegin( const DragDropEvent &event )
{
	m_initiatedDrag = false;

	if( !m_valueAtButtonPress )
	{
		return RunTimeTypedPtr();
	}

	// NOTE : There is a possibility that the tool has become inactive since the button
	//        press event that triggered the drag was accepted, the cutoff point is the
	//        button press event, so any change to the active state after that does not
	//        affect an ongoing drag operation. We therefore always request a redraw
	//        here so that the displayed value is cleared.

	m_initiatedDrag = true;
	view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	Pointer::setCurrent( "values" );

	return m_valueAtButtonPress;
}

bool VisualiserTool::dragEnd( const DragDropEvent &event )
{
	if( !m_initiatedDrag )
	{
		return false;
	}

	m_initiatedDrag = false;
	Pointer::setCurrent( "" );
	return true;
}

void VisualiserTool::plugDirtied( const Plug *plug )
{
	if(
		plug == activePlug() ||
		plug == internalScenePlug()->objectPlug() ||
		plug == internalScenePlug()->transformPlug()
	)
	{
		m_selectionDirty = true;
		m_gadgetDirty = true;
		m_priorityPathsDirty = true;
	}
	else if(
		plug == dataNamePlug() ||
		plug == opacityPlug() ||
		plug == valueMinPlug() ||
		plug == valueMaxPlug() ||
		plug == sizePlug() ||
		plug == modePlug()
	)
	{
		m_gadgetDirty = true;
		view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	}

	if( plug == activePlug() )
	{
		if( activePlug()->getValue() )
		{
			connectOnActive();
		}
		else
		{
			disconnectOnInactive();
			m_gadget->setVisible( false );

			sceneGadget()->setPriorityPaths( PathMatcher() );
		}
	}
}

void VisualiserTool::plugSet( const Plug *plug )
{
	// Ensure that the min value does not exceed the max and vice-versa

	if( plug == valueMinPlug() )
	{
		const V3f valueMin = valueMinPlug()->getValue();
		V3f valueMax = valueMaxPlug()->getValue();

		for( int i = 0; i < 3; ++i )
		{
			valueMax[i] = std::max( valueMin[i], valueMax[i] );
		}

		valueMaxPlug()->setValue( valueMax );
	}
	else if( plug == valueMaxPlug() )
	{
		V3f valueMin = valueMinPlug()->getValue();
		const V3f valueMax = valueMaxPlug()->getValue();

		for( int i = 0; i < 3; ++i )
		{
			valueMin[i] = std::min( valueMin[i], valueMax[i] );
		}

		valueMinPlug()->setValue( valueMin );
	}
}

void VisualiserTool::updateSelection() const
{
	if( !m_selectionDirty )
	{
		return;
	}

	m_selection.clear();
	m_selectionDirty = false;

	if( !activePlug()->getValue() )
	{
		return;
	}

	auto scene = internalScenePlug()->getInput<const ScenePlug>();

	if( !scene )
	{
		scene = scene->getInput<ScenePlug>();
		if( !scene )
		{
			return;
		}
	}

	const PathMatcher selectedPaths = ScriptNodeAlgo::getSelectedPaths( view()->scriptNode() );


	if( selectedPaths.isEmpty() )
	{
		return;
	}

	for( PathMatcher::Iterator it = selectedPaths.begin(), eIt = selectedPaths.end(); it != eIt; ++it )
	{
		m_selection.emplace_back( *scene, *it, *view()->context() );
	}
}

void VisualiserTool::preRender()
{
	updateSelection();

	if( m_priorityPathsDirty )
	{
		sceneGadget()->setPriorityPaths(
			m_selection.empty() ? PathMatcher() : ScriptNodeAlgo::getSelectedPaths( view()->scriptNode() )
		);

		m_priorityPathsDirty = false;
	}

	if( m_selection.empty() )
	{
		m_gadget->setVisible( false );
		return;
	}

	m_gadget->setVisible( true );

	if( m_gadgetDirty )
	{
		m_gadgetDirty = false;
	}

	/// \todo This causes a noticeable performance decline due to it's use of `objectAt()`, which
	/// redraws the scene into a selection buffer. We don't have a solution at the moment, but
	/// noting this as the cause for future investigation.
	updateCursorValue();
}

void VisualiserTool::updateCursorPos( const ButtonEvent &event )
{
	// Update cursor raster position
	//
	// NOTE : the cursor position is stored in raster space so it is free of camera
	//        transformations so we do not need to track camera changes.

	assert( view() );
	assert( view()->viewportGadget() );

	m_cursorPos = view()->viewportGadget()->gadgetToRasterSpace( event.line.p1, sceneGadget() );
}

void VisualiserTool::updateCursorValue()
{
	DataPtr cursorValue = m_cursorValue;
	m_cursorValue.reset();

	// NOTE : during a drag do not update the cursor value

	if( m_initiatedDrag || !m_cursorPosValid )
	{
		return;
	}

	// Get scene gadget and viewport gadgets

	SceneGadget *sg = sceneGadget();
	if( !sg || !view() || !view()->viewportGadget() )
	{
		return;
	}

	// Get the current object at cursor

	ScenePlug::ScenePath path;

	const StringVectorData *selectionMask = nullptr;
	try
	{
		// Clear any existing selection mask
		selectionMask = sg->getSelectionMask();
		sg->setSelectionMask( nullptr );

		if( !sg->objectAt( view()->viewportGadget()->rasterToGadgetSpace( m_cursorPos, sg ), path ) )
		{
			return;
		}

		// restore selection mask
		sg->setSelectionMask( selectionMask );
	}
	catch( const Exception & )
	{
		// NOTE : objectAt seems to write to the OpenGL color buffer so if there was an
		//        error the OpenGL color buffer will contain the remnants of the failed
		//        object id pass. If we are being called from preRender() the color buffer
		//        would normally be cleared after the preRender callback has finished so
		//        catch the exception and return. If we are being called from button press
		//        we don't want the exception to propagate so again catch and return. In
		//        both cases the error should happen again during the next render pass.

		// restore selection mask
		sg->setSelectionMask( selectionMask );

		return;
	}

	// Check current object is included in selection

	const std::vector<Selection>::const_iterator sIt = std::find_if(
		m_selection.begin(),
		m_selection.end(),
		[ &path ]( const Selection &item ) -> bool
		{
			return item.path() == path;
		}
	);
	if( sIt == m_selection.end() )
	{
		return;
	}

	// Check scene location exists

	const Selection &item = *sIt;
	ScenePlug::PathScope scope( &item.context(), &path );
	if( !item.scene().existsPlug()->getValue() )
	{
		return;
	}

	// Extract mesh primitive object

	auto mesh = runTimeCast<const MeshPrimitive>( item.scene().objectPlug()->getValue() );
	if( !mesh )
	{
		return;
	}

	// Check mesh has named primitive variable

	const std::string &name = dataNamePlug()->getValue();
	PrimitiveVariableMap::const_iterator vIt = mesh->variables.find( name );
	if( vIt == mesh->variables.end() || !vIt->second.data )
	{
		return;
	}

	// Check type of data

	switch( vIt->second.data->typeId() )
	{
		case IntVectorDataTypeId:
		case FloatVectorDataTypeId:
		case V2fVectorDataTypeId:
		case V3fVectorDataTypeId:
		case Color3fVectorDataTypeId:
			break;
		default:
			return;
	}

	// Create a mesh primitive evaluator
	//
	// NOTE : In order to create an evaluator we need a triangulated mesh
	//        this processing is expensive so we cache the created evaluator in an LRU cache

	const EvaluationData evalData = g_evaluatorCache.get( mesh );
	PrimitiveEvaluator::ResultPtr result = evalData.evaluator->createResult();

	// Intersect line from cursor with mesh in object space using evaluator

	const LineSegment3f line = view()->viewportGadget()->rasterToWorldSpace( cursorPos() ) *
			item.scene().fullTransform( path ).gjInverse();
	if( !evalData.evaluator->intersectionPoint( line.p0, line.direction(), result.get() ) )
	{
		return;
	}

	// Update value from intersection result

	switch( vIt->second.data->typeId() )
	{
		case IntVectorDataTypeId :
		{
			auto data = runTimeCast<IntData>( cursorValue );
			if( !data )
			{
				data.reset( new IntData() );
			}
			data->writable() = result->intPrimVar( evalData.triMesh->variables.at( name ) );
			cursorValue = data;
			break;
		}
		case FloatVectorDataTypeId :
		{
			auto data =runTimeCast<FloatData>( cursorValue );
			if( !data )
			{
				data.reset( new FloatData() );
			}
			data->writable() = result->floatPrimVar( evalData.triMesh->variables.at( name ) );
			cursorValue = data;
			break;
		}
		case V2fVectorDataTypeId :
		{
			auto data =runTimeCast<V2fData>( cursorValue );
			if( !data )
			{
				data.reset( new V2fData() );
			}
			data->writable() = result->vec2PrimVar( evalData.triMesh->variables.at( name ) );
			cursorValue = data;
			break;
		}
		case V3fVectorDataTypeId :
		{
			auto data = runTimeCast<V3fData>( cursorValue );
			if( !data )
			{
				data.reset( new V3fData() );
			}
			data->writable() = result->vectorPrimVar( evalData.triMesh->variables.at( name ) );
			cursorValue = data;
			break;
		}
		case Color3fVectorDataTypeId :
		{
			auto data = runTimeCast<Color3fData>( cursorValue );
			if( !data )
			{
				data.reset( new Color3fData() );
			}
			data->writable() = result->colorPrimVar( evalData.triMesh->variables.at( name ) );
			cursorValue = data;
			break;
		}
		default:
			return;
	}

	m_cursorValue = cursorValue;
}

SceneGadget *VisualiserTool::sceneGadget()
{
	return runTimeCast<SceneGadget>( view()->viewportGadget()->getPrimaryChild() );
}

const SceneGadget * VisualiserTool::sceneGadget() const
{
	return runTimeCast<const SceneGadget>( view()->viewportGadget()->getPrimaryChild() );
}

void VisualiserTool::makeGadgetFirst()
{
	const GraphComponent::ChildContainer oldChildren = view()->viewportGadget()->children();

	GraphComponent::ChildContainer newChildren( oldChildren );

	auto it = std::find_if(
		newChildren.begin(),
		newChildren.end(),
		[this]( const auto &c )
		{
			return c == m_gadget;
		}
	);
	if( it != newChildren.end() && it != newChildren.begin() )
	{
		// `std::swap` would likely be more efficient, but losing the
		// rest of the tool order causes selection highlighting to be
		// drawn over transform tools.
		std::rotate( newChildren.begin(), it, it + 1 );
		view()->viewportGadget()->reorderChildren( newChildren );
	}
}

VisualiserTool::Selection::Selection(
	const ScenePlug &scene,
	const ScenePlug::ScenePath &path,
	const Context &context
) : m_scene( &scene ), m_path( path ), m_context( &context )
{

}

const ScenePlug &VisualiserTool::Selection::scene() const
{
	return *m_scene;
}

const ScenePlug::ScenePath &VisualiserTool::Selection::path() const
{
	return m_path;
}

const Context &VisualiserTool::Selection::context() const
{
	return *m_context;
}
