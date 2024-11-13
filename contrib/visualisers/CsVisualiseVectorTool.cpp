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

#include "CsVisualiseVectorTool.h"

#include <Gaffer/Metadata.h>
#include <Gaffer/MetadataAlgo.h>
#include <GafferUI/Gadget.h>
#include <GafferUI/Style.h>
#include <GafferUI/ViewportGadget.h>
#include <GafferSceneUI/SceneView.h>
#if GAFFER_COMPATIBILITY_VERSION >= MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
#include <GafferSceneUI/ScriptNodeAlgo.h>
#else
#include <GafferSceneUI/ContextAlgo.h>
#endif

#include <IECore/VectorTypedData.h>
#include <IECoreScene/Primitive.h>

#include <IECoreGL/GL.h>
#include <IECoreGL/CachedConverter.h>
//#include <IECoreGL/Buffer.h>
//#include <IECoreGL/Primitive.h>
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
#include <string>

namespace
{
    // scale and colour constants

    float const g_scaleDefault = 1.f;
    float const g_scaleMin = 10.f * std::numeric_limits< float >::min();
    float const g_scaleInc = 0.01f;

    Imath::Color3f g_colourDefault( 1.f, 1.f, 1.f );

    // name of P primitive variable

    std::string const g_pName( "P" );

    // uniform block structure (std140 layout)

    struct UniformBlock
    {
        alignas( 16 ) Imath::M44f o2v;
        alignas( 16 ) Imath::M44f n2v;
        alignas( 16 ) Imath::M44f v2c;
        alignas( 16 ) Imath::M44f o2c;
        alignas( 16 ) Imath::Color3f colour;
        alignas( 4 ) float scale;
    };

    GLuint const g_uniformBlockBindingIndex = 0;

#   define UNIFORM_BLOCK_GLSL_SOURCE \
        "layout( std140, row_major ) uniform UniformBlock\n" \
        "{\n" \
        "   mat4 o2v;\n" \
        "   mat4 n2v;\n" \
        "   mat4 v2c;\n" \
        "   mat4 o2c;\n" \
        "   vec3 colour;\n" \
        "   float scale;\n" \
        "} uniforms;\n"

#   define ATTRIB_GLSL_LOCATION_PS 0
#   define ATTRIB_GLSL_LOCATION_VS 1

#   define ATTRIB_GLSL_SOURCE \
        "layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_PS ) " ) in vec3 ps;\n" \
        "layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_VS ) " ) in vec3 vs;\n"

    // opengl vertex shader code (point format)

    std::string const g_vertSourcePoint
    (
        "#version 330\n"

        UNIFORM_BLOCK_GLSL_SOURCE

        ATTRIB_GLSL_SOURCE

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

    // opengl vertex shader code (vector format)

    std::string const g_vertSourceVector
    (
        "#version 330\n"

        UNIFORM_BLOCK_GLSL_SOURCE

        ATTRIB_GLSL_SOURCE

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

    // opengl vertex shader code (bivector format)

    std::string const g_vertSourceBivector
    (
        "#version 330\n"

        UNIFORM_BLOCK_GLSL_SOURCE

        ATTRIB_GLSL_SOURCE

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

    // opengl fragment shader code

    std::string const g_fragSource
    (
        "#version 330\n"

        UNIFORM_BLOCK_GLSL_SOURCE

        "layout( location = 0 ) out vec4 cs;\n"

        "void main()\n"
        "{\n"
        "   cs = vec4( uniforms.colour, 1.0 );\n"
        "}\n"
    );

    // the gadget that does the actual opengl drawing of the vector lines

    struct Gadget
    : public GafferUI::Gadget
    {
        explicit
        Gadget
        (
            CSGafferUI::CsVisualiseVectorTool const& tool,
            std::string const& name = "CsVisualiseVectorGadget"
        )
        : GafferUI::Gadget( name )
        , m_tool( & tool )
        , m_vectorShader()
        , m_bivectorShader()
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

            // bootleg shaders

            buildShader( m_pointShader, g_vertSourcePoint );
            buildShader( m_vectorShader, g_vertSourceVector );
            buildShader( m_bivectorShader, g_vertSourceBivector );

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

            // get the name of the primitive variable to visualise and format

            std::string const& name = m_tool->namePlug()->getValue();
            CSGafferUI::CsVisualiseVectorTool::Format const format =
                static_cast< CSGafferUI::CsVisualiseVectorTool::Format >(
                    m_tool->formatPlug()->getValue() );

            // get scale factor and colour

            UniformBlock uniforms;
            uniforms.colour = m_tool->colourPlug()->getValue();
            uniforms.scale = m_tool->scalePlug()->getValue();

            // get the world to view and view to clip space matrices

            Imath::M44f const w2v = viewportGadget->getCameraTransform().gjInverse();
            glGetFloatv( GL_PROJECTION_MATRIX, uniforms.v2c.getValue() );

            // set opengl state

            GLfloat lineWidth;
            glGetFloatv( GL_LINE_WIDTH, & lineWidth );
            glLineWidth( 1.f );

            GLboolean const depthEnabled = glIsEnabled( GL_DEPTH_TEST );
            if( ! depthEnabled ) glEnable( GL_DEPTH_TEST );

            GLboolean depthWriteEnabled;
            glGetBooleanv( GL_DEPTH_WRITEMASK, & depthWriteEnabled );
            if( depthWriteEnabled ) glDepthMask( GL_FALSE );

            GLboolean lineSmooth;
            glGetBooleanv( GL_LINE_SMOOTH, & lineSmooth );
            if( lineSmooth ) glDisable( GL_LINE_SMOOTH );

            GLboolean const blendEnabled = glIsEnabled( GL_BLEND );
            if( blendEnabled ) glDisable( GL_BLEND );

            // choose shader program

            GLint shaderProgram;
            glGetIntegerv( GL_CURRENT_PROGRAM, & shaderProgram );
            glUseProgram( chooseProgram( format ) );

            // set opengl vertex attribute array state

            GLint arrayBinding;
            glGetIntegerv( GL_ARRAY_BUFFER_BINDING, & arrayBinding );

            glPushClientAttrib( GL_CLIENT_VERTEX_ARRAY_BIT );

            glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_PS, 1 );
            glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_PS );
            glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_VS, 1 );
            glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_VS );

            // loop through current selection

            for( std::vector< CSGafferUI::CsVisualiseVectorTool::Selection >::const_iterator
                    it    = m_tool->selection().begin(),
                    itEnd = m_tool->selection().end(); it != itEnd; ++it )
            {
                GafferScene::ScenePlug::PathScope scope( &( ( *it ).context() ), &( ( *it ).path() ) );

                // check path exists

                if( !( ( *it ).scene().existsPlug()->getValue() ) )
                {
                    continue;
                }

                // extract primitive

                IECoreScene::ConstPrimitivePtr const primitive =
                    IECore::runTimeCast< IECoreScene::Primitive const >(
                        ( *it ).scene().objectPlug()->getValue() );
        
                if( ! primitive )
                {
                    continue;
                }

                // retrieve cached IECoreGL primitive

                IECoreGL::ConstPrimitivePtr const primitiveGL =
                    IECore::runTimeCast< IECoreGL::Primitive const >(
                        converter->convert( primitive.get() ) );

                if( ! primitiveGL )
                {
                    continue;
                }

                // find "P" vertex attribute

                IECoreGL::Primitive::AttributeMap::const_iterator const pit =
                    primitiveGL->m_vertexAttributes.find( g_pName );
                if( pit == primitiveGL->m_vertexAttributes.end() )
                {
                    continue;
                }

                IECore::ConstV3fVectorDataPtr const pData =
                    IECore::runTimeCast< IECore::V3fVectorData const >( ( *pit ).second );
                if( ! pData )
                {
                    continue;
                }

                // find named vertex attribute
                //
                // NOTE : conversion to IECoreGL mesh may generate vertex attributes (eg. "N")
                //        so check named primitive variable exists on IECore mesh primitive as well.

                IECoreGL::Primitive::AttributeMap::const_iterator const vit =
                    primitiveGL->m_vertexAttributes.find( name );
                if( ( vit == primitiveGL->m_vertexAttributes.end() ) ||
                    ( primitive->variables.find( name ) == primitive->variables.end() ) )
                {
                    continue;
                }

                IECore::ConstV3fVectorDataPtr const vData =
                    IECore::runTimeCast< IECore::V3fVectorData const >( ( *vit ).second );
                if( ! vData )
                {
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

                // compute object/normal to view and object to clip matrices

                uniforms.o2v = o2w * w2v;
                uniforms.n2v = ( uniforms.o2v.gjInverse() ).transpose();
                uniforms.o2c = uniforms.o2v * uniforms.v2c;

                // upload opengl uniform block data

                glBufferData( GL_UNIFORM_BUFFER, sizeof( UniformBlock ), & uniforms, GL_DYNAMIC_DRAW );

                // instance a line segment for each element of vector data

                glBindBuffer( GL_ARRAY_BUFFER, pBuffer->m_buffer );
                glVertexAttribPointer( ATTRIB_GLSL_LOCATION_PS, 3, GL_FLOAT, GL_FALSE, 0,
                    static_cast< void const* >( 0 ) );
                glBindBuffer( GL_ARRAY_BUFFER, vBuffer->m_buffer );
                glVertexAttribPointer( ATTRIB_GLSL_LOCATION_VS, 3, GL_FLOAT, GL_FALSE, 0,
                    static_cast< void const* >( 0 ) );
                glDrawArraysInstanced( GL_LINES, 0, 2, static_cast< GLsizei >( pData->readable().size() ) );
            }

            // restore opengl state

            glPopClientAttrib();
            glBindBuffer( GL_ARRAY_BUFFER, arrayBinding );
            glBindBuffer( GL_UNIFORM_BUFFER, uniformBinding );
            
            glLineWidth( lineWidth );

            if( lineSmooth ) glEnable( GL_LINE_SMOOTH );
            if( blendEnabled ) glEnable( GL_BLEND );
            if( ! depthEnabled ) glDisable( GL_DEPTH_TEST );
            if( depthWriteEnabled ) glDepthMask( GL_TRUE );
            glUseProgram( shaderProgram );
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

        GLuint
        chooseProgram
        (
            CSGafferUI::CsVisualiseVectorTool::Format const format
        )
        const
        {
            IECoreGL::Shader const* shader = nullptr;
            switch( format )
            {
                case CSGafferUI::CsVisualiseVectorTool::Format::Point:
                    shader = m_pointShader.get();
                    break;
                case CSGafferUI::CsVisualiseVectorTool::Format::Vector:
                    shader = m_vectorShader.get();
                    break;
                case CSGafferUI::CsVisualiseVectorTool::Format::Bivector:
                    shader = m_bivectorShader.get();
                    break;
                default:
                    assert( 0 );
                    break;
            }

            return ( shader != nullptr ) ? shader->program() : static_cast< GLuint >( 0 );
        }

        void
        buildShader
        (
            IECoreGL::ConstShaderPtr& shader,
            std::string const& vertSource
        )
        const
        {
            if( ! shader )
            {
                shader = IECoreGL::ShaderLoader::defaultShaderLoader()->create(
                    vertSource, std::string(), g_fragSource );
                if( shader )
                {
                    GLuint const program = shader->program();
                    GLuint const blockIndex = glGetUniformBlockIndex( program, "UniformBlock" );
                    if( blockIndex != GL_INVALID_INDEX )
                    {
                        glUniformBlockBinding( program, blockIndex, g_uniformBlockBindingIndex );
                    }
                }
            }
        }

        CSGafferUI::CsVisualiseVectorTool const* m_tool;
        mutable IECoreGL::ConstShaderPtr m_pointShader;
        mutable IECoreGL::ConstShaderPtr m_vectorShader;
        mutable IECoreGL::ConstShaderPtr m_bivectorShader;
        mutable IECoreGL::ConstBufferPtr m_uniformBuffer;
    };

} // namespace

namespace CSGafferUI
{
    GAFFER_NODE_DEFINE_TYPE( CsVisualiseVectorTool )

    GafferUI::Tool::ToolDescription< CsVisualiseVectorTool, GafferSceneUI::SceneView > CsVisualiseVectorTool::m_toolDescription;

    size_t CsVisualiseVectorTool::m_firstPlugIndex = 0;

    CsVisualiseVectorTool::CsVisualiseVectorTool
    (
        GafferSceneUI::SceneView* const view,
        std::string const& name
    )
    : GafferSceneUI::SelectionTool( view, name )
#   if GAFFER_COMPATIBILITY_VERSION < MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
    , m_contextChangedConnection()
#   endif
    , m_preRenderConnection()
    , m_gadget( new Gadget( *this ) )
    , m_selection()
    , m_gadgetDirty( true )
    , m_selectionDirty( true )
    , m_priorityPathsDirty( true )
    {
        // add gadget to view and hide

        view->viewportGadget()->addChild( m_gadget );
        m_gadget->setVisible( false );

        // store offset of first plug

        storeIndexOfNextChild( m_firstPlugIndex );

        // add child plugs

        addChild( new Gaffer::StringPlug( "name", Gaffer::Plug::In, "N" ) );
        addChild( new Gaffer::IntPlug( "format", Gaffer::Plug::In,
            static_cast< int >( Format::Bivector ),
            static_cast< int >( Format::Point ),
            static_cast< int >( Format::Bivector ) ) );
        addChild( new Gaffer::FloatPlug( "scale", Gaffer::Plug::In, g_scaleDefault, g_scaleMin ) );
        addChild( new Gaffer::Color3fPlug( "colour", Gaffer::Plug::In, g_colourDefault ) );
        addChild( new GafferScene::ScenePlug( "__scene", Gaffer::Plug::In ) );

        // connect out internal scene plug to the parent view's scene plug

        internalScenePlug()->setInput( view->inPlug< GafferScene::ScenePlug >() );

        // connect signal handlers

        view->viewportGadget()->keyPressSignal().connect(
            boost::bind( & CsVisualiseVectorTool::keyPress, this, boost::placeholders::_2 ) );

        plugDirtiedSignal().connect(
            boost::bind( & CsVisualiseVectorTool::plugDirtied, this, boost::placeholders::_1 ) );

#       if GAFFER_COMPATIBILITY_VERSION >= MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
        view->contextChangedSignal().connect(
            boost::bind( & CsVisualiseVectorTool::contextChanged, this ) );
        GafferSceneUI::ScriptNodeAlgo::selectedPathsChangedSignal( view->scriptNode() ).connect(
                boost::bind( &CsVisualiseVectorTool::selectedPathsChanged, this ) );
#       else
        connectToViewContext();
        view->contextChangedSignal().connect(
            boost::bind( & CsVisualiseVectorTool::connectToViewContext, this ) );
#       endif

        Gaffer::Metadata::plugValueChangedSignal().connect(
            boost::bind( & CsVisualiseVectorTool::metadataChanged, this, boost::placeholders::_3 ) );
        Gaffer::Metadata::nodeValueChangedSignal().connect(
            boost::bind( & CsVisualiseVectorTool::metadataChanged, this, boost::placeholders::_2 ) );
    }

    CsVisualiseVectorTool::~CsVisualiseVectorTool()
    {
        // NOTE : ensure that the gadget's reference to the tool is reset

        static_cast< Gadget* >( m_gadget.get() )->resetTool();
    }

    Gaffer::StringPlug* CsVisualiseVectorTool::namePlug()
    {
        return const_cast< Gaffer::StringPlug* >(
            static_cast< CsVisualiseVectorTool const* >( this )->namePlug() );
    }

    Gaffer::StringPlug const* CsVisualiseVectorTool::namePlug() const
    {
        return getChild< Gaffer::StringPlug >( m_firstPlugIndex + 0 );
    }

    Gaffer::IntPlug* CsVisualiseVectorTool::formatPlug()
    {
        return const_cast< Gaffer::IntPlug* >(
            static_cast< CsVisualiseVectorTool const* >( this )->formatPlug() );
    }

    Gaffer::IntPlug const* CsVisualiseVectorTool::formatPlug() const
    {
        return getChild< Gaffer::IntPlug >( m_firstPlugIndex + 1 );
    }

    Gaffer::FloatPlug* CsVisualiseVectorTool::scalePlug()
    {
        return const_cast< Gaffer::FloatPlug* >(
            static_cast< CsVisualiseVectorTool const* >( this )->scalePlug() );
    }

    Gaffer::FloatPlug const* CsVisualiseVectorTool::scalePlug() const
    {
        return getChild< Gaffer::FloatPlug >( m_firstPlugIndex + 2 );
    }

    Gaffer::Color3fPlug* CsVisualiseVectorTool::colourPlug()
    {
        return const_cast< Gaffer::Color3fPlug* >(
            static_cast< CsVisualiseVectorTool const* >( this )->colourPlug() );
    }

    Gaffer::Color3fPlug const* CsVisualiseVectorTool::colourPlug() const
    {
        return getChild< Gaffer::Color3fPlug >( m_firstPlugIndex + 3 );
    }

    GafferScene::ScenePlug* CsVisualiseVectorTool::internalScenePlug()
    {
        return const_cast< GafferScene::ScenePlug* >(
            static_cast< CsVisualiseVectorTool const* >( this )->internalScenePlug() );
    }

    GafferScene::ScenePlug const* CsVisualiseVectorTool::internalScenePlug() const
    {
        return getChild< GafferScene::ScenePlug >( m_firstPlugIndex + 4 );
    }

    std::vector< CsVisualiseVectorTool::Selection > const& CsVisualiseVectorTool::selection() const
    {
        return m_selection;
    }
#   if GAFFER_COMPATIBILITY_VERSION >= MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
    void CsVisualiseVectorTool::contextChanged()
    {
        // Context changes can change the scene, which in turn
        // dirties our selection.
        selectedPathsChanged();
    }

    void CsVisualiseVectorTool::selectedPathsChanged()
    {
        m_selectionDirty = true;
        m_gadgetDirty = true;
        m_priorityPathsDirty = true;
    }
#   else
    void CsVisualiseVectorTool::connectToViewContext()
    {
        m_contextChangedConnection = view()->getContext()->changedSignal().connect(
            boost::bind( & CsVisualiseVectorTool::contextChanged, this, boost::placeholders::_2 ) );
    }

    void CsVisualiseVectorTool::contextChanged
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

    void CsVisualiseVectorTool::plugDirtied
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
            ( plug == scalePlug() ) ||
            ( plug == colourPlug() ) ||
            ( plug == formatPlug() ) )
        {
            m_gadgetDirty = true;
            view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
        }

        if( plug == activePlug() )
        {
            if( activePlug()->getValue() )
            {
                m_preRenderConnection = view()->viewportGadget()->preRenderSignal().connect(
                    boost::bind( & CsVisualiseVectorTool::preRender, this ) );
            }
            else
            {
                m_preRenderConnection.disconnect();
                m_gadget->setVisible( false );

                static_cast< GafferSceneUI::SceneGadget* >( view()->viewportGadget()->getPrimaryChild() )
                    ->setPriorityPaths( IECore::PathMatcher() );
            }
        }
    }

    void CsVisualiseVectorTool::metadataChanged
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

    void CsVisualiseVectorTool::updateSelection() const
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

    void CsVisualiseVectorTool::preRender()
    {
        updateSelection();

        if( m_priorityPathsDirty )
        {
#           if GAFFER_COMPATIBILITY_VERSION >= MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
            static_cast< GafferSceneUI::SceneGadget* >( view()->viewportGadget()->getPrimaryChild() )
                ->setPriorityPaths( ( m_selection.empty() )
                    ? IECore::PathMatcher()
                    : GafferSceneUI::ScriptNodeAlgo::getSelectedPaths( view()->scriptNode() ) );
#           else
            static_cast< GafferSceneUI::SceneGadget* >( view()->viewportGadget()->getPrimaryChild() )
                ->setPriorityPaths( ( m_selection.empty() )
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
    }

    bool CsVisualiseVectorTool::keyPress
    (
        GafferUI::KeyEvent const& event
    )
    {
        if( ! activePlug()->getValue() )
        {
            return false;
        }

        // allow user to scale vectors with +/- keys

        if( event.key == "Plus" || event.key == "Equal" )
        {
            scalePlug()->setValue( scalePlug()->getValue() + g_scaleInc );
        }
        else
        if( event.key == "Minus" || event.key == "Underscore" )
        {
            scalePlug()->setValue( std::max( scalePlug()->getValue() - g_scaleInc, g_scaleMin ) );
        }

        return false;
    }

    CsVisualiseVectorTool::Selection::Selection
    (
        GafferScene::ScenePlug const& scene,
        GafferScene::ScenePlug::ScenePath const& path,
        Gaffer::Context const& context
    )
    : m_scene( & scene )
    , m_path( path )
    , m_context( & context )
    {}

    GafferScene::ScenePlug const& CsVisualiseVectorTool::Selection::scene() const
    {
        return *( m_scene );
    }

    GafferScene::ScenePlug::ScenePath const& CsVisualiseVectorTool::Selection::path() const
    {
        return m_path;
    }

    Gaffer::Context const& CsVisualiseVectorTool::Selection::context() const
    {
        return *( m_context );
    }

} // CSGafferUI
