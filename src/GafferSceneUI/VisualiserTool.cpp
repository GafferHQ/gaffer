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

#include "GafferScene/ResamplePrimitiveVariables.h"

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

#include "fmt/format.h"

#include <algorithm>
#include <cassert>
#include <limits>
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

// Vector constants
const float g_vectorScaleDefault = 1.f;
const float g_vectorScaleMin = 10.f * std::numeric_limits< float >::min();
float const g_vectorScaleInc = 0.01f;

const Color3f g_vectorColorDefault( 1.f, 1.f, 1.f );

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

const std::string g_primitiveVariablePrefix= "primitiveVariable:";
const int g_primitiveVariablePrefixSize = g_primitiveVariablePrefix.size();

// VertexLabel constants
const float g_cursorRadius2 = 25.f * 25.f;
const std::string g_vertexIndexDataName = "vertex:index";

//-----------------------------------------------------------------------------
// Color shader
//-----------------------------------------------------------------------------

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

//-----------------------------------------------------------------------------
// Vertex label shader
//-----------------------------------------------------------------------------

struct UniformBlockVertexLabelShader
{
	alignas( 16 ) Imath::M44f o2c;
};

// Block binding indexes for the uniform and shader storage buffers

GLuint const g_storageBlockBindingIndex = 0;

// Uniform block definition (std140 layout)

#define UNIFORM_BLOCK_VERTEX_LABEL_SHADER_GLSL_SOURCE \
	"layout( std140, row_major ) uniform UniformBlock\n" \
	"{\n" \
	"   mat4 o2c;\n" \
	"} uniforms;\n"

// Shader storage block definition (std430 layout)
//
// NOTE : std430 layout ensures that the elements of a uint array are tightly packed
//        std140 would require 16 byte alignment of each element ...

#define STORAGE_BLOCK_VERTEX_LABEL_SHADER_GLSL_SOURCE \
	"layout( std430 ) buffer StorageBlock\n" \
	"{\n" \
	"   coherent restrict uint visibility[];\n" \
	"} buffers;\n"

// Vertex attribute definitions

#define ATTRIB_VERTEX_LABEL_SHADER_GLSL_SOURCE \
	"layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_PS ) " ) in vec3 ps;\n"

// Interface block definition

#define INTERFACE_BLOCK_VERTEX_LABEL_SHADER_GLSL_SOURCE( STORAGE, NAME ) \
	BOOST_PP_STRINGIZE( STORAGE ) " InterfaceBlock\n" \
	"{\n" \
	"   flat uint vertexId;\n" \
	"} " BOOST_PP_STRINGIZE( NAME ) ";\n"

// Opengl vertex shader code

std::string const g_vertexLabelShaderVertSource
(
	"#version 430\n"

	UNIFORM_BLOCK_VERTEX_LABEL_SHADER_GLSL_SOURCE

	ATTRIB_VERTEX_LABEL_SHADER_GLSL_SOURCE

	INTERFACE_BLOCK_VERTEX_LABEL_SHADER_GLSL_SOURCE( out, outputs )

	"void main()\n"
	"{\n"
	"   gl_Position = vec4( ps, 1.0 ) * uniforms.o2c;\n"
	"   outputs.vertexId = uint( gl_VertexID );\n"
	"}\n"
);

// Opengl fragment shader code

std::string const g_vertexLabelShaderFragSource
(
	"#version 430\n"

	// NOTE : ensure that shader is only run for fragments that pass depth test.

	"layout( early_fragment_tests ) in;\n"

	STORAGE_BLOCK_VERTEX_LABEL_SHADER_GLSL_SOURCE

	UNIFORM_BLOCK_VERTEX_LABEL_SHADER_GLSL_SOURCE

	INTERFACE_BLOCK_VERTEX_LABEL_SHADER_GLSL_SOURCE( in, inputs )

	"void main()\n"
	"{\n"
	"   uint index = inputs.vertexId / 32u;\n"
	"   uint value = inputs.vertexId % 32u;\n"
	"   atomicOr( buffers.visibility[ index ], 1u << value );\n"
	"}\n"
);

//-----------------------------------------------------------------------------
// Vector shader
//-----------------------------------------------------------------------------

struct UniformBlockVectorShader
{
	alignas( 16 ) Imath::M44f o2v;
	alignas( 16 ) Imath::M44f n2v;
	alignas( 16 ) Imath::M44f v2c;
	alignas( 16 ) Imath::M44f o2c;
	alignas( 16 ) Imath::Color3f color;
	alignas( 4 ) float opacity;
	alignas( 4 ) float scale;
};

#define UNIFORM_BLOCK_VECTOR_GLSL_SOURCE \
	"layout( std140, row_major ) uniform UniformBlock\n" \
	"{\n" \
	"   mat4 o2v;\n" \
	"   mat4 n2v;\n" \
	"   mat4 v2c;\n" \
	"   mat4 o2c;\n" \
	"   vec3 color;\n" \
	"   float opacity;\n" \
	"   float scale;\n" \
	"} uniforms;\n"

#define ATTRIB_GLSL_LOCATION_VS 1

#define ATTRIB_VECTOR_GLSL_SOURCE \
	"layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_PS ) " ) in vec3 ps;\n" \
	"layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_VS ) " ) in vec3 vs;\n"

// Opengl vertex shader code (point format)

const std::string g_vectorShaderVertSourcePoint
(
	"#version 330\n"

	UNIFORM_BLOCK_VECTOR_GLSL_SOURCE

	ATTRIB_VECTOR_GLSL_SOURCE

	"void main()\n"
	"{\n"
	"   vec3 position = ps;\n"

	"   if( gl_VertexID == 1 )\n"
	"   {\n"
	"       position = vs;\n"
	"   }\n"

	"   gl_Position = vec4( position, 1.0 ) * uniforms.o2c;\n"
	"}\n"
);

// Opengl vertex shader code (vector format)

const std::string g_vectorShaderVertSourceVector
(
	"#version 330\n"

	UNIFORM_BLOCK_VECTOR_GLSL_SOURCE

	ATTRIB_VECTOR_GLSL_SOURCE

	"void main()\n"
	"{\n"
	"   vec3 position = ps;\n"

	"   if( gl_VertexID == 1 )\n"
	"   {\n"
	"       position += vs * uniforms.scale;"
	"   }\n"

	"   gl_Position = vec4( position, 1.0 ) * uniforms.o2c;\n"
	"}\n"
);

// Opengl vertex shader code (bivector format)

const std::string g_vectorShaderVertSourceBivector
(
	"#version 330\n"

	UNIFORM_BLOCK_VECTOR_GLSL_SOURCE

	ATTRIB_VECTOR_GLSL_SOURCE

	"void main()\n"
	"{\n"
	"   vec4 position = vec4( ps, 1.0 ) * uniforms.o2v;\n"

	"   if( gl_VertexID == 1 )\n"
	"   {\n"
	"       position.xyz += normalize( vs * mat3( uniforms.n2v ) ) * ( uniforms.scale * length( vs ) );\n"
	"   }\n"

	"   gl_Position = position * uniforms.v2c;\n"
	"}\n"
);

// Opengl fragment shader code

std::string const g_vectorShaderFragSource
(
	"#version 330\n"

	UNIFORM_BLOCK_VECTOR_GLSL_SOURCE

	"layout( location = 0 ) out vec4 cs;\n"

	"void main()\n"
	"{\n"
	"   cs = vec4( uniforms.color, uniforms.opacity );\n"
	"}\n"
);

//-----------------------------------------------------------------------------
// Helper Methods
//-----------------------------------------------------------------------------

void drawStrokedText(
	const ViewportGadget *viewportGadget,
	const std::string &text,
	const float size,
	const V2f &rasterPosition,
	const Style *style,
	const Style::State state
)
{
	ViewportGadget::RasterScope raster( viewportGadget );
	const V3f scale( size, -size, 1.f );

	glPushMatrix();
	glTranslatef( rasterPosition.x, rasterPosition.y, 0.f );
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
	style->renderText( Style::LabelText, text, state );

	glPopMatrix();
}

std::string primitiveVariableFromDataName( const std::string &dataName )
{
	const std::string name = boost::starts_with( dataName, g_primitiveVariablePrefix ) ? dataName.c_str() + g_primitiveVariablePrefixSize : "";

	return name;
}

auto stringFromValue = []( auto &&value ) -> std::string
{
	/// \todo Improve on this by adding custom formatters for `fmt::format` to
	/// handle V2f, V3f and Color3f.
	using T = std::decay_t<decltype( value )>;
	if constexpr( std::is_same_v<T, int> )
	{
		return fmt::format( "{}", value );
	}
	else if constexpr( std::is_same_v<T, float> )
	{
		return fmt::format( "{:.3f}", value );
	}
	else if constexpr( std::is_same_v<T, V2f> )
	{
		return fmt::format( "{:.3f}, {:.3f}", value.x, value.y );
	}
	else if constexpr( std::is_same_v<T, V3f> )
	{
		return fmt::format( "{:.3f}, {:.3f}, {:.3f}", value.x, value.y, value.z);
	}
	else if constexpr( std::is_same_v<T, Color3f> )
	{
		return fmt::format( "{:.3f}, {:.3f}, {:.3f}", value.x, value.y, value.z );
	}

	return "";
};

//-----------------------------------------------------------------------------
// VisualiserGadget
//-----------------------------------------------------------------------------

enum class VisualiserShaderType
{
	Color,
	VertexLabel
};

// The gadget that does the actual opengl drawing of the shaded primitive
class VisualiserGadget : public Gadget
{

	public :

		explicit VisualiserGadget( const VisualiserTool &tool, const std::string &name = defaultName<VisualiserGadget>() ) :
			Gadget( name ),
			m_tool( &tool ),
			m_colorShader(),
			m_colorUniformBuffer(),
			m_vertexLabelShader(),
			m_vertexLabelUniformBuffer(),
			m_cursorVertexValue()
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

			const VisualiserTool::Mode mode = (VisualiserTool::Mode)m_tool->modePlug()->getValue();

			if( layer == Gadget::Layer::MidFront )
			{
				renderColorVisualiser( viewportGadget, mode );
				renderVectorVisualiser( viewportGadget, mode );
			}

			else if( layer == Gadget::Layer::Front )
			{
				renderColorValue( viewportGadget, style, mode );
				renderVertexLabelValue( viewportGadget, style, mode );
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

		friend VisualiserTool;

		void buildShader( IECoreGL::ConstShaderPtr &shader, const std::string &vertSource, const std::string &fragSource ) const
		{
			if( !shader )
			{
				shader = IECoreGL::ShaderLoader::defaultShaderLoader()->create(
					vertSource, std::string(), fragSource
				);
				if( shader )
				{
					const GLuint program = shader->program();
					const GLuint blockIndex = glGetUniformBlockIndex( program, "UniformBlock" );
					if( blockIndex != GL_INVALID_INDEX )
					{
						glUniformBlockBinding( program, blockIndex, g_uniformBlockBindingIndex );
					}
				}
			}
		}

		/// Renders the color visualiser for the given `ViewportGadget`. In general, each visualiser
		/// is reponsible for determining if it should be drawn for the given `mode`. Objects may
		/// have different data types for the same variable name, so a visualiser's suitability may
		/// vary per-object.
		void renderColorVisualiser( const ViewportGadget *viewportGadget, VisualiserTool::Mode mode ) const
		{
			// Get the name of the primitive variable to visualise
			const std::string name = primitiveVariableFromDataName( m_tool->dataNamePlug()->getValue() );
			if(
				name.empty() ||
				(
					mode != VisualiserTool::Mode::Auto &&
					mode != VisualiserTool::Mode::Color &&
					mode != VisualiserTool::Mode::ColorAutoRange
				)
			)
			{
				return;
			}

			buildShader( m_colorShader, g_colorShaderVertSource, g_colorShaderFragSource );

			if( !m_colorShader )
			{
				return;
			}

			// Get the cached converter from IECoreGL, this is used to convert primitive
			// variable data to opengl buffers which will be shared with the IECoreGL renderer
			IECoreGL::CachedConverter *converter = IECoreGL::CachedConverter::defaultCachedConverter();

			GLint uniformBinding;
			glGetIntegerv( GL_UNIFORM_BUFFER_BINDING, &uniformBinding );

			if( !m_colorUniformBuffer )
			{
				GLuint buffer = 0u;
				glGenBuffers( 1, &buffer );
				glBindBuffer( GL_UNIFORM_BUFFER, buffer );
				glBufferData( GL_UNIFORM_BUFFER, sizeof( UniformBlockColorShader ), 0, GL_DYNAMIC_DRAW );
				m_colorUniformBuffer.reset( new IECoreGL::Buffer( buffer ) );
			}

			glBindBufferBase( GL_UNIFORM_BUFFER, g_uniformBlockBindingIndex, m_colorUniformBuffer->buffer() );

			// Get min/max values and colors and opacity
			UniformBlockColorShader uniforms;
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
			glUseProgram( m_colorShader->program() );

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

				ConstMeshPrimitivePtr mesh;
				M44f o2w;
				try
				{
					// Check path exists
					if( !location.scene().existsPlug()->getValue() )
					{
						continue;
					}

					// Extract mesh primitive
					mesh = runTimeCast<const MeshPrimitive>( location.scene().objectPlug()->getValue() );
					if( !mesh )
					{
						continue;
					}

					// Get the object to world transform
					ScenePlug::ScenePath path( location.path() );
					while( !path.empty() )
					{
						scope.setPath( &path );
						o2w = o2w * location.scene().transformPlug()->getValue();
						path.pop_back();
					}
				}
				catch( const std::exception & )
				{
					/// \todo Ideally the GL state would be handled by `IECoreGL::State` and related classes
					/// which would restore the GL state via RAII in the case of exceptions.
					/// But those don't handle everything we need like shader attribute block alignment,
					/// `GL_POLYGON_OFFSET` and more, so we use try / catch blocks throughout this tool.
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

				if(
					mode == VisualiserTool::Mode::Auto && (
						vData->typeId() == IntVectorDataTypeId ||  // Will be handled by `renderVertexLabelValue()` instead.
						vData->typeId() == V3fVectorDataTypeId  // Will be handled by `renderVectorVisualiser()` instead.
					)
				)
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

		/// See comment for `renderColorVisualiser()` for requirements for handling `mode`.
		void renderColorValue( const ViewportGadget *viewportGadget, const Style *style, VisualiserTool::Mode mode ) const
		{
			// Display value at cursor as text

			std::optional<V2f> cursorPos = m_tool->cursorPos();
			if( !cursorPos || !std::holds_alternative<std::monostate>( cursorVertexValue() ) )
			{
				return;
			}

			if(
				mode != VisualiserTool::Mode::Auto &&
				mode != VisualiserTool::Mode::Color &&
				mode != VisualiserTool::Mode::ColorAutoRange
			)
			{
				return;
			}

			const VisualiserTool::CursorValue value = m_tool->cursorValue();

			if(
				mode == VisualiserTool::Mode::Auto && (
					std::holds_alternative<int>( value ) ||
					std::holds_alternative<V3f>( value )
				)
			)
			{
				return;
			}

			if( !std::holds_alternative<std::monostate>( value ) )
			{
				const std::string text = std::visit( stringFromValue, value );

				if( !text.empty() )
				{
					// Draw in raster space
					//
					// NOTE : It seems that Gaffer defines the origin of raster space as the top left corner
					//        of the viewport, however the style text drawing functions assume that y increases
					//        "up" the screen rather than "down", so invert y to ensure text is not upside down.

					drawStrokedText(
						viewportGadget,
						text,
						m_tool->sizePlug()->getValue(),
						cursorPos.value(),
						style,
						Style::State::NormalState
					);
				}
			}
		}

		/// See comment for `renderColorVisualiser()` for requirements for handling `mode`.
		void renderVertexLabelValue( const ViewportGadget *viewportGadget, const Style *style, VisualiserTool::Mode mode ) const
		{
			if( mode != VisualiserTool::Mode::Auto && mode != VisualiserTool::Mode::VertexLabel )
			{
				return;
			}

			buildShader( m_vertexLabelShader, g_vertexLabelShaderVertSource, g_vertexLabelShaderFragSource );

			if( !m_vertexLabelShader )
			{
				return;
			}

			// Get the cached converter from IECoreGL, this is used to convert primitive
			// variable data to opengl buffers which will be shared with the IECoreGL renderer

			IECoreGL::CachedConverter *converter = IECoreGL::CachedConverter::defaultCachedConverter();

			GLint uniformBinding;
			glGetIntegerv( GL_UNIFORM_BUFFER_BINDING, &uniformBinding );

			if( !m_vertexLabelUniformBuffer )
			{
				GLuint buffer = 0u;
				glGenBuffers( 1, &buffer );
				glBindBuffer( GL_UNIFORM_BUFFER, buffer );
				glBufferData( GL_UNIFORM_BUFFER, sizeof( UniformBlockVertexLabelShader ), 0, GL_DYNAMIC_DRAW );
				glBindBuffer( GL_UNIFORM_BUFFER, uniformBinding );
				m_vertexLabelUniformBuffer.reset( new IECoreGL::Buffer( buffer ) );
			}

			UniformBlockVertexLabelShader uniforms;

			GLint storageBinding;
			glGetIntegerv( GL_SHADER_STORAGE_BUFFER_BINDING, &storageBinding );

			if( !m_vertexLabelStorageBuffer )
			{
				GLuint buffer = 0u;
				glGenBuffers( 1, &buffer );
				m_vertexLabelStorageBuffer.reset( new IECoreGL::Buffer( buffer ) );
			}

			// Save opengl state

			GLfloat pointSize;
			glGetFloatv( GL_POINT_SIZE, &pointSize );

			GLint depthFunc;
			glGetIntegerv( GL_DEPTH_FUNC, &depthFunc );

			GLboolean depthWriteEnabled;
			glGetBooleanv( GL_DEPTH_WRITEMASK, &depthWriteEnabled );

			const GLboolean depthEnabled = glIsEnabled( GL_DEPTH_TEST );
			const GLboolean multisampleEnabled = glIsEnabled( GL_MULTISAMPLE );

			GLint shaderProgram;
			glGetIntegerv( GL_CURRENT_PROGRAM, &shaderProgram );

			GLint arrayBinding;
			glGetIntegerv( GL_ARRAY_BUFFER_BINDING, &arrayBinding );

			// Get the world to clip space matrix

			Imath::M44f v2c;
			glGetFloatv( GL_PROJECTION_MATRIX, v2c.getValue() );
			const Imath::M44f w2c = viewportGadget->getCameraTransform().gjInverse() * v2c;

			// Get raster space bounding box

			const Imath::Box2f rasterBounds = Imath::Box2f(
				Imath::V2f( 0.f ),
				Imath::V2f(
					static_cast<float>( viewportGadget->getViewport().x ),
					static_cast<float>( viewportGadget->getViewport().y )
				)
			);

			// Get text raster space scale and colour
			//
			// NOTE : It seems that Gaffer defines the origin of raster space as the top left corner
			//        of the viewport, however the style text drawing functions assume that y increases
			//        "up" the screen rather than "down", so invert y to ensure text is not upside down.

			const float size = m_tool->sizePlug()->getValue();
			const Imath::V3f scale( size, -size, 1.f );

			// Get cursor raster position

			VisualiserTool::CursorValue cursorVertexValue;
			const std::optional<V2f> cursorRasterPos = m_tool->cursorPos();
			std::optional<V2f> cursorVertexRasterPos;
			float minDistance2 = std::numeric_limits<float>::max();

			// Get cursor search radius
			//
			// NOTE : when the cursor position is invalid set the radius to zero to disable search.

			const Imath::Box2i viewport( Imath::V2i( 0 ), viewportGadget->getViewport() );
			const float cursorRadius2 =
				cursorRasterPos && viewport.intersects( cursorRasterPos.value() ) ?
				g_cursorRadius2 :
				0.f;

			const std::string dataName = m_tool->dataNamePlug()->getValue();
			const std::string primitiveVariableName = primitiveVariableFromDataName( dataName );

			float cursorVertexValueTextScale = 2.f;

			// Loop through current selection

			for( const auto &location : m_tool->selection() )
			{
				GafferScene::ScenePlug::PathScope scope( &location.context() , &location.path() );

				ConstPrimitivePtr primitive;
				Imath::M44f o2w;
				try
				{
					// Check path exists
					if( !location.scene().existsPlug()->getValue() )
					{
						continue;
					}

					primitive = runTimeCast<const Primitive>( location.scene().objectPlug()->getValue() );
					if( !primitive )
					{
						continue;
					}

					// Get the object to world transform
					GafferScene::ScenePlug::ScenePath path( location.path() );
					while( !path.empty() )
					{
						scope.setPath( &path );
						o2w = o2w * location.scene().transformPlug()->getValue();
						path.pop_back();
					}
				}
				catch( const std::exception & )
				{
					continue;
				}

				ConstDataPtr vData = nullptr;

				if( dataName != g_vertexIndexDataName )
				{
					vData = primitive->expandedVariableData<Data>(
						primitiveVariableName,
						IECoreScene::PrimitiveVariable::Vertex,
						false /* throwIfInvalid */
					);

					if( !vData )
					{
						continue;
					}

					if(
						mode == VisualiserTool::Mode::Auto &&
						primitive->typeId() == MeshPrimitive::staticTypeId() &&
						vData->typeId() != IntVectorDataTypeId &&
						vData->typeId() != V3fVectorDataTypeId
					)
					{
						// Will be handled by `renderColorVisualiser()` instead.
						// If the data type is V3f data, we continue right before
						// drawing the per-vertex label in order to get and display
						// the value closest to the cursor.
						continue;
					}

					if(
						vData->typeId() != IntVectorDataTypeId &&
						vData->typeId() != FloatVectorDataTypeId &&
						vData->typeId() != V2fVectorDataTypeId &&
						vData->typeId() != V3fVectorDataTypeId &&
						vData->typeId() != Color3fVectorDataTypeId
					)
					{
						continue;
					}
				}

				if( mode == VisualiserTool::Mode::Auto && vData && vData->typeId() == V3fVectorDataTypeId )
				{
					cursorVertexValueTextScale = 1.f;
				}
				else
				{
					cursorVertexValueTextScale = 2.f;
				}

				// Find "P" vertex attribute
				//
				// TODO : We need to use the same polygon offset as the Viewer uses when it draws the
				//        primitive in polygon points mode. For mesh primitives topology may be different,
				//        primitive variables were converted to face varying and the mesh triangulated
				//        with vertex positions duplicated. This means that gl_VertexID in the shader
				//        no longer corresponds to the vertex id we want to display. It also means there
				//        may be multiple vertices in the IECoreGL mesh for each vertex in the IECore mesh.
				//        To get the correct polygon offset we need to draw the mesh using the same
				//        OpenGL draw call as the Viewer used so we must draw the IECoreGL mesh. So
				//        we need to search for the (posibly multiple) vertices that correspond to each
				//        original vertex. If any of these IECoreGL mesh vertices are visible we display
				//        the IECore mesh vertex id. To accelerate the search we build a multi map keyed
				//        on vertex position. This assumes that the triangulation and/or conversion to
				//        face varying attributes processing in IECore does not alter the position of the
				//        vertices. The building of this map is done after we issue the draw call for the
				//        mesh primitive, this gives OpenGL an opportunity to concurrently execute the
				//        visibility pass while we are building the map, ready for the map buffer operation.
				//        For points and curves primitives there is no polygon offset. For all primitives
				//        there may be a slight slight precision difference in o2c transform so push vertices
				//        forward.
				// NOTE : a cheap alternative approach that solves most of the above problems is to draw
				//        the visibility pass using "fat" points which cover multiple pixels. This still
				//        has problems for vertices with negative surrounding curvature ...
				//
				// NOTE : We use the primitive variable from the IECore primitive as that has
				//        vertex interpolation.

				ConstV3fVectorDataPtr pData = primitive->expandedVariableData<IECore::V3fVectorData>(
					g_pName,
					IECoreScene::PrimitiveVariable::Vertex,
					false /* throwIfInvalid */
				);

				if( !pData )
				{
					continue;
				}

				// Retrieve cached opengl buffer data

				auto pBuffer = runTimeCast<const IECoreGL::Buffer>( converter->convert( pData.get() ) );

				// Compute object to clip matrix

				uniforms.o2c = o2w * w2c;

				// Upload opengl uniform block data

				glBindBufferBase( GL_UNIFORM_BUFFER, g_uniformBlockBindingIndex, m_vertexLabelUniformBuffer->buffer() );
				glBufferData(
					GL_UNIFORM_BUFFER,
					sizeof( UniformBlockVertexLabelShader ),
					&uniforms,
					GL_DYNAMIC_DRAW
				);

				// Ensure storage buffer capacity

				glBindBufferBase(
					GL_SHADER_STORAGE_BUFFER,
					g_storageBlockBindingIndex,
					m_vertexLabelStorageBuffer->buffer()
				);

				const std::size_t storageCapacity =
					( pData->readable().size() / static_cast<std::size_t>( 32 ) ) +
					static_cast<std::size_t>( 1 );
				const std::size_t storageSize = sizeof( std::uint32_t ) * storageCapacity;

				if( m_vertexLabelStorageCapacity < storageCapacity )
				{
					glBufferData( GL_SHADER_STORAGE_BUFFER, storageSize, 0, GL_DYNAMIC_DRAW );
					m_vertexLabelStorageCapacity = storageCapacity;
				}

				// Clear storage buffer
				//
				// NOTE : Shader writes to individual bits using atomicOr instruction so region of
				//        storage buffer being used for current object needs to be cleared to zero

				const GLuint zeroValue = 0u;
				glClearBufferSubData(
					GL_SHADER_STORAGE_BUFFER,
					GL_R32UI,
					0,
					storageSize,
					GL_RED_INTEGER,
					GL_UNSIGNED_INT,
					&zeroValue
				);

				// Set opengl state

				glPointSize( 3.f );
				glDepthFunc( GL_LEQUAL );
				if( !depthEnabled )
				{
					glEnable( GL_DEPTH_TEST );
				}
				if( depthEnabled )
				{
					glDisable( GL_DEPTH_TEST );
				}
				if( depthWriteEnabled )
				{
					glDepthMask( GL_FALSE );
				}
				if( multisampleEnabled )
				{
					glDisable( GL_MULTISAMPLE );
				}

				// Set opengl vertex attribute array state

				glPushClientAttrib( GL_CLIENT_VERTEX_ARRAY_BIT );

				glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_PS, 0 );
				glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_PS );

				// Set visibility pass shader

				glUseProgram( m_vertexLabelShader->program() );

				// Draw points and ouput visibility to storage buffer

				glBindBuffer( GL_ARRAY_BUFFER, pBuffer->buffer() );
				glVertexAttribPointer(
					ATTRIB_GLSL_LOCATION_PS,
					3,
					GL_FLOAT,
					GL_FALSE,
					0,
					nullptr
				);
				glDrawArrays( GL_POINTS, 0, static_cast< GLsizei >( pData->readable().size() ) );

				// Restore opengl state

				glPopClientAttrib();
				glBindBuffer( GL_ARRAY_BUFFER, arrayBinding );
				glBindBuffer( GL_UNIFORM_BUFFER, uniformBinding );

				glPointSize( pointSize );
				glDepthFunc( depthFunc );
				if( !depthEnabled )
				{
					glDisable( GL_DEPTH_TEST );
				}
				if( depthEnabled )
				{
					glEnable( GL_DEPTH_TEST );
				}
				if( depthWriteEnabled )
				{
					glDepthMask( GL_TRUE );
				}
				if( multisampleEnabled )
				{
					glEnable( GL_MULTISAMPLE );
				}
				glUseProgram( shaderProgram );

				// Map storage buffer

				auto vBuffer = static_cast<const std::uint32_t*>(
					glMapBufferRange(
						GL_SHADER_STORAGE_BUFFER,
						0,
						storageSize,
						GL_MAP_READ_BIT
					)
				);
				glBindBuffer( GL_SHADER_STORAGE_BUFFER, storageBinding );

				// Draw vertex ids or int variable offset to vertex position in raster space

				if( vBuffer )
				{
					ViewportGadget::RasterScope raster( viewportGadget );

					VisualiserTool::CursorValue vertexValue;
					const std::vector<Imath::V3f> &points = pData->readable();
					for( size_t i = 0; i < points.size(); ++i )
					{
						// Check visibility of vertex

						const std::uint32_t index = static_cast<std::uint32_t>( i ) / static_cast<std::uint32_t>( 32u );
						const std::uint32_t value = static_cast<std::uint32_t>( i ) % static_cast<std::uint32_t>( 32u );

						if( vBuffer[index] & ( static_cast<std::uint32_t>( 1u ) << value ) )
						{
							// Transform vertex position to raster space and do manual scissor test
							//
							// NOTE : visibility pass encorporates scissor test which culls most
							//        vertices however some will slip through as visibility pass
							//        draws "fat" points. bounds test is cheap.

							Imath::V3f worldPos;
							o2w.multVecMatrix( points[i], worldPos );
							std::optional<V2f> rasterPos = viewportGadget->worldToRasterSpace( worldPos );
							if( rasterBounds.intersects( rasterPos.value() ) )
							{
								if( !vData )
								{
									vertexValue = (int)i;
								}
								else
								{
									if( auto iData = runTimeCast<const IntVectorData>( vData.get() ) )
									{
										vertexValue = iData->readable()[i];
									}
									if( auto fData = runTimeCast<const FloatVectorData>( vData.get() ) )
									{
										vertexValue = fData->readable()[i];
									}
									if( auto v2fData = runTimeCast<const V2fVectorData>( vData.get() ) )
									{
										vertexValue = v2fData->readable()[i];
									}
									if( auto v3fData = runTimeCast<const V3fVectorData>( vData.get() ) )
									{
										vertexValue = v3fData->readable()[i];
									}
									if( auto c3fData = runTimeCast<const Color3fVectorData>( vData.get() ) )
									{
										vertexValue = c3fData->readable()[i];
									}
								}

								// Update cursor value
								//
								// NOTE : We defer drawing of the value currently under the cursor, so
								//        draw the last value label if we replace the cursor value

								if( cursorRasterPos )
								{
									const float distance2 = ( cursorRasterPos.value() - rasterPos.value() ).length2();
									if( ( distance2 < cursorRadius2 ) && ( distance2 < minDistance2 ) )
									{
										std::swap( cursorVertexValue, vertexValue );
										std::swap( cursorVertexRasterPos, rasterPos );
										minDistance2 = distance2;
									}
								}

								if( mode == VisualiserTool::Mode::Auto && vData && vData->typeId() == V3fVectorDataTypeId )
								{
									// Do everything except drawing the per-vertex value. That will
									// be handled by `renderVectorVisualiser()` instead.
									continue;
								}

								// Draw value label

								if( !std::holds_alternative<std::monostate>( vertexValue ) && rasterPos )
								{
									const std::string text = std::visit( stringFromValue, vertexValue );

									drawStrokedText(
										viewportGadget,
										text,
										size,
										V2f(
											rasterPos.value().x - style->textBound( GafferUI::Style::LabelText, text ).size().x * 0.5f * scale.x,
											rasterPos.value().y
										),
										style,
										Style::State::NormalState
									);
								}
							}
						}
					}

					// unmap storage buffer

					glBindBuffer( GL_SHADER_STORAGE_BUFFER, m_vertexLabelStorageBuffer->buffer() );
					glUnmapBuffer( GL_SHADER_STORAGE_BUFFER );
					glBindBuffer( GL_SHADER_STORAGE_BUFFER, storageBinding );
				}

				glBindBuffer( GL_SHADER_STORAGE_BUFFER, storageBinding );
			}

			// Draw cursor vertex

			if( !std::holds_alternative<std::monostate>( cursorVertexValue ) && cursorVertexRasterPos )
			{
				GafferUI::ViewportGadget::RasterScope raster( viewportGadget );

				std::string const text = std::visit( stringFromValue, cursorVertexValue );

				drawStrokedText(
					viewportGadget,
					text,
					scale.x * cursorVertexValueTextScale,
					V2f(
						cursorVertexRasterPos.value().x - style->textBound( GafferUI::Style::LabelText, text ).size().x * 0.5f * cursorVertexValueTextScale * scale.x,
						cursorVertexRasterPos.value().y
					),
					style,
					Style::State::NormalState
				);
			}

			// Set tool cursor vertex id

			m_cursorVertexValue = cursorVertexValue;
		}

		void renderVectorVisualiser( const ViewportGadget *viewportGadget, VisualiserTool::Mode mode ) const
		{
			const std::string name = primitiveVariableFromDataName( m_tool->dataNamePlug()->getValue() );
			if( name.empty() || mode != VisualiserTool::Mode::Auto )
			{
				return;
			}

			buildShader( m_vectorShaderPoint, g_vectorShaderVertSourcePoint, g_vectorShaderFragSource );
			buildShader( m_vectorShaderVector, g_vectorShaderVertSourceVector, g_vectorShaderFragSource );
			buildShader( m_vectorShaderBivector, g_vectorShaderVertSourceBivector, g_vectorShaderFragSource );

			if( !m_vectorShaderPoint || !m_vectorShaderVector || !m_vectorShaderBivector )
			{
				return;
			}

			// Get the cached converter from IECoreGL, this is used to convert primitive
			// variable data to opengl buffers which will be shared with the IECoreGL renderer
			IECoreGL::CachedConverter *converter = IECoreGL::CachedConverter::defaultCachedConverter();

			GLint uniformBinding;
			glGetIntegerv( GL_UNIFORM_BUFFER_BINDING, &uniformBinding );

			if( !m_vectorUniformBuffer )
			{
				GLuint buffer = 0u;
				glGenBuffers( 1, &buffer );
				glBindBuffer( GL_UNIFORM_BUFFER, buffer );
				glBufferData( GL_UNIFORM_BUFFER, sizeof( UniformBlockVectorShader ), 0, GL_DYNAMIC_DRAW );
				m_vectorUniformBuffer.reset( new IECoreGL::Buffer( buffer ) );
			}

			glBindBufferBase( GL_UNIFORM_BUFFER, g_uniformBlockBindingIndex, m_vectorUniformBuffer->buffer() );

			UniformBlockVectorShader uniforms;
			uniforms.color = m_tool->vectorColorPlug()->getValue();
			uniforms.opacity = m_tool->opacityPlug()->getValue();
			uniforms.scale = m_tool->vectorScalePlug()->getValue();

			// Get the world to view and view to clip space matrices
			const M44f w2v = viewportGadget->getCameraTransform().gjInverse();
			glGetFloatv( GL_PROJECTION_MATRIX, uniforms.v2c.getValue() );

			// Set OpenGL state
			GLfloat lineWidth;
			glGetFloatv( GL_LINE_WIDTH, &lineWidth );
			glLineWidth( 1.f );

			const GLboolean depthEnabled = glIsEnabled( GL_DEPTH_TEST );
			if( !depthEnabled )
			{
				glEnable( GL_DEPTH_TEST );
			}

			GLboolean depthWriteEnabled;
			glGetBooleanv( GL_DEPTH_WRITEMASK, &depthWriteEnabled );
			if( depthWriteEnabled )
			{
				glDepthMask( GL_FALSE );
			}

			GLboolean lineSmooth;
			glGetBooleanv( GL_LINE_SMOOTH, &lineSmooth );
			if( lineSmooth )
			{
				glDisable( GL_LINE_SMOOTH );
			}

			const GLboolean blendEnabled = glIsEnabled( GL_BLEND );
			if( !blendEnabled )
			{
				glEnable( GL_BLEND );
			}

			// Store current shader program to be restored after drawing.
			// We set the shader program for drawing vectors when we know
			// the interpretation of the visualised data, which may
			// be different per object.
			GLint shaderProgram;
			glGetIntegerv( GL_CURRENT_PROGRAM, &shaderProgram );
			std::optional<GLint> currentShaderProgram;

			// Set OpenGL vertex attribute array state
			GLint arrayBinding;
			glGetIntegerv( GL_ARRAY_BUFFER_BINDING, &arrayBinding );

			glPushClientAttrib( GL_CLIENT_VERTEX_ARRAY_BIT );

			glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_PS, 1 );
			glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_PS );
			glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_VS, 1 );
			glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_VS );

			// Loop through the current selection
			for( const auto &location : m_tool->selection() )
			{
				ScenePlug::PathScope scope( &location.context(), &location.path() );

				ConstPrimitivePtr primitive;
				M44f o2w;
				try
				{
					// Check path exists
					if( !location.scene().existsPlug()->getValue() )
					{
						continue;
					}

					// Extract primitive
					primitive = runTimeCast<const Primitive>( location.scene().objectPlug()->getValue() );
					if( !primitive )
					{
						continue;
					}

					// Get the object to world transform
					ScenePlug::ScenePath path( location.path() );
					while( !path.empty() )
					{
						scope.setPath( &path );
						o2w = o2w * location.scene().transformPlug()->getValue();
						path.pop_back();
					}
				}
				catch( const std::exception & )
				{
					continue;
				}

				// Find named vertex attribute
				// NOTE : Conversion to IECoreGL mesh may generate vertex attributes (eg. "N")
				// so check named primitive variable exists on IECore mesh primitive.
				const auto vIt = primitive->variables.find( name );
				if( vIt == primitive->variables.end() )
				{
					continue;
				}

				auto vData = runTimeCast<const V3fVectorData>( vIt->second.data );
				if( !vData )
				{
					// Will be handled by `renderColorVisualiser()` or `renderVertexLabelValue()` instead.
					continue;
				}

				if( vIt->second.interpolation == PrimitiveVariable::Uniform )
				{
					try
					{
						primitive = runTimeCast<const Primitive>( location.uniformPScene().objectPlug()->getValue() );
					}
					catch( const std::exception & )
					{
						continue;
					}

					if( !primitive )
					{
						continue;
					}
				}

				// Make sure we have "P" data and it is the correct type.
				const auto pIt = primitive->variables.find( g_pName );
				if( pIt == primitive->variables.end() )
				{
					continue;
				}

				auto pData = runTimeCast<const V3fVectorData>( pIt->second.data );
				if( !pData )
				{
					continue;
				}

				IECoreGL::ConstBufferPtr pBuffer = nullptr;
				IECoreGL::ConstBufferPtr vBuffer = nullptr;
				GLsizei vertexCount = 0;

				// Retrieve cached IECoreGL primitive

				if( vIt->second.interpolation != PrimitiveVariable::FaceVarying )
				{
					pBuffer = runTimeCast<const IECoreGL::Buffer>( converter->convert( pData.get() ) );
					vBuffer = runTimeCast<const IECoreGL::Buffer>( converter->convert( vData.get() ) );
					vertexCount = (GLsizei)pData->readable().size();
				}
				else
				{
					auto primitiveGL = runTimeCast<const IECoreGL::Primitive>( converter->convert( primitive.get() ) );
					if( !primitiveGL )
					{
						continue;
					}

					pBuffer = primitiveGL->getVertexBuffer( g_pName );
					vBuffer = primitiveGL->getVertexBuffer( name );
					vertexCount = primitiveGL->getVertexCount();
				}

				if( !pBuffer || !vBuffer )
				{
					continue;
				}

				GLint vDataProgram;
				switch( vData->getInterpretation() )
				{
					case GeometricData::Interpretation::Point :
						vDataProgram = m_vectorShaderPoint->program();
						break;
					case GeometricData::Interpretation::Normal :
						vDataProgram = m_vectorShaderBivector->program();
						break;
					default :
						vDataProgram = m_vectorShaderVector->program();
				}
				if( !currentShaderProgram || currentShaderProgram.value() != vDataProgram )
				{
					glUseProgram( vDataProgram );
					currentShaderProgram = vDataProgram;
				}

				// Compute object/normal to view and object to clip matrices
				uniforms.o2v = o2w * w2v;
				uniforms.n2v = ( uniforms.o2v.gjInverse() ).transpose();
				uniforms.o2c = uniforms.o2v * uniforms.v2c;

				// Upload OpenGL uniform block data
				glBufferData( GL_UNIFORM_BUFFER, sizeof( UniformBlockVectorShader ), &uniforms, GL_DYNAMIC_DRAW );

				// Instance a line segment for each element of vector data
				glBindBuffer( GL_ARRAY_BUFFER, pBuffer->buffer() );
				glVertexAttribPointer( ATTRIB_GLSL_LOCATION_PS, 3, GL_FLOAT, GL_FALSE, 0, nullptr );
				glBindBuffer( GL_ARRAY_BUFFER, vBuffer->buffer() );
				glVertexAttribPointer( ATTRIB_GLSL_LOCATION_VS, 3, GL_FLOAT, GL_FALSE, 0, nullptr );
				glDrawArraysInstanced( GL_LINES, 0, 2, vertexCount );

			}

			// Restore OpenGL state

			glPopClientAttrib();
			glBindBuffer( GL_ARRAY_BUFFER, arrayBinding );
			glBindBuffer( GL_UNIFORM_BUFFER, uniformBinding );

			glLineWidth( lineWidth );

			if( lineSmooth )
			{
				glEnable( GL_LINE_SMOOTH );
			}
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

		VisualiserTool::CursorValue cursorVertexValue() const
		{
			return m_cursorVertexValue;
		}

		const VisualiserTool *m_tool;
		mutable IECoreGL::ConstShaderPtr m_colorShader;
		mutable IECoreGL::ConstBufferPtr m_colorUniformBuffer;
		mutable IECoreGL::ConstShaderPtr m_vertexLabelShader;
		mutable IECoreGL::ConstBufferPtr m_vertexLabelUniformBuffer;
		mutable IECoreGL::ConstShaderPtr m_vectorShaderPoint;
		mutable IECoreGL::ConstShaderPtr m_vectorShaderVector;
		mutable IECoreGL::ConstShaderPtr m_vectorShaderBivector;
		mutable IECoreGL::ConstBufferPtr m_vectorUniformBuffer;

		mutable IECoreGL::ConstBufferPtr m_vertexLabelStorageBuffer;
		mutable std::size_t m_vertexLabelStorageCapacity;

		mutable VisualiserTool::CursorValue m_cursorVertexValue;
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

//-----------------------------------------------------------------------------
// VisualiserTool
//-----------------------------------------------------------------------------

GAFFER_NODE_DEFINE_TYPE( VisualiserTool )

Tool::ToolDescription<VisualiserTool, SceneView> VisualiserTool::m_toolDescription;

size_t VisualiserTool::g_firstPlugIndex = 0;

VisualiserTool::VisualiserTool( SceneView *view, const std::string &name ) : SelectionTool( view, name ),
	m_preRenderConnection(),
	m_buttonPressConnection(),
	m_dragBeginConnection(),
	m_gadget( new VisualiserGadget( *this ) ),
	m_selection(),
	m_cursorPos(),
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

	addChild( new StringPlug( "dataName", Plug::In, g_primitiveVariablePrefix + "uv" ) );
	addChild( new FloatPlug( "opacity", Plug::In, g_opacityDefault, g_opacityMin, g_opacityMax ) );
	addChild( new IntPlug( "mode", Plug::In, (int)Mode::Auto, (int)Mode::First, (int)Mode::Last ) );
	addChild( new V3fPlug( "valueMin", Plug::In, g_valueMinDefault ) );
	addChild( new V3fPlug( "valueMax", Plug::In, g_valueMaxDefault ) );
	addChild( new FloatPlug( "size", Plug::In, g_textSizeDefault, g_textSizeMin ) );
	addChild( new FloatPlug( "vectorScale", Plug::In, g_vectorScaleDefault, g_vectorScaleMin ) );
	addChild( new Color3fPlug( "vectorColor", Plug::In, g_vectorColorDefault ) );
	addChild( new ScenePlug( "__scene", Plug::In ) );
	addChild( new ScenePlug( "__uniformPScene", Plug::In ) );

	ScenePlug *inScene = view->inPlug<ScenePlug>();

	PathFilterPtr filter = new PathFilter( "__resampleFilter" );
	filter->pathsPlug()->setValue( new StringVectorData( { "/..." } ) );
	addChild( filter );

	ResamplePrimitiveVariablesPtr resamplePrimVars = new ResamplePrimitiveVariables( "__resamplePrimVars" );
	addChild( resamplePrimVars );
	resamplePrimVars->inPlug()->setInput( inScene );
	resamplePrimVars->namesPlug()->setValue( "P" );
	resamplePrimVars->interpolationPlug()->setValue( IECoreScene::PrimitiveVariable::Interpolation::Uniform );
	resamplePrimVars->filterPlug()->setInput( filter->outPlug() );

	internalScenePlug()->setInput( inScene);
	internalSceneUniformPPlug()->setInput( resamplePrimVars->outPlug() );

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

FloatPlug *VisualiserTool::vectorScalePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 6 );
}

const FloatPlug *VisualiserTool::vectorScalePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 6 );
}

Color3fPlug *VisualiserTool::vectorColorPlug()
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 7 );
}

const Color3fPlug *VisualiserTool::vectorColorPlug() const
{
	return getChild<Color3fPlug>( g_firstPlugIndex + 7 );
}

ScenePlug *VisualiserTool::internalScenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 8 );
}

const ScenePlug *VisualiserTool::internalScenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 8 );
}

ScenePlug *VisualiserTool::internalSceneUniformPPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 9 );
}

const ScenePlug *VisualiserTool::internalSceneUniformPPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 9 );
}

const std::vector<VisualiserTool::Selection> &VisualiserTool::selection() const
{
	return m_selection;
}

VisualiserTool::CursorPosition VisualiserTool::cursorPos() const
{
	return m_cursorPos;
}

const VisualiserTool::CursorValue VisualiserTool::cursorValue() const
{
	return m_cursorValue;
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

	// NOTE : only schedule redraw if tool active

	if( activePlug()->getValue() )
	{
		view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	}
}

void VisualiserTool::leave( const ButtonEvent &event )
{
	m_cursorPos = CursorPosition( std::nullopt );

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
		if( event.modifiers == KeyEvent::Modifiers::None )
		{
			sizePlug()->setValue( sizePlug()->getValue() + g_textSizeInc );
		}
		else if( event.modifiers == KeyEvent::Modifiers::Shift )
		{
			vectorScalePlug()->setValue( vectorScalePlug()->getValue() + g_vectorScaleInc );
		}
	}
	else if( event.key == "Minus" || event.key == "Underscore" )
	{
		if( event.modifiers == KeyEvent::Modifiers::None )
		{
			sizePlug()->setValue( std::max( sizePlug()->getValue() - g_textSizeInc, g_textSizeMin ) );
		}
		else if( event.modifiers == KeyEvent::Modifiers::Shift )
		{
			vectorScalePlug()->setValue( std::max( vectorScalePlug()->getValue() - g_vectorScaleInc, g_vectorScaleMin ) );
		}
	}

	return false;
}

bool VisualiserTool::buttonPress( const ButtonEvent &event )
{
	m_valueAtButtonPress = std::monostate();
	m_initiatedDrag = false;

	if( event.button & ButtonEvent::Left && !( event.modifiers & GafferUI::ButtonEvent::Modifiers::Control ) )
	{
		updateCursorValue();
		if( !std::holds_alternative<std::monostate>( m_cursorValue ) )
		{
			m_valueAtButtonPress = m_cursorValue;
			return true;
		}
	}

	return false;
}

bool VisualiserTool::buttonRelease( const ButtonEvent &event )
{
	m_valueAtButtonPress = std::monostate();
	m_initiatedDrag = false;

	return false;
}

RunTimeTypedPtr VisualiserTool::dragBegin( const DragDropEvent &event )
{
	m_initiatedDrag = false;

	if( std::holds_alternative<std::monostate>( m_valueAtButtonPress ) )
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

	if( std::holds_alternative<int>( m_valueAtButtonPress ) )
	{
		return new IntData( std::get<int>( m_valueAtButtonPress ) );
	}
	if( std::holds_alternative<float>( m_valueAtButtonPress ) )
	{
		return new FloatData( std::get<float>( m_valueAtButtonPress ) );
	}
	if( std::holds_alternative<V2f>( m_valueAtButtonPress ) )
	{
		return new V2fData( std::get<V2f>( m_valueAtButtonPress ) );
	}
	if( std::holds_alternative<V3f>( m_valueAtButtonPress ) )
	{
		return new V3fData( std::get<V3f>( m_valueAtButtonPress ) );
	}
	if( std::holds_alternative<Color3f>( m_valueAtButtonPress ) )
	{
		return new Color3fData( std::get<Color3f>( m_valueAtButtonPress ) );
	}

	return RunTimeTypedPtr();
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
		plug == internalScenePlug()->transformPlug() ||
		plug == internalSceneUniformPPlug()->objectPlug() ||
		plug == internalSceneUniformPPlug()->transformPlug()
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
		plug == modePlug() ||
		plug == vectorScalePlug() ||
		plug == vectorColorPlug()
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
		m_selection.emplace_back( *scene, *internalSceneUniformPPlug(), *it, *view()->context() );
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
	CursorValue cursorValue = m_cursorValue;
	m_cursorValue = std::monostate();

	// NOTE : during a drag do not update the cursor value

	if( m_initiatedDrag || !cursorPos() )
	{
		return;
	}

	const std::string dataName = dataNamePlug()->getValue();

	// We draw all visualisation types each time, and the vertex label visualisation
	// resets the `cursorVertexValue()` each time before potentially setting it to
	// the closest point. So if there is no such point, this will be `std::monostate`.
	CursorValue v = static_cast<VisualiserGadget *>( m_gadget.get() )->cursorVertexValue();
	if( !std::holds_alternative<std::monostate>( v ) )
	{
		m_cursorValue = v;
		return;
	}

	if( modePlug()->getValue() == (int)Mode::VertexLabel )
	{
		// If `VisualiserGadget::cursorVertexValue()` is not set and we're in `VertexLabel`
		// mode, it means the label failed to draw (for example if the interpolation is not
		// supported). Don't set the cursor value to a sampled value in that case.
		return;
	}

	const std::string name = primitiveVariableFromDataName( dataName );
	if( name.empty() )
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

		if( !sg->objectAt( view()->viewportGadget()->rasterToGadgetSpace( cursorPos().value(), sg ), path ) )
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

	ConstMeshPrimitivePtr mesh;
	try
	{
		mesh = runTimeCast<const MeshPrimitive>( item.scene().objectPlug()->getValue() );
	}
	catch( const std::exception & )
	{
		return;
	}

	if( !mesh )
	{
		return;
	}

	// Check mesh has named primitive variable

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

	const LineSegment3f line = view()->viewportGadget()->rasterToWorldSpace( cursorPos().value() ) *
			item.scene().fullTransform( path ).gjInverse();
	if( !evalData.evaluator->intersectionPoint( line.p0, line.direction(), result.get() ) )
	{
		return;
	}

	// Update value from intersection result

	switch( vIt->second.data->typeId() )
	{
		case IntVectorDataTypeId :
			cursorValue = result->intPrimVar( evalData.triMesh->variables.at( name ) );
			break;
		case FloatVectorDataTypeId :
			cursorValue = result->floatPrimVar( evalData.triMesh->variables.at( name ) );
			break;
		case V2fVectorDataTypeId :
			cursorValue = result->vec2PrimVar( evalData.triMesh->variables.at( name ) );
			break;
		case V3fVectorDataTypeId :
			cursorValue = result->vectorPrimVar( evalData.triMesh->variables.at( name ) );
			break;
		case Color3fVectorDataTypeId :
			cursorValue = result->colorPrimVar( evalData.triMesh->variables.at( name ) );
			break;
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
	const ScenePlug &uniformPScene,
	const ScenePlug::ScenePath &path,
	const Context &context
) : m_scene( &scene ), m_uniformPScene( &uniformPScene ), m_path( path ), m_context( &context )
{

}

const ScenePlug &VisualiserTool::Selection::scene() const
{
	return *m_scene;
}

const ScenePlug &VisualiserTool::Selection::uniformPScene() const
{
	return *m_uniformPScene;
}

const ScenePlug::ScenePath &VisualiserTool::Selection::path() const
{
	return m_path;
}

const Context &VisualiserTool::Selection::context() const
{
	return *m_context;
}
