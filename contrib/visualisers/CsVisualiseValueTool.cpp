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

#include <IECoreGL/Export.h>
#include <IECoreGL/GL.h>
#include <IECoreGL/Renderable.h>
#include <IECoreGL/Shader.h>
#include <IECoreGL/TypedStateComponent.h>
#include <IECoreGL/TypeIds.h>
#include <IECore/RunTimeTyped.h>
#include <IECoreScene/PrimitiveVariable.h>
#include <IECore/Export.h>
#include <IECore/VectorTypedData.h>
#include <IECore/LRUCache.h>

#include <Gaffer/Version.h>

IECORE_PUSH_DEFAULT_VISIBILITY
#if GAFFER_COMPATIBILITY_VERSION < MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 3 )
#include <OpenEXR/ImathBox.h>
#else
#include <Imath/ImathBox.h>
#endif
IECORE_POP_DEFAULT_VISIBILITY

#define private public
#include <IECoreGL/Buffer.h>
#include <IECoreGL/Primitive.h>
#undef private

#include "CsVisualiseValueTool.h"

#include <Gaffer/Metadata.h>
#include <Gaffer/MetadataAlgo.h>
#include <GafferUI/Gadget.h>
#include <GafferUI/Pointer.h>
#include <GafferUI/Style.h>
#include <GafferUI/ViewportGadget.h>
#include <GafferSceneUI/SceneView.h>
#if GAFFER_COMPATIBILITY_VERSION >= MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
#include <GafferSceneUI/ScriptNodeAlgo.h>
#else
#include <GafferSceneUI/ContextAlgo.h>
#endif

#include <IECore/VectorTypedData.h>
#include <IECoreScene/MeshAlgo.h>
#include <IECoreScene/MeshPrimitive.h>
#include <IECoreScene/MeshPrimitiveEvaluator.h>

//#include <IECoreGL/GL.h>
//#include <IECoreGL/Buffer.h>
#include <IECoreGL/CachedConverter.h>
#include <IECoreGL/MeshPrimitive.h>
//#include <IECoreGL/Shader.h>
#include <IECoreGL/ShaderLoader.h>
#if ( GAFFER_MILESTONE_VERSION == 0 && GAFFER_MAJOR_VERSION < 61 )
#include <IECoreGL/Selector.h>
#endif

#if GAFFER_COMPATIBILITY_VERSION < MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 3 )
#include <OpenEXR/ImathColor.h>
#else
#include <Imath/ImathColor.h>
#endif

#include <boost/bind/bind.hpp>
#include <boost/algorithm/string/predicate.hpp>
#include <boost/preprocessor/stringize.hpp>

#include <algorithm>
#include <cassert>
#include <limits>
#include <sstream>
#include <string>

namespace
{
    // text and size constants

    float const g_textSizeDefault = 9.0f;
    float const g_textSizeMin = 6.0f;
    float const g_textSizeInc = 0.5f;

    Imath::Color3f g_colourDefault( 1.f, 1.f, 1.f );
    
    // opacity and value constants

    float const g_opacityDefault = 0.5f;
    float const g_opacityMin = 0.0f;
    float const g_opacityMax = 1.0f;

    Imath::V3f const g_valueMinDefault( 0.f );
    Imath::V3f const g_valueMaxDefault( 1.f );

    // convert three component colour to four component colour with full opacity

    Imath::Color4f convertToColor4f
    (
        Imath::Color3f const& c
    )
    {
        return Imath::Color4f( c[ 0 ], c[ 1 ], c[ 2 ], 1.f );
    }

    // name of P primitive variable

    std::string const g_pName( "P" );

    // uniform block structure (std140 layout)

    struct UniformBlock
    {
        alignas( 16 ) Imath::M44f o2c;
        alignas( 16 ) Imath::V3f valueMin;
        alignas( 16 ) Imath::V3f valueRange;
        alignas( 4 ) float opacity;
    };

    GLuint const g_uniformBlockBindingIndex = 0;

#   define UNIFORM_BLOCK_GLSL_SOURCE \
        "layout( std140, row_major ) uniform UniformBlock\n" \
        "{\n" \
        "   mat4 o2c;\n" \
        "   vec3 valueMin;\n" \
        "   vec3 valueRange;\n" \
        "   float opacity;\n" \
        "} uniforms;\n"

#   define ATTRIB_GLSL_LOCATION_PS 0
#   define ATTRIB_GLSL_LOCATION_VSX 1
#   define ATTRIB_GLSL_LOCATION_VSY 2
#   define ATTRIB_GLSL_LOCATION_VSZ 3

#   define ATTRIB_GLSL_SOURCE \
        "layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_PS ) " ) in vec3 ps;\n" \
        "layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_VSX ) " ) in float vsx;\n" \
        "layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_VSY ) " ) in float vsy;\n" \
        "layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_VSZ ) " ) in float vsz;\n" \

#   define INTERFACE_BLOCK_GLSL_SOURCE( STORAGE, NAME ) \
        BOOST_PP_STRINGIZE( STORAGE ) " InterfaceBlock\n" \
        "{\n" \
        "   smooth vec3 value;\n" \
        "} " BOOST_PP_STRINGIZE( NAME ) ";\n"

    // opengl vertex shader code

    std::string const g_vertSource
    (
        "#version 330\n"

        UNIFORM_BLOCK_GLSL_SOURCE

        ATTRIB_GLSL_SOURCE

        INTERFACE_BLOCK_GLSL_SOURCE( out, outputs )

        "void main()\n"
        "{\n"
        "   outputs.value = clamp( ( vec3( vsx, vsy, vsz ) - uniforms.valueMin )\n"
        "       * uniforms.valueRange, 0.0, 1.0 );\n"
        "   gl_Position = vec4( ps, 1.0 ) * uniforms.o2c;\n"
        "}\n"
    );

    // opengl fragment shader code

    std::string const g_fragSource
    (
        "#version 330\n"

        UNIFORM_BLOCK_GLSL_SOURCE

        INTERFACE_BLOCK_GLSL_SOURCE( in, inputs )

        "layout( location = 0 ) out vec4 cs;\n"

        "void main()\n"
        "{\n"
        "   cs = vec4( inputs.value, uniforms.opacity );\n"
        "}\n"
    );

    // the gadget that does the actual opengl drawing of the shaded primitive

    struct Gadget
    : public GafferUI::Gadget
    {
        explicit
        Gadget
        (
            CSGafferUI::CsVisualiseValueTool const& tool,
            std::string const& name = "CsVisualiseValueGadget"
        )
        : GafferUI::Gadget( name )
        , m_tool( & tool )
        , m_shader()
        , m_uniformBuffer()
        {}

        void resetTool()
        {
            m_tool = nullptr;
        }

    protected:

        void
#       if ( GAFFER_MILESTONE_VERSION > 0 || GAFFER_MAJOR_VERSION >= 61 )
        renderLayer
#       else
        doRenderLayer
#       endif
        (
            GafferUI::Gadget::Layer layer,
            GafferUI::Style const* style
#           if ( GAFFER_MILESTONE_VERSION > 0 || GAFFER_MAJOR_VERSION >= 61 )
            , GafferUI::Gadget::RenderReason reason
#           endif
        )
        const override
        {
            if( ( layer != GafferUI::Gadget::Layer::MidFront ) ||
#               if ( GAFFER_MILESTONE_VERSION > 0 || GAFFER_MAJOR_VERSION >= 61 )
                ( GafferUI::Gadget::isSelectionRender( reason ) ) )
#               else
                ( IECoreGL::Selector::currentSelector() ) )
#               endif
            {
                return;
            }

            // check tool reference valid

            if( m_tool == nullptr )
            {
                return;
            }

            // get parent viewport gadget

            GafferUI::ViewportGadget const* const viewportGadget =
                ancestor< GafferUI::ViewportGadget >();
            if( viewportGadget == nullptr )
            {
                return;
            }

            // bootleg shader

            buildShader();

            if( ! m_shader )
            {
                return;
            }

            // get the cached converter from IECoreGL, this is used to convert primitive
            // variable data to opengl buffers which will be shared with the IECoreGL renderer

            IECoreGL::CachedConverter* const converter =
                IECoreGL::CachedConverter::defaultCachedConverter();

            // bootleg uniform buffer

            GLint uniformBinding;
            glGetIntegerv( GL_UNIFORM_BUFFER_BINDING, & uniformBinding );

            if( ! m_uniformBuffer )
            {
                GLuint buffer = 0u;
                glGenBuffers( 1, & buffer );
                glBindBuffer( GL_UNIFORM_BUFFER, buffer );
                glBufferData( GL_UNIFORM_BUFFER, sizeof( UniformBlock ), 0, GL_DYNAMIC_DRAW );
                m_uniformBuffer.reset( new IECoreGL::Buffer( buffer ) );
            }

            glBindBufferBase( GL_UNIFORM_BUFFER, g_uniformBlockBindingIndex, m_uniformBuffer->m_buffer );

            // get the name of the primitive variable to visualise

            std::string const& name = m_tool->namePlug()->getValue();

            // get min/max values and colours and opacity

            UniformBlock uniforms;
            Imath::V3f const valueMin = m_tool->valueMinPlug()->getValue();
            Imath::V3f const valueMax = m_tool->valueMaxPlug()->getValue();
            uniforms.opacity = m_tool->opacityPlug()->getValue();

            // compute value range reciprocal
            //
            // NOTE : when range is <= 0 set the reciprocal to 0 so that value becomes 0 (minimum)

            Imath::V3f valueRange = ( valueMax - valueMin );
            for( int i = 0; i < 3; ++i )
            {
                valueRange[ i ] = ( valueRange[ i ] > 0.f )
                    ? ( 1.f / valueRange[ i ] ) : 0.f;
            }

            // get the world to clip space matrix

            Imath::M44f v2c;
            glGetFloatv( GL_PROJECTION_MATRIX, v2c.getValue() );
            Imath::M44f const w2c = viewportGadget->getCameraTransform().gjInverse() * v2c;

            // set opengl polygon and blend state
            //
            // NOTE : use polygon offset to ensure that any discrepancies between the transform
            //        from object to clip space do not cause z-fighting. This is necessary as
            //        the shader uses an object to clip matrix which may give slighly different
            //        depth results to the transformation used in the IECoreGL renderer.

            GLint blendEqRgb, blendEqAlpha;
            glGetIntegerv( GL_BLEND_EQUATION_RGB, & blendEqRgb );
            glGetIntegerv( GL_BLEND_EQUATION_ALPHA, & blendEqAlpha );
            glBlendEquation( GL_FUNC_ADD );

            GLint blendSrcRgb, blendSrcAlpha, blendDstRgb, blendDstAlpha;
            glGetIntegerv( GL_BLEND_SRC_RGB, & blendSrcRgb );
            glGetIntegerv( GL_BLEND_SRC_ALPHA, & blendSrcAlpha );
            glGetIntegerv( GL_BLEND_DST_RGB, & blendDstRgb );
            glGetIntegerv( GL_BLEND_DST_ALPHA, & blendDstAlpha );
            glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );

            GLboolean const depthEnabled = glIsEnabled( GL_DEPTH_TEST );
            if( ! depthEnabled ) glEnable( GL_DEPTH_TEST );

            GLint depthFunc;
            glGetIntegerv( GL_DEPTH_FUNC, & depthFunc );
            glDepthFunc( GL_LEQUAL );

            GLboolean depthWriteEnabled;
            glGetBooleanv( GL_DEPTH_WRITEMASK, & depthWriteEnabled );
            if( depthWriteEnabled ) glDepthMask( GL_FALSE );

            GLboolean const blendEnabled = glIsEnabled( GL_BLEND );
            if( ! blendEnabled ) glEnable( GL_BLEND );

            GLint polygonMode;
            glGetIntegerv( GL_POLYGON_MODE, & polygonMode );
            glPolygonMode( GL_FRONT_AND_BACK, GL_FILL );

            GLboolean const cullFaceEnabled = glIsEnabled( GL_CULL_FACE );
            if( cullFaceEnabled ) glDisable( GL_CULL_FACE );

            GLboolean const polgonOffsetFillEnabled = glIsEnabled( GL_POLYGON_OFFSET_FILL );
            if( ! polgonOffsetFillEnabled ) glEnable( GL_POLYGON_OFFSET_FILL );

            GLfloat polygonOffsetFactor, polygonOffsetUnits;
            glGetFloatv( GL_POLYGON_OFFSET_FACTOR, & polygonOffsetFactor );
            glGetFloatv( GL_POLYGON_OFFSET_UNITS, & polygonOffsetUnits );
            glPolygonOffset( -1, -1 );

            // enable shader program

            GLint shaderProgram;
            glGetIntegerv( GL_CURRENT_PROGRAM, & shaderProgram );
            glUseProgram( m_shader->program() );

            // set opengl vertex attribute array state

            GLint arrayBinding;
            glGetIntegerv( GL_ARRAY_BUFFER_BINDING, & arrayBinding );

            glPushClientAttrib( GL_CLIENT_VERTEX_ARRAY_BIT );

            glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_PS, 0 );
            glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_PS );
            glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_VSX, 0 );
            glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_VSX );
            glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_VSY, 0 );
            glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_VSY );
            glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_VSZ, 0 );

            // loop through current selection

            for( std::vector< CSGafferUI::CsVisualiseValueTool::Selection >::const_iterator
                    it    = m_tool->selection().begin(),
                    itEnd = m_tool->selection().end(); it != itEnd; ++it )
            {
                GafferScene::ScenePlug::PathScope scope( &( ( *it ).context() ), &( ( *it ).path() ) );

                // check path exists

                if( !( ( *it ).scene().existsPlug()->getValue() ) )
                {
                    continue;
                }

                // extract mesh primitive

                IECoreScene::ConstMeshPrimitivePtr const mesh =
                    IECore::runTimeCast< IECoreScene::MeshPrimitive const >(
                        ( *it ).scene().objectPlug()->getValue() );
        
                if( ! mesh )
                {
                    continue;
                }

                // retrieve cached IECoreGL mesh primitive

                IECoreGL::ConstPrimitivePtr const meshGL =
                    IECore::runTimeCast< IECoreGL::MeshPrimitive const >(
                        converter->convert( mesh.get() ) );

                if( ! meshGL )
                {
                    continue;
                }

                // find "P" vertex attribute

                IECoreGL::Primitive::AttributeMap::const_iterator const pit =
                    meshGL->m_vertexAttributes.find( g_pName );
                if( pit == meshGL->m_vertexAttributes.end() )
                {
                    continue;
                }

                IECore::ConstV3fVectorDataPtr const pData =
                    IECore::runTimeCast< IECore::V3fVectorData const >( ( *pit ).second );
                if( ! pData )
                {
                    continue;
                }

                // find named vertex attribute (FloatVectorData, V2fVectorData or V3fVectorData)
                //
                // NOTE : conversion to IECoreGL mesh may generate vertex attributes (eg. "N")
                //        so check named primitive variable exists on IECore mesh primitive.

                IECoreGL::Primitive::AttributeMap::const_iterator const vit =
                    meshGL->m_vertexAttributes.find( name );
                if( ( vit == meshGL->m_vertexAttributes.end() ) || !( ( *vit ).second ) ||
                    ( mesh->variables.find( name ) == mesh->variables.end() ) )
                {
                    continue;
                }

                IECore::ConstDataPtr const vData = ( *vit ).second;
                GLsizei stride = 0;
                GLenum type = GL_FLOAT;
                bool offset = false;
                bool enableVSZ = false;
                switch( vData->typeId() )
                {
                    case IECore::IntVectorDataTypeId:
                        type = GL_INT;
                    case IECore::FloatVectorDataTypeId:
                        enableVSZ = true;
                        uniforms.valueMin = Imath::V3f( valueMin.x );
                        uniforms.valueRange = Imath::V3f( valueRange.x );
                        break;
                    case IECore::V2fVectorDataTypeId:
                        stride = 2;
                        offset = true;
                        uniforms.valueMin = Imath::V3f( valueMin.x, valueMin.y, 0.f );
                        uniforms.valueRange = Imath::V3f( valueRange.x, valueRange.y, 0.f );
                        break;
                    case IECore::V3fVectorDataTypeId:
                        stride = 3;
                        offset = true;
                        enableVSZ = true;
                        uniforms.valueMin = valueMin;
                        uniforms.valueRange = valueRange;
                        break;
                    default:
                        continue;
                }

                // retrieve cached opengl buffer data

                IECoreGL::ConstBufferPtr const pBuffer =
                    IECore::runTimeCast< IECoreGL::Buffer const >( converter->convert( pData.get() ) );
                IECoreGL::ConstBufferPtr const vBuffer =
                    IECore::runTimeCast< IECoreGL::Buffer const >( converter->convert( vData.get() ) );

                // get the object to world transform

                Imath::M44f o2w;
                GafferScene::ScenePlug::ScenePath path( ( *it ).path() );
                while( ! path.empty() )
                {
                    scope.setPath( & path );
                    o2w = o2w * ( *it ).scene().transformPlug()->getValue();
                    path.pop_back();
                }

                // compute object to clip matrix

                uniforms.o2c = o2w * w2c;

                // upload opengl uniform block data

                glBufferData( GL_UNIFORM_BUFFER, sizeof( UniformBlock ), & uniforms, GL_DYNAMIC_DRAW );

                // draw primitive

                glBindBuffer( GL_ARRAY_BUFFER, pBuffer->m_buffer );
                glVertexAttribPointer( ATTRIB_GLSL_LOCATION_PS, 3, GL_FLOAT, GL_FALSE,
                    0, ( void const* )( 0 ) );
                glBindBuffer( GL_ARRAY_BUFFER, vBuffer->m_buffer );
                glVertexAttribPointer( ATTRIB_GLSL_LOCATION_VSX, 1, type, GL_FALSE,
                    stride * sizeof( GLfloat ), ( void const* )( 0 ) );
                glVertexAttribPointer( ATTRIB_GLSL_LOCATION_VSY, 1, type, GL_FALSE,
                    stride * sizeof( GLfloat ), ( void const* )( ( offset ? 1 : 0 ) * sizeof( GLfloat ) ) );
                if( enableVSZ )
                {
                    glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_VSZ );
                    glVertexAttribPointer( ATTRIB_GLSL_LOCATION_VSZ, 1, type, GL_FALSE,
                        stride * sizeof( GLfloat ), ( void const* )( ( offset ? 2 : 0 ) * sizeof( GLfloat ) ) );
                }
                else
                {
                    glDisableVertexAttribArray( ATTRIB_GLSL_LOCATION_VSZ );
                    glVertexAttrib1f( ATTRIB_GLSL_LOCATION_VSZ, 0.f );
                }

                meshGL->renderInstances( 1 );
            }

            // restore opengl state

            glPopClientAttrib();
            glBindBuffer( GL_ARRAY_BUFFER, arrayBinding );
            glBindBuffer( GL_UNIFORM_BUFFER, uniformBinding );

            glDepthFunc( depthFunc );
            glBlendEquationSeparate( blendEqRgb, blendEqAlpha );
            glBlendFuncSeparate( blendSrcRgb, blendDstRgb, blendSrcAlpha, blendDstAlpha );
            glPolygonMode( GL_FRONT_AND_BACK, polygonMode );
            if( cullFaceEnabled ) glEnable( GL_CULL_FACE );
            if( ! polgonOffsetFillEnabled ) glDisable( GL_POLYGON_OFFSET_FILL );
            glPolygonOffset( polygonOffsetFactor, polygonOffsetUnits );

            if( ! blendEnabled ) glDisable( GL_BLEND );
            if( ! depthEnabled ) glDisable( GL_DEPTH_TEST );
            if( depthWriteEnabled ) glDepthMask( GL_TRUE );
            glUseProgram( shaderProgram );

            // display value at cursor as text

            IECore::Data const* const value = m_tool->cursorValue();
            if( value )
            {
                std::ostringstream oss;
                switch( value->typeId() )
                {
                    case IECore::IntDataTypeId:
                        oss << ( IECore::assertedStaticCast< IECore::IntData const >( value )->readable() );
                        break;
                    case IECore::FloatDataTypeId:
                        oss << ( IECore::assertedStaticCast< IECore::FloatData const >( value )->readable() );
                        break;
                    case IECore::V2fDataTypeId:
                        oss << ( IECore::assertedStaticCast< IECore::V2fData const >( value )->readable() );
                        break;
                    case IECore::V3fDataTypeId:
                        oss << ( IECore::assertedStaticCast< IECore::V3fData const >( value )->readable() );
                        break;
                    default:
                        break;
                }

                std::string const text = oss.str();
                if( ! text.empty() )
                {
                    // draw in raster space
                    //
                    // NOTE : It seems that Gaffer defines the origin of raster space as the top left corner
                    //        of the viewport, however the style text drawing functions assume that y increases
                    //        "up" the screen rather than "down", so invert y to ensure text is not upside down.

                    GafferUI::ViewportGadget::RasterScope raster( viewportGadget );
                    float const size = m_tool->sizePlug()->getValue();
                    Imath::V3f const scale( size, -size, 1.f );
                    Imath::Color4f const colour = convertToColor4f( m_tool->colourPlug()->getValue() );
                    Imath::V2f const& rp = m_tool->cursorPos();

                    glPushMatrix();
                    glTranslatef( rp.x, rp.y, 0.f );
                    glScalef( scale.x, scale.y, scale.z );
                    style->renderText( GafferUI::Style::LabelText, text, GafferUI::Style::NormalState, & colour );
                    glPopMatrix();
                }
            }
        }

#       if ( GAFFER_MILESTONE_VERSION > 0 || GAFFER_MAJOR_VERSION >= 61 )
        Imath::Box3f renderBound() const override
        {
            // NOTE : for now just return an infinite box

            Imath::Box3f b;
            b.makeInfinite();
            return b;
        }
#       endif

#       if ( GAFFER_MILESTONE_VERSION > 0 || GAFFER_MAJOR_VERSION >= 61 )
        unsigned layerMask() const override
        {
            return ( m_tool )
                ? static_cast< unsigned >( GafferUI::Gadget::Layer::MidFront )
                : static_cast< unsigned >( 0 );
        }
#       else
        bool hasLayer( GafferUI::Gadget::Layer layer )
        {
            return ( m_tool &&
                ( layer == GafferUI::Gadget::Layer::MidFront ) );
        }
#       endif

    private:

        void buildShader() const
        {
            if( ! m_shader )
            {
                m_shader = IECoreGL::ShaderLoader::defaultShaderLoader()->create(
                    g_vertSource, std::string(), g_fragSource );
                if( m_shader )
                {
                    GLuint const program = m_shader->program();
                    GLuint const blockIndex = glGetUniformBlockIndex( program, "UniformBlock" );
                    if( blockIndex != GL_INVALID_INDEX )
                    {
                        glUniformBlockBinding( program, blockIndex, g_uniformBlockBindingIndex );
                    }
                }
            }
        }

        CSGafferUI::CsVisualiseValueTool const* m_tool;
        mutable IECoreGL::ConstShaderPtr m_shader;
        mutable IECoreGL::ConstBufferPtr m_uniformBuffer;
    };

    // cache for mesh evaluators

    struct EvaluationData
    {
        IECoreScene::ConstMeshPrimitivePtr triMesh;
        IECoreScene::ConstMeshPrimitiveEvaluatorPtr evaluator;
    };

    IECore::LRUCache<
        IECoreScene::ConstMeshPrimitivePtr,
        EvaluationData > g_evaluatorCache( []
        (
            IECoreScene::ConstMeshPrimitivePtr const mesh,
            size_t& cost
        ) -> EvaluationData
        {
            cost = 1;
            EvaluationData data;
            data.triMesh = mesh->copy();
            data.triMesh = IECoreScene::MeshAlgo::triangulate( data.triMesh.get() );
            data.evaluator = new IECoreScene::MeshPrimitiveEvaluator( data.triMesh );
            return data;
        }, 10 );

} // namespace

namespace CSGafferUI
{
    GAFFER_NODE_DEFINE_TYPE( CsVisualiseValueTool )

    GafferUI::Tool::ToolDescription< CsVisualiseValueTool, GafferSceneUI::SceneView > CsVisualiseValueTool::m_toolDescription;

    size_t CsVisualiseValueTool::m_firstPlugIndex = 0;

    CsVisualiseValueTool::CsVisualiseValueTool
    (
        GafferSceneUI::SceneView* const view,
        std::string const& name
    )
    : GafferSceneUI::SelectionTool( view, name )
#   if GAFFER_COMPATIBILITY_VERSION < MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
    , m_contextChangedConnection()
#   endif
    , m_preRenderConnection()
    , m_buttonPressConnection()
    , m_dragBeginConnection()
    , m_gadget( new Gadget( *this ) )
    , m_selection()
    , m_cursorPos( -1, -1 )
    , m_cursorPosValid( false )
    , m_cursorValue()
    , m_gadgetDirty( true )
    , m_selectionDirty( true )
    , m_priorityPathsDirty( true )
    , m_acceptedButtonPress( false )
    , m_initiatedDrag( false )
    {
        // add gadget to view and hide

        view->viewportGadget()->addChild( m_gadget );
        m_gadget->setVisible( false );

        // store offset of first plug

        storeIndexOfNextChild( m_firstPlugIndex );

        // add child plugs

        addChild( new Gaffer::StringPlug( "name", Gaffer::Plug::In, "uv" ) );
        addChild( new Gaffer::FloatPlug( "opacity", Gaffer::Plug::In, g_opacityDefault, g_opacityMin, g_opacityMax ) );
        addChild( new Gaffer::V3fPlug( "valueMin", Gaffer::Plug::In, g_valueMinDefault ) );
        addChild( new Gaffer::V3fPlug( "valueMax", Gaffer::Plug::In, g_valueMaxDefault ) );
        addChild( new Gaffer::FloatPlug( "size", Gaffer::Plug::In, g_textSizeDefault, g_textSizeMin ) );
        addChild( new Gaffer::Color3fPlug( "colour", Gaffer::Plug::In, g_colourDefault ) );
        addChild( new GafferScene::ScenePlug( "__scene", Gaffer::Plug::In ) );

        // connect out internal scene plug to the parent view's scene plug

        internalScenePlug()->setInput( view->inPlug< GafferScene::ScenePlug >() );

        // connect signal handlers
        //
        // NOTE : connecting to the viewport gadget means we will get called for all events
        //        which makes sense for key events, however we do not want to display value
        //        text when the mouse is over another gadget, (eg. Transform Tool handle)
        //        so instead connect to scene gadget signal.
        // NOTE : There are other handlers that will attempt to consume button and drag
        //        events so connect handlers at the front of button/drag signal handler queues. 

        view->viewportGadget()->keyPressSignal().connect(
            boost::bind( & CsVisualiseValueTool::keyPress, this, boost::placeholders::_2 ) );

        // NOTE : drag end and button release handlers remain whilst tool inactive in case tool
        //        is made inactive after button pressed or drag initiated in which case these
        //        handlers still need to tidy up state.

        sceneGadget()->buttonReleaseSignal().
#           if ( GAFFER_MILESTONE_VERSION > 0 || GAFFER_MAJOR_VERSION >= 62 )
            connectFront
#           else
            connect
#           endif
            ( boost::bind( & CsVisualiseValueTool::buttonRelease, this, boost::placeholders::_2 )
#           if ( GAFFER_MILESTONE_VERSION == 0 && GAFFER_MAJOR_VERSION < 62 )
            , boost::signals::at_front
#           endif
            );

        sceneGadget()->dragEndSignal().
#           if ( GAFFER_MILESTONE_VERSION > 0 || GAFFER_MAJOR_VERSION >= 62 )
            connectFront
#           else
            connect
#           endif
            ( boost::bind( & CsVisualiseValueTool::dragEnd, this, boost::placeholders::_2 )
#           if ( GAFFER_MILESTONE_VERSION == 0 && GAFFER_MAJOR_VERSION < 62 )
            , boost::signals::at_front
#           endif
            );

        // NOTE : mouse tracking handlers remain connected whilst tool inactive as they track the cursor
        //        line and whether its valid or not. This prevents the value display from "sticking" to
        //        edge of viewport when cursor leaves viewport's screen space. It also means that we do
        //        not have to work out the cursor line and whether its valid when tool is made active.

        sceneGadget()->enterSignal().connect(
            boost::bind( & CsVisualiseValueTool::enter, this, boost::placeholders::_2 ) );
        sceneGadget()->leaveSignal().connect(
            boost::bind( & CsVisualiseValueTool::leave, this, boost::placeholders::_2 ) );
        sceneGadget()->mouseMoveSignal().connect(
            boost::bind( & CsVisualiseValueTool::mouseMove, this, boost::placeholders::_2 ) );

        plugDirtiedSignal().connect(
            boost::bind( & CsVisualiseValueTool::plugDirtied, this, boost::placeholders::_1 ) );
        plugSetSignal().connect(
            boost::bind( & CsVisualiseValueTool::plugSet, this, boost::placeholders::_1 ) );

#       if GAFFER_COMPATIBILITY_VERSION >= MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
        view->contextChangedSignal().connect(
            boost::bind( & CsVisualiseValueTool::contextChanged, this ) );
        GafferSceneUI::ScriptNodeAlgo::selectedPathsChangedSignal( view->scriptNode() ).connect(
                boost::bind( &CsVisualiseValueTool::selectedPathsChanged, this ) );
#       else
        connectToViewContext();
        view->contextChangedSignal().connect(
            boost::bind( & CsVisualiseValueTool::connectToViewContext, this ) );
#       endif

        Gaffer::Metadata::plugValueChangedSignal().connect(
            boost::bind( & CsVisualiseValueTool::metadataChanged, this, boost::placeholders::_3 ) );
        Gaffer::Metadata::nodeValueChangedSignal().connect(
            boost::bind( & CsVisualiseValueTool::metadataChanged, this, boost::placeholders::_2 ) );
    }

    CsVisualiseValueTool::~CsVisualiseValueTool()
    {
        // NOTE : ensure that the gadget's reference to the tool is reset

        static_cast< Gadget* >( m_gadget.get() )->resetTool();
    }

    Gaffer::StringPlug* CsVisualiseValueTool::namePlug()
    {
        return const_cast< Gaffer::StringPlug* >(
            static_cast< CsVisualiseValueTool const* >( this )->namePlug() );
    }

    Gaffer::StringPlug const* CsVisualiseValueTool::namePlug() const
    {
        return getChild< Gaffer::StringPlug >( m_firstPlugIndex + 0 );
    }

    Gaffer::FloatPlug* CsVisualiseValueTool::opacityPlug()
    {
        return const_cast< Gaffer::FloatPlug* >(
            static_cast< CsVisualiseValueTool const* >( this )->opacityPlug() );
    }

    Gaffer::FloatPlug const* CsVisualiseValueTool::opacityPlug() const
    {
        return getChild< Gaffer::FloatPlug >( m_firstPlugIndex + 1 );
    }

    Gaffer::V3fPlug* CsVisualiseValueTool::valueMinPlug()
    {
        return const_cast< Gaffer::V3fPlug* >(
            static_cast< CsVisualiseValueTool const* >( this )->valueMinPlug() );
    }

    Gaffer::V3fPlug const* CsVisualiseValueTool::valueMinPlug() const
    {
        return getChild< Gaffer::V3fPlug >( m_firstPlugIndex + 2 );
    }

    Gaffer::V3fPlug* CsVisualiseValueTool::valueMaxPlug()
    {
        return const_cast< Gaffer::V3fPlug* >(
            static_cast< CsVisualiseValueTool const* >( this )->valueMaxPlug() );
    }

    Gaffer::V3fPlug const* CsVisualiseValueTool::valueMaxPlug() const
    {
        return getChild< Gaffer::V3fPlug >( m_firstPlugIndex + 3 );
    }

    Gaffer::FloatPlug* CsVisualiseValueTool::sizePlug()
    {
        return const_cast< Gaffer::FloatPlug* >(
            static_cast< CsVisualiseValueTool const* >( this )->sizePlug() );
    }

    Gaffer::FloatPlug const* CsVisualiseValueTool::sizePlug() const
    {
        return getChild< Gaffer::FloatPlug >( m_firstPlugIndex + 4 );
    }

    Gaffer::Color3fPlug* CsVisualiseValueTool::colourPlug()
    {
        return const_cast< Gaffer::Color3fPlug* >(
            static_cast< CsVisualiseValueTool const* >( this )->colourPlug() );
    }

    Gaffer::Color3fPlug const* CsVisualiseValueTool::colourPlug() const
    {
        return getChild< Gaffer::Color3fPlug >( m_firstPlugIndex + 5 );
    }

    GafferScene::ScenePlug* CsVisualiseValueTool::internalScenePlug()
    {
        return const_cast< GafferScene::ScenePlug* >(
            static_cast< CsVisualiseValueTool const* >( this )->internalScenePlug() );
    }

    GafferScene::ScenePlug const* CsVisualiseValueTool::internalScenePlug() const
    {
        return getChild< GafferScene::ScenePlug >( m_firstPlugIndex + 6 );
    }

    std::vector< CsVisualiseValueTool::Selection > const& CsVisualiseValueTool::selection() const
    {
        return m_selection;
    }

    Imath::V2f CsVisualiseValueTool::cursorPos() const
    {
        return m_cursorPos;
    }

    IECore::Data const* CsVisualiseValueTool::cursorValue() const
    {
        return m_cursorValue.get();
    }

    void CsVisualiseValueTool::connectOnActive()
    {
        // NOTE : There are other handlers that will attempt to consume button and drag events
        //        so connect handlers at the front of button/drag signal handler queues. 

        m_buttonPressConnection = sceneGadget()->buttonPressSignal().
#           if ( GAFFER_MILESTONE_VERSION > 0 || GAFFER_MAJOR_VERSION >= 62 )
            connectFront
#           else
            connect
#           endif
            ( boost::bind( & CsVisualiseValueTool::buttonPress, this, boost::placeholders::_2 )
#           if ( GAFFER_MILESTONE_VERSION == 0 && GAFFER_MAJOR_VERSION < 62 )
            , boost::signals::at_front
#           endif
            );
        m_dragBeginConnection = sceneGadget()->dragBeginSignal().
#           if ( GAFFER_MILESTONE_VERSION > 0 || GAFFER_MAJOR_VERSION >= 62 )
            connectFront
#           else
            connect
#           endif
            ( boost::bind( & CsVisualiseValueTool::dragBegin, this, boost::placeholders::_2 )
#           if ( GAFFER_MILESTONE_VERSION == 0 && GAFFER_MAJOR_VERSION < 62 )
            , boost::signals::at_front
#           endif
            );

        m_preRenderConnection = view()->viewportGadget()->preRenderSignal().connect(
            boost::bind( & CsVisualiseValueTool::preRender, this ) );

        // NOTE : redraw necessary to ensure value display updated.

        view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
    }

    void CsVisualiseValueTool::disconnectOnInactive()
    {
        m_preRenderConnection.disconnect();
        m_buttonPressConnection.disconnect();
        m_dragBeginConnection.disconnect();
    }

#   if GAFFER_COMPATIBILITY_VERSION >= MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
    void CsVisualiseValueTool::contextChanged()
    {
        // Context changes can change the scene, which in turn
        // dirties our selection.
        selectedPathsChanged();
    }

    void CsVisualiseValueTool::selectedPathsChanged()
    {
        m_selectionDirty = true;
        m_gadgetDirty = true;
        m_priorityPathsDirty = true;
    }
#   else
    void CsVisualiseValueTool::connectToViewContext()
    {
        m_contextChangedConnection = view()->getContext()->changedSignal().connect(
            boost::bind( & CsVisualiseValueTool::contextChanged, this, boost::placeholders::_2 ) );
    }

    void CsVisualiseValueTool::contextChanged
    (
        IECore::InternedString const& name
    )
    {
        if( GafferSceneUI::ContextAlgo::affectsSelectedPaths( name ) ||
            GafferSceneUI::ContextAlgo::affectsLastSelectedPath( name ) ||
            ! boost::starts_with( name.string(), "ui:" ) )
        {
            m_selectionDirty = true;
            m_gadgetDirty = true;
            m_priorityPathsDirty = true;
        }
    }
#   endif

    bool CsVisualiseValueTool::mouseMove
    (
        GafferUI::ButtonEvent const& event
    )
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

    void CsVisualiseValueTool::enter
    (
        GafferUI::ButtonEvent const& event
    )
    {
        updateCursorPos( event );
        m_cursorPosValid = true;
        
        // NOTE : only schedule redraw if tool active
        
        if( activePlug()->getValue() )
        {
            view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
        }
    }

    void CsVisualiseValueTool::leave
    (
        GafferUI::ButtonEvent const& event
    )
    {
        updateCursorPos( event );
        m_cursorPosValid = false;

        // NOTE : only schedule redraw if tool active
        
        if( activePlug()->getValue() )
        {
            view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
        }
    }

    bool CsVisualiseValueTool::keyPress
    (
        GafferUI::KeyEvent const& event
    )
    {
        if( ! activePlug()->getValue() )
        {
            return false;
        }

        // allow user to scale text with +/- keys

        if( event.key == "Plus" || event.key == "Equal" )
        {
            sizePlug()->setValue( sizePlug()->getValue() + g_textSizeInc );
        }
        else
        if( event.key == "Minus" || event.key == "Underscore" )
        {
            sizePlug()->setValue( std::max( sizePlug()->getValue() - g_textSizeInc, g_textSizeMin ) );
        }

        return false;
    }

    bool CsVisualiseValueTool::buttonPress
    (
        GafferUI::ButtonEvent const& event
    )
    {
        m_acceptedButtonPress = false;
        m_initiatedDrag = false;

        if( ( event.button & GafferUI::ButtonEvent::Left ) )
        {
            updateCursorValue();
            if( m_cursorValue )
            {
                m_acceptedButtonPress = true;
                return true;
            }
        }

        return false;
    }

    bool CsVisualiseValueTool::buttonRelease
    (
        GafferUI::ButtonEvent const& event
    )
    {
        m_acceptedButtonPress = false;
        m_initiatedDrag = false;

        return false;
    }

    IECore::RunTimeTypedPtr
    CsVisualiseValueTool::dragBegin
    (
        GafferUI::DragDropEvent const& event
    )
    {
        m_initiatedDrag = false;

        if( ! m_acceptedButtonPress )
        {
            return IECore::RunTimeTypedPtr();
        }

        m_acceptedButtonPress = false;

        if( m_cursorValue )
        {
            // NOTE : There is a possibility that the tool has become inactive since the button
            //        press event that triggered the drag was accepted, the cutoff point is the
            //        button press event, so any change to the active state after that does not
            //        affect an ongoing drag operation. We therefore always request a redraw
            //        here so that the displayed value is cleared.

            m_initiatedDrag = true;
            view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
            GafferUI::Pointer::setCurrent( "values" );
        }

        return m_cursorValue;
    }

    bool CsVisualiseValueTool::dragEnd
    (
        GafferUI::DragDropEvent const& event
    )
    {
        if( ! m_initiatedDrag )
        {
            return false;
        }

        m_initiatedDrag = false;
        GafferUI::Pointer::setCurrent( "" );
        return true;
    }

    void CsVisualiseValueTool::plugDirtied
    (
        Gaffer::Plug const* const plug
    )
    {
        if( ( plug == activePlug() ) ||
            ( plug == internalScenePlug()->objectPlug() ) ||
            ( plug == internalScenePlug()->transformPlug() ) )
        {
            m_selectionDirty = true;
            m_gadgetDirty = true;
            m_priorityPathsDirty = true;
        }
        else
        if( ( plug == namePlug() ) ||
            ( plug == opacityPlug() ) ||
            ( plug == valueMinPlug() ) ||
            ( plug == valueMaxPlug() ) ||
            ( plug == sizePlug() ) ||
            ( plug == colourPlug() ) )
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

                sceneGadget()->setPriorityPaths( IECore::PathMatcher() );
            }
        }
    }

    void CsVisualiseValueTool::plugSet( Gaffer::Plug* const plug )
    {
        // ensure that the min value does not exceed the max and vice-versa

        if( plug == valueMinPlug() )
        {
            Imath::V3f const valueMin = valueMinPlug()->getValue();
            Imath::V3f       valueMax = valueMaxPlug()->getValue();

            for( int i = 0; i < 3; ++i )
            {
                valueMax[ i ] = std::max( valueMin[ i ], valueMax[ i ] );
            }

            valueMaxPlug()->setValue( valueMax );
        }
        else
        if( plug == valueMaxPlug() )
        {
            Imath::V3f       valueMin = valueMinPlug()->getValue();
            Imath::V3f const valueMax = valueMaxPlug()->getValue();

            for( int i = 0; i < 3; ++i )
            {
                valueMin[ i ] = std::min( valueMin[ i ], valueMax[ i ] );
            }

            valueMinPlug()->setValue( valueMin );
        }
    }

    void CsVisualiseValueTool::metadataChanged
    (
        IECore::InternedString const& key
    )
    {
        if( ! Gaffer::MetadataAlgo::readOnlyAffectedByChange( key ) )
        {
            return;
        }

        if( ! m_selectionDirty )
        {
            m_selectionDirty = true;
        }

        if( ! m_gadgetDirty )
        {
            m_gadgetDirty = true;
            view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
        }
    }

    void CsVisualiseValueTool::updateSelection() const
    {
        if( ! m_selectionDirty )
        {
            return;
        }

        m_selection.clear();
        m_selectionDirty = false;

        if( ! activePlug()->getValue() )
        {
            return;
        }

        GafferScene::ScenePlug const* scene =
            internalScenePlug()->getInput< GafferScene::ScenePlug >();

        if( !( scene ) ||
            !( scene = scene->getInput< GafferScene::ScenePlug >() ) )
        {
            return;
        }

#       if GAFFER_COMPATIBILITY_VERSION >= MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
        IECore::PathMatcher const selectedPaths =
            GafferSceneUI::ScriptNodeAlgo::getSelectedPaths( view()->scriptNode() );
#       else
        IECore::PathMatcher const selectedPaths =
            GafferSceneUI::ContextAlgo::getSelectedPaths( view()->getContext() );
#       endif

        if( selectedPaths.isEmpty() )
        {
            return;
        }

        for( IECore::PathMatcher::Iterator it    = selectedPaths.begin(),
                                           itEnd = selectedPaths.end(); it != itEnd; ++it )
        {
#           if GAFFER_COMPATIBILITY_VERSION >= MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
            m_selection.emplace_back( *( scene ), *it, *( view()->context() ) );
#           else
            m_selection.emplace_back( *( scene ), *it, *( view()->getContext() ) );
#           endif

        }
    }

    void CsVisualiseValueTool::preRender()
    {
        updateSelection();

        if( m_priorityPathsDirty )
        {
#           if GAFFER_COMPATIBILITY_VERSION >= MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
            sceneGadget()->setPriorityPaths( ( m_selection.empty() )
                    ? IECore::PathMatcher()
                    : GafferSceneUI::ScriptNodeAlgo::getSelectedPaths( view()->scriptNode() ) );
#           else
            sceneGadget()->setPriorityPaths( ( m_selection.empty() )
                    ? IECore::PathMatcher()
                    : GafferSceneUI::ContextAlgo::getSelectedPaths( view()->getContext() ) );
#           endif

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

        updateCursorValue();
    }

    void CsVisualiseValueTool::updateCursorPos
    (
        GafferUI::ButtonEvent const& event
    )
    {
        // update cursor raster position
        //
        // NOTE : the cursor position is stored in raster space so it is free of camera
        //        transformations so we do not need to track camera changes.

        assert( view() );
        assert( view()->viewportGadget() );

        m_cursorPos = view()->viewportGadget()->gadgetToRasterSpace( event.line.p1, sceneGadget() );
    }

    void CsVisualiseValueTool::updateCursorValue()
    {
        IECore::DataPtr cursorValue = m_cursorValue;
        m_cursorValue.reset();

        // NOTE : during a drag do not update the cursor value
        
        if( m_initiatedDrag || ! m_cursorPosValid )
        {
            return;
        }

        // get scene gadget and viewport gadgets

        GafferSceneUI::SceneGadget* const sg = sceneGadget();
        if( ! sg || ! view() || !( view()->viewportGadget() ) )
        {
            return;
        }

        // clear any existing selection mask

        IECore::StringVectorData const* const selectionMask = sg->getSelectionMask();
        sg->setSelectionMask( nullptr );

        // get the current object at cursor

        GafferScene::ScenePlug::ScenePath path;

        try
        {
            if( ! sg->objectAt( view()->viewportGadget()->rasterToGadgetSpace( m_cursorPos, sg ), path ) )
            {
                return;
            }
        }
        catch( IECore::Exception const& e )
        {
            // NOTE : objectAt seems to write to the OpenGL color buffer so if there was an
            //        error the OpenGL color buffer will contain the remnants of the failed
            //        object id pass. If we are being called from preRender() the color buffer
            //        would normally be cleared after the preRender callback has finished so
            //        catch the exception and return. If we are being called from button press
            //        we don't want the exception to propagate so again catch and return. In
            //        both cases the error should happen again during the next render pass.

            return;
        }

        // check current object is included in selection

        std::vector< Selection >::const_iterator const sit =
            std::find_if( m_selection.begin(), m_selection.end(),
                [ & path ]( Selection const& item ) -> bool
                {
                    return item.path() == path;
                } );
        if( sit == m_selection.end() )
        {
            return;
        }

        // check scene location exists

        Selection const& item = ( *sit );
        GafferScene::ScenePlug::PathScope scope( &( item.context() ), & path );
        if( !( item.scene().existsPlug()->getValue() ) )
        {
            return;
        }

        // extract mesh primitive object

        IECoreScene::ConstMeshPrimitivePtr const mesh =
            IECore::runTimeCast< IECoreScene::MeshPrimitive const >(
                item.scene().objectPlug()->getValue() );
        if( ! mesh )
        {
            return;
        }

        // check mesh has named primitive variable

        std::string const& name = namePlug()->getValue();
        IECoreScene::PrimitiveVariableMap::const_iterator const vit = mesh->variables.find( name );
        if( vit == mesh->variables.end() || !( ( *vit ).second.data ) )
        {
            return;
        }

        // check type of data

        switch( ( *vit ).second.data->typeId() )
        {
            case IECore::IntVectorDataTypeId:
            case IECore::FloatVectorDataTypeId:
            case IECore::V2fVectorDataTypeId:
            case IECore::V3fVectorDataTypeId:
                break;
            default:
                return;
        }

        // create a mesh primitive evaluator
        //
        // NOTE : In order to create an evaluator we need a triangulated mesh
        //        this processing is expensive so we cache the created evaluator in an LRU cache

        EvaluationData const evalData = g_evaluatorCache.get( mesh );
        IECoreScene::PrimitiveEvaluator::ResultPtr const result = evalData.evaluator->createResult();

        // intersect line from cursor with mesh in object space using evaluator

        IECore::LineSegment3f const line =
            view()->viewportGadget()->rasterToWorldSpace( cursorPos() ) *
                item.scene().fullTransform( path ).gjInverse();
        if( ! evalData.evaluator->intersectionPoint( line.p0, line.direction(), result.get() ) )
        {
            return;
        }

        // update value from intersection result

        switch( ( *vit ).second.data->typeId() )
        {
            case IECore::IntVectorDataTypeId:
            {
                IECore::IntDataPtr data =
                    IECore::runTimeCast< IECore::IntData >( cursorValue );
                if( ! data ) data.reset( new IECore::IntData() );
                data->writable() = result->intPrimVar( evalData.triMesh->variables.at( name ) );
                cursorValue = data;
                break;
            }
            case IECore::FloatVectorDataTypeId:
            {
                IECore::FloatDataPtr data =
                    IECore::runTimeCast< IECore::FloatData >( cursorValue );
                if( ! data ) data.reset( new IECore::FloatData() );
                data->writable() = result->floatPrimVar( evalData.triMesh->variables.at( name ) );
                cursorValue = data;
                break;
            }
            case IECore::V2fVectorDataTypeId:
            {
                IECore::V2fDataPtr data =
                    IECore::runTimeCast< IECore::V2fData >( cursorValue );
                if( ! data ) data.reset( new IECore::V2fData() );
                data->writable() = result->vec2PrimVar( evalData.triMesh->variables.at( name ) );
                cursorValue = data;
                break;
            }
            case IECore::V3fVectorDataTypeId:
            {
                IECore::V3fDataPtr data =
                    IECore::runTimeCast< IECore::V3fData >( cursorValue );
                if( ! data ) data.reset( new IECore::V3fData() );
                data->writable() = result->vectorPrimVar( evalData.triMesh->variables.at( name ) );
                cursorValue = data;
                break;
            }
            default:
                return;
        }

        m_cursorValue = cursorValue;

        // restore selection mask

        sg->setSelectionMask( selectionMask );
    }

    GafferSceneUI::SceneGadget* CsVisualiseValueTool::sceneGadget()
    {
        return const_cast< GafferSceneUI::SceneGadget* >(
            static_cast< CsVisualiseValueTool const* >( this )->sceneGadget() );
    }

    GafferSceneUI::SceneGadget const* CsVisualiseValueTool::sceneGadget() const
    {
        return IECore::runTimeCast< GafferSceneUI::SceneGadget const >(
            view()->viewportGadget()->getPrimaryChild() );
    }

    CsVisualiseValueTool::Selection::Selection
    (
        GafferScene::ScenePlug const& scene,
        GafferScene::ScenePlug::ScenePath const& path,
        Gaffer::Context const& context
    )
    : m_scene( & scene )
    , m_path( path )
    , m_context( & context )
    {}

    GafferScene::ScenePlug const& CsVisualiseValueTool::Selection::scene() const
    {
        return *( m_scene );
    }

    GafferScene::ScenePlug::ScenePath const& CsVisualiseValueTool::Selection::path() const
    {
        return m_path;
    }

    Gaffer::Context const& CsVisualiseValueTool::Selection::context() const
    {
        return *( m_context );
    }

} // CSGafferUI
