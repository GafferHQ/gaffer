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

#include "CsVisualiseVertexIdTool.h"

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
#include <IECoreScene/Primitive.h>

#include <IECoreGL/GL.h>
#include <IECoreGL/Debug.h>
#include <IECoreGL/CachedConverter.h>
//#include <IECoreGL/Buffer.h>
//#include <IECoreGL/Primitive.h>
//#include <IECoreGL/Shader.h>
#include <IECoreGL/ShaderLoader.h>
#if ( GAFFER_MILESTONE_VERSION == 0 && GAFFER_MAJOR_VERSION < 61 )
#include <IECoreGL/Selector.h>
#endif

//#include <Imath/ImathBox.h>

#include <boost/bind/bind.hpp>
#include <boost/algorithm/string/predicate.hpp>

#include <limits>
#include <sstream>
#include <string>

namespace
{
    // text sizes

    float const g_textSizeDefault = 9.0f;
    float const g_textSizeMin = 6.0f;
    float const g_textSizeInc = 0.5f;
    float const g_cursorRadiusDefault = 25.f;

    Imath::Color3f const g_colourFGDefault( 0.9f );
    Imath::Color3f const g_colourHLDefault( 0.466f, 0.612f, 0.741f );

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
    };

    // block binding indexes for the uniform and shader storage buffers

    GLuint const g_uniformBlockBindingIndex = 0;
    GLuint const g_storageBlockBindingIndex = 0;

    // uniform block definition (std140 layout)

#   define UNIFORM_BLOCK_NAME "UniformBlock"
#   define UNIFORM_BLOCK_GLSL_SOURCE \
        "layout( std140, row_major ) uniform " UNIFORM_BLOCK_NAME "\n" \
        "{\n" \
        "   mat4 o2c;\n" \
        "} uniforms;\n"

    // shader storage block definition (std430 layout)
    //
    // NOTE : std430 layout ensures that the elements of a uint array are tightly packed
    //        std140 would require 16 byte alignment of each element ...

#   define STORAGE_BLOCK_NAME "StorageBlock"
#   define STORAGE_BLOCK_GLSL_SOURCE \
        "layout( std430 ) buffer " STORAGE_BLOCK_NAME "\n" \
        "{\n" \
        "   coherent restrict uint visibility[];\n" \
        "} buffers;\n"

    // vertex attribute definitions

#   define ATTRIB_GLSL_LOCATION_PS 0
#   define ATTRIB_GLSL_SOURCE \
        "layout( location = " BOOST_PP_STRINGIZE( ATTRIB_GLSL_LOCATION_PS ) " ) in vec3 ps;\n"

    // interface block definition

#   define INTERFACE_BLOCK_GLSL_SOURCE( STORAGE, NAME ) \
        BOOST_PP_STRINGIZE( STORAGE ) " InterfaceBlock\n" \
        "{\n" \
        "   flat uint vertexId;\n" \
        "} " BOOST_PP_STRINGIZE( NAME ) ";\n"

    // opengl vertex shader code

    std::string const g_vertSource
    (
        "#version 430\n"

        UNIFORM_BLOCK_GLSL_SOURCE

        ATTRIB_GLSL_SOURCE

        INTERFACE_BLOCK_GLSL_SOURCE( out, outputs )

        "void main()\n"
        "{\n"
        "   gl_Position = vec4( ps, 1.0 ) * uniforms.o2c;\n"
        "   outputs.vertexId = uint( gl_VertexID );\n"
        "}\n"
    );

    // opengl fragment shader code

    std::string const g_fragSource
    (
        "#version 430\n"

        // NOTE : ensure that shader is only run for fragments that pass depth test.

        "layout( early_fragment_tests ) in;\n"

        STORAGE_BLOCK_GLSL_SOURCE

        UNIFORM_BLOCK_GLSL_SOURCE

        INTERFACE_BLOCK_GLSL_SOURCE( in, inputs )

        "void main()\n"
        "{\n"
        "   uint index = inputs.vertexId / 32u;\n"
        "   uint value = inputs.vertexId % 32u;\n"
        "   atomicOr( buffers.visibility[ index ], 1u << value );\n"
        "}\n"
    );

    // the gadget that does the actual opengl drawing of the vertex id text

    struct Gadget
    : public GafferUI::Gadget
    {
        explicit
        Gadget
        (
            CSGafferUI::CsVisualiseVertexIdTool& tool,
            std::string const& name = "CsVisualiseVertexIdGadget"
        )
        : GafferUI::Gadget( name )
        , m_tool( & tool )
        , m_shader()
        , m_uniformBuffer()
        , m_storageBuffer()
        , m_storageCapacity( 0 )
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
                glBindBuffer( GL_UNIFORM_BUFFER, uniformBinding );
                m_uniformBuffer.reset( new IECoreGL::Buffer( buffer ) );
            }

            UniformBlock uniforms;

            // bootleg storage buffer

            GLint storageBinding;
            glGetIntegerv( GL_SHADER_STORAGE_BUFFER_BINDING, & storageBinding );

            if( ! m_storageBuffer )
            {
                GLuint buffer = 0u;
                glGenBuffers( 1, & buffer );
                m_storageBuffer.reset( new IECoreGL::Buffer( buffer ) );
            }

            // save opengl state

            GLfloat pointSize;
            glGetFloatv( GL_POINT_SIZE, & pointSize );

            GLint depthFunc;
            glGetIntegerv( GL_DEPTH_FUNC, & depthFunc );

            GLboolean depthWriteEnabled;
            glGetBooleanv( GL_DEPTH_WRITEMASK, & depthWriteEnabled );

            GLboolean const depthEnabled = glIsEnabled( GL_DEPTH_TEST );
            GLboolean const multisampleEnabled = glIsEnabled( GL_MULTISAMPLE );

            GLint shaderProgram;
            glGetIntegerv( GL_CURRENT_PROGRAM, & shaderProgram );

            GLint arrayBinding;
            glGetIntegerv( GL_ARRAY_BUFFER_BINDING, & arrayBinding );

            // get the world to clip space matrix

            Imath::M44f v2c;
            glGetFloatv( GL_PROJECTION_MATRIX, v2c.getValue() );
            Imath::M44f const w2c = viewportGadget->getCameraTransform().gjInverse() * v2c;

            // get raster space bounding box

            Imath::Box2f const rasterBounds = Imath::Box2f( Imath::V2f( 0.f ),
                Imath::V2f( static_cast< float >( viewportGadget->getViewport().x ),
                            static_cast< float >( viewportGadget->getViewport().y ) ) );

            // get text raster space scale and colour
            //
            // NOTE : It seems that Gaffer defines the origin of raster space as the top left corner
            //        of the viewport, however the style text drawing functions assume that y increases
            //        "up" the screen rather than "down", so invert y to ensure text is not upside down.

            float const size = m_tool->sizePlug()->getValue();
            Imath::V3f const scale( size, -size, 1.f );
            Imath::Color4f const colourFG = convertToColor4f( m_tool->colourPlug()->getValue() );
            Imath::Color4f const colourHL = convertToColor4f( m_tool->cursorColourPlug()->getValue() );

            // get cursor raster position

            int cursorVertexId = -1;
            Imath::V2f const cursorRasterPos = m_tool->cursorPos();
            Imath::V2f cursorVertexRasterPos = Imath::V2f( -1.f );
            float minDistance2 = std::numeric_limits< float >::max();

            // get cursor search radius
            //
            // NOTE : when the cursor position is invalid set the radius to zero to disable search.

            Imath::Box2i const viewport( Imath::V2i( 0 ), viewportGadget->getViewport() );
            float const cursorRadius = ( m_tool->cursorPosValid() && viewport.intersects( cursorRasterPos ) )
                ? m_tool->cursorRadiusPlug()->getValue() : 0.f;
            float const cursorRadius2 = cursorRadius * cursorRadius;

            // loop through current selection

            std::stringstream oss;
            for( std::vector< CSGafferUI::CsVisualiseVertexIdTool::Selection >::const_iterator
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

                // find "P" vertex attribute
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

                IECore::ConstV3fVectorDataPtr const pData =
                    primitive->expandedVariableData< IECore::V3fVectorData >(
                        g_pName, IECoreScene::PrimitiveVariable::Vertex, false /* throwIfInvalid */ );

                if( ! pData )
                {
                    continue;
                }

                // retrieve cached opengl buffer data

                IECoreGL::ConstBufferPtr const pBuffer =
                    IECore::runTimeCast< IECoreGL::Buffer const >( converter->convert( pData.get() ) );

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

                glBindBufferBase( GL_UNIFORM_BUFFER, g_uniformBlockBindingIndex, m_uniformBuffer->m_buffer );
                glBufferData( GL_UNIFORM_BUFFER, sizeof( UniformBlock ), & uniforms, GL_DYNAMIC_DRAW );

                // ensure storage buffer capacity

                glBindBufferBase( GL_SHADER_STORAGE_BUFFER, g_storageBlockBindingIndex, m_storageBuffer->m_buffer );

                std::size_t const storageCapacity =
                    ( pData->readable().size() / static_cast< std::size_t >( 32 ) )
                        + static_cast< std::size_t >( 1 );
                std::size_t const storageSize = sizeof( std::uint32_t ) * storageCapacity;

                if( m_storageCapacity < storageCapacity )
                {
                    glBufferData( GL_SHADER_STORAGE_BUFFER, storageSize, 0, GL_DYNAMIC_DRAW );
                    m_storageCapacity = storageCapacity;
                }

                // clear storage buffer
                //
                // NOTE : Shader writes to individual bits using atomicOr instruction so region of
                //        storage buffer being used for current object needs to be cleared to zero

                GLuint const zeroValue = 0u;
                glClearBufferSubData( GL_SHADER_STORAGE_BUFFER, GL_R32UI, 0, storageSize,
                    GL_RED_INTEGER, GL_UNSIGNED_INT, & zeroValue );

                // set opengl state

                glPointSize( 3.f );
                glDepthFunc( GL_LEQUAL );
                if( ! depthEnabled ) glEnable( GL_DEPTH_TEST );
                if( depthEnabled ) glDisable( GL_DEPTH_TEST );
                if( depthWriteEnabled ) glDepthMask( GL_FALSE );
                if( multisampleEnabled ) glDisable( GL_MULTISAMPLE );

                // set opengl vertex attribute array state

                glPushClientAttrib( GL_CLIENT_VERTEX_ARRAY_BIT );

                glVertexAttribDivisor( ATTRIB_GLSL_LOCATION_PS, 0 );
                glEnableVertexAttribArray( ATTRIB_GLSL_LOCATION_PS );

                // set visibility pass shader

                glUseProgram( m_shader->program() );

                // draw points and ouput visibility to storage buffer

                glBindBuffer( GL_ARRAY_BUFFER, pBuffer->m_buffer );
                glVertexAttribPointer( ATTRIB_GLSL_LOCATION_PS, 3, GL_FLOAT, GL_FALSE, 0,
                    static_cast< void const* >( 0 ) );
                glDrawArrays( GL_POINTS, 0, static_cast< GLsizei >( pData->readable().size() ) );

                // restore opengl state

                glPopClientAttrib();
                glBindBuffer( GL_ARRAY_BUFFER, arrayBinding );
                glBindBuffer( GL_UNIFORM_BUFFER, uniformBinding );

                glPointSize( pointSize );
                glDepthFunc( depthFunc );
                if( ! depthEnabled ) glDisable( GL_DEPTH_TEST );
                if( depthEnabled ) glEnable( GL_DEPTH_TEST );
                if( depthWriteEnabled ) glDepthMask( GL_TRUE );
                if( multisampleEnabled ) glEnable( GL_MULTISAMPLE );
                glUseProgram( shaderProgram );

                // map storage buffer

                std::uint32_t const* const vBuffer =
                    static_cast< std::uint32_t* >( glMapBufferRange(
                        GL_SHADER_STORAGE_BUFFER, 0, storageSize, GL_MAP_READ_BIT ) );
                glBindBuffer( GL_SHADER_STORAGE_BUFFER, storageBinding );

                // draw vertex ids offset to vertex position in raster space

                if( vBuffer )
                {
                    GafferUI::ViewportGadget::RasterScope raster( viewportGadget );

                    std::vector< Imath::V3f > const& points = pData->readable();
                    for( int i = 0; i < points.size(); ++i )
                    {
                        // check visibility of vertex
                        
                        std::uint32_t const index = static_cast< std::uint32_t >( i ) / static_cast< std::uint32_t >( 32u );
                        std::uint32_t const value = static_cast< std::uint32_t >( i ) % static_cast< std::uint32_t >( 32u );

                        if( vBuffer[ index ] & ( static_cast< std::uint32_t >( 1u ) << value ) )
                        {
                            // transform vertex position to raster space and do manual scissor test
                            //
                            // NOTE : visibility pass encorporates scissor test which culls most
                            //        vertices however some will slip through as visibility pass
                            //        draws "fat" points. bounds test is cheap.
                            
                            Imath::V3f worldPos;
                            o2w.multVecMatrix( points[ i ], worldPos );
                            Imath::V2f rasterPos = viewportGadget->worldToRasterSpace( worldPos );
                            if( rasterBounds.intersects( rasterPos ) )
                            {
                                int vertexId = i;

                                // update cursor vertex id
                                //
                                // NOTE : We defer drawing of the vertex id currently under the cursor, so
                                //        draw the last vertex id label if we replace the cursor vertex id

                                float const distance2 = ( cursorRasterPos - rasterPos ).length2();
                                if( ( distance2 < cursorRadius2 ) && ( distance2 < minDistance2 ) )
                                {
                                    using std::swap;
                                    swap( cursorVertexId, vertexId );
                                    swap( cursorVertexRasterPos, rasterPos );
                                    minDistance2 = distance2;
                                }

                                // draw vertex id label

                                if( vertexId != -1 )
                                {
                                    oss.str( "" );
                                    oss.clear();
                                    oss << vertexId;
                                    std::string const text = oss.str();

                                    glPushMatrix();
                                    glTranslatef( rasterPos.x - style->textBound( GafferUI::Style::LabelText, text ).size().x * 0.5f * scale.x, rasterPos.y, 0.f );
                                    glScalef( scale.x, scale.y, scale.z );
                                    style->renderText( GafferUI::Style::LabelText, text, GafferUI::Style::NormalState, & colourFG );
                                    glPopMatrix();
                                }
                            }
                        }
                    }

                    // unmap storage buffer

                    glBindBuffer( GL_SHADER_STORAGE_BUFFER, m_storageBuffer->m_buffer );
                    glUnmapBuffer( GL_SHADER_STORAGE_BUFFER );
                    glBindBuffer( GL_SHADER_STORAGE_BUFFER, storageBinding );
                }

                glBindBuffer( GL_SHADER_STORAGE_BUFFER, storageBinding );
            }

            // draw cursor vertex

            if( cursorVertexId != -1 )
            {
                GafferUI::ViewportGadget::RasterScope raster( viewportGadget );
                
                oss.str( "" );
                oss.clear();
                oss << cursorVertexId;
                std::string const text = oss.str();

                glPushMatrix();
                glTranslatef( cursorVertexRasterPos.x - style->textBound( GafferUI::Style::LabelText, text ).size().x * scale.x, cursorVertexRasterPos.y, 0.f );
                glScalef( scale.x * 2.f, scale.y * 2.f, scale.z );
                style->renderText( GafferUI::Style::LabelText, text, GafferUI::Style::NormalState, & colourHL );
                glPopMatrix();
            }

            // set tool cursor vertex id

            m_tool->cursorVertexId( cursorVertexId );
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
        bool hasLayer( GafferUI::Gadget::Layer layer ) const override
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
                    GLuint const uniformblockIndex = glGetProgramResourceIndex( program, GL_UNIFORM_BLOCK, UNIFORM_BLOCK_NAME );
                    if( uniformblockIndex != GL_INVALID_INDEX )
                    {
                        glUniformBlockBinding( program, uniformblockIndex, g_uniformBlockBindingIndex );
                    }
                    GLuint const storageblockIndex = glGetProgramResourceIndex( program, GL_SHADER_STORAGE_BLOCK, STORAGE_BLOCK_NAME );
                    if( storageblockIndex != GL_INVALID_INDEX )
                    {
                        glShaderStorageBlockBinding( program, storageblockIndex, g_storageBlockBindingIndex );
                    }
                }
            }
        }

        CSGafferUI::CsVisualiseVertexIdTool* m_tool;
        mutable IECoreGL::ConstShaderPtr m_shader;
        mutable IECoreGL::ConstBufferPtr m_uniformBuffer;
        mutable IECoreGL::ConstBufferPtr m_storageBuffer;
        mutable std::size_t m_storageCapacity;
    };

} // namespace

namespace CSGafferUI
{
    GAFFER_NODE_DEFINE_TYPE( CsVisualiseVertexIdTool );

    GafferUI::Tool::ToolDescription< CsVisualiseVertexIdTool, GafferSceneUI::SceneView > CsVisualiseVertexIdTool::m_toolDescription;
    
    size_t CsVisualiseVertexIdTool::m_firstPlugIndex = 0;

    CsVisualiseVertexIdTool::CsVisualiseVertexIdTool
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
    , m_cursorVertexId( -1 )
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

        addChild( new Gaffer::FloatPlug( "size", Gaffer::Plug::In, g_textSizeDefault, g_textSizeMin ) );
        addChild( new Gaffer::Color3fPlug( "colour", Gaffer::Plug::In, g_colourFGDefault ) );
        addChild( new Gaffer::Color3fPlug( "cursorColour", Gaffer::Plug::In, g_colourHLDefault ) );
        addChild( new Gaffer::FloatPlug( "cursorRadius", Gaffer::Plug::In, g_cursorRadiusDefault, 0.f ) );
        addChild( new GafferScene::ScenePlug( "__scene", Gaffer::Plug::In ) );

        // connect our internal scene plug to the parent view's scene plug

        internalScenePlug()->setInput( view->inPlug< GafferScene::ScenePlug >() );

        // connect signal handlers
        //
        // NOTE : connecting to the viewport gadget means we will get called for all events
        //        which makes sense for key events, however we do not want to display vertex id
        //        text when the mouse is over another gadget, (eg. Transform Tool handle)
        //        so instead connect to scene gadget signal.
        // NOTE : There are other handlers that will attempt to consume button and drag
        //        events so connect handlers at the front of button/drag signal handler queues.

        view->viewportGadget()->keyPressSignal().connect(
            boost::bind( & CsVisualiseVertexIdTool::keyPress, this, boost::placeholders::_2 ) );

        // NOTE : drag end and button release handlers remain whilst tool inactive in case tool
        //        is made inactive after button pressed or drag initiated in which case these
        //        handlers still need to tidy up state.

        sceneGadget()->buttonReleaseSignal().
#           if ( GAFFER_MILESTONE_VERSION > 0 || GAFFER_MAJOR_VERSION >= 62 )
            connectFront
#           else
            connect
#           endif
            ( boost::bind( & CsVisualiseVertexIdTool::buttonRelease, this, boost::placeholders::_2 )
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
            ( boost::bind( & CsVisualiseVertexIdTool::dragEnd, this, boost::placeholders::_2 )
#           if ( GAFFER_MILESTONE_VERSION == 0 && GAFFER_MAJOR_VERSION < 62 )
            , boost::signals::at_front
#           endif
            );

        // NOTE : mouse tracking handlers remain connected whilst tool inactive as they track the cursor
        //        line and whether its valid or not. This prevents the vertex id display from "sticking" to
        //        edge of viewport when cursor leaves viewport's screen space. It also means that we do
        //        not have to work out the cursor line and whether its valid when tool is made active.

        sceneGadget()->enterSignal().connect(
            boost::bind( & CsVisualiseVertexIdTool::enter, this, boost::placeholders::_2 ) );
        sceneGadget()->leaveSignal().connect(
            boost::bind( & CsVisualiseVertexIdTool::leave, this, boost::placeholders::_2 ) );
        sceneGadget()->mouseMoveSignal().connect(
            boost::bind( & CsVisualiseVertexIdTool::mouseMove, this, boost::placeholders::_2 ) );

        plugDirtiedSignal().connect(
            boost::bind( & CsVisualiseVertexIdTool::plugDirtied, this, boost::placeholders::_1 ) );

#       if GAFFER_COMPATIBILITY_VERSION >= MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
        view->contextChangedSignal().connect(
            boost::bind( & CsVisualiseVertexIdTool::contextChanged, this ) );
        GafferSceneUI::ScriptNodeAlgo::selectedPathsChangedSignal( view->scriptNode() ).connect(
                boost::bind( &CsVisualiseVertexIdTool::selectedPathsChanged, this ) );
#       else
        connectToViewContext();
        view->contextChangedSignal().connect(
            boost::bind( & CsVisualiseVertexIdTool::connectToViewContext, this ) );
#       endif

        Gaffer::Metadata::plugValueChangedSignal().connect(
            boost::bind( & CsVisualiseVertexIdTool::metadataChanged, this, boost::placeholders::_3 ) );
        Gaffer::Metadata::nodeValueChangedSignal().connect(
            boost::bind( & CsVisualiseVertexIdTool::metadataChanged, this, boost::placeholders::_2 ) );
    }

    CsVisualiseVertexIdTool::~CsVisualiseVertexIdTool()
    {
        // NOTE : ensure that the gadget's reference to the tool is reset

        static_cast< Gadget* >( m_gadget.get() )->resetTool();
    }

    Gaffer::FloatPlug* CsVisualiseVertexIdTool::sizePlug()
    {
        return const_cast< Gaffer::FloatPlug* >(
            static_cast< CsVisualiseVertexIdTool const* >( this )->sizePlug() );
    }

    Gaffer::FloatPlug const* CsVisualiseVertexIdTool::sizePlug() const
    {
        return getChild< Gaffer::FloatPlug >( m_firstPlugIndex + 0 );
    }

    Gaffer::Color3fPlug* CsVisualiseVertexIdTool::colourPlug()
    {
        return const_cast< Gaffer::Color3fPlug* >(
            static_cast< CsVisualiseVertexIdTool const* >( this )->colourPlug() );
    }

    Gaffer::Color3fPlug const* CsVisualiseVertexIdTool::colourPlug() const
    {
        return getChild< Gaffer::Color3fPlug >( m_firstPlugIndex + 1 );
    }

    Gaffer::Color3fPlug* CsVisualiseVertexIdTool::cursorColourPlug()
    {
        return const_cast< Gaffer::Color3fPlug* >(
            static_cast< CsVisualiseVertexIdTool const* >( this )->cursorColourPlug() );
    }

    Gaffer::Color3fPlug const* CsVisualiseVertexIdTool::cursorColourPlug() const
    {
        return getChild< Gaffer::Color3fPlug >( m_firstPlugIndex + 2 );
    }

    Gaffer::FloatPlug* CsVisualiseVertexIdTool::cursorRadiusPlug()
    {
        return const_cast< Gaffer::FloatPlug* >(
            static_cast< CsVisualiseVertexIdTool const* >( this )->cursorRadiusPlug() );
    }

    Gaffer::FloatPlug const* CsVisualiseVertexIdTool::cursorRadiusPlug() const
    {
        return getChild< Gaffer::FloatPlug >( m_firstPlugIndex + 3 );
    }

    GafferScene::ScenePlug* CsVisualiseVertexIdTool::internalScenePlug()
    {
        return const_cast< GafferScene::ScenePlug* >(
            static_cast< CsVisualiseVertexIdTool const* >( this )->internalScenePlug() );
    }

    GafferScene::ScenePlug const* CsVisualiseVertexIdTool::internalScenePlug() const
    {
        return getChild< GafferScene::ScenePlug >( m_firstPlugIndex + 4 );
    }

    std::vector< CsVisualiseVertexIdTool::Selection > const& CsVisualiseVertexIdTool::selection() const
    {
        return m_selection;
    }

    Imath::V2f CsVisualiseVertexIdTool::cursorPos() const
    {
        return m_cursorPos;
    }

    bool CsVisualiseVertexIdTool::cursorPosValid() const
    {
        return m_cursorPosValid;
    }

    void CsVisualiseVertexIdTool::cursorVertexId( int const vertexId )
    {
        m_cursorVertexId = vertexId;
    }

    void CsVisualiseVertexIdTool::connectOnActive()
    {
        // NOTE : There are other handlers that will attempt to consume button and drag events
        //        so connect handlers at the front of button/drag signal handler queues. 

        m_buttonPressConnection = sceneGadget()->buttonPressSignal().
#           if ( GAFFER_MILESTONE_VERSION > 0 || GAFFER_MAJOR_VERSION >= 62 )
            connectFront
#           else
            connect
#           endif
            ( boost::bind( & CsVisualiseVertexIdTool::buttonPress, this, boost::placeholders::_2 )
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
            ( boost::bind( & CsVisualiseVertexIdTool::dragBegin, this, boost::placeholders::_2 )
#           if ( GAFFER_MILESTONE_VERSION == 0 && GAFFER_MAJOR_VERSION < 62 )
            , boost::signals::at_front
#           endif
            );

        m_preRenderConnection = view()->viewportGadget()->preRenderSignal().connect(
            boost::bind( & CsVisualiseVertexIdTool::preRender, this ) );

        // NOTE : redraw necessary to ensure value display updated.

        view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
    }

    void CsVisualiseVertexIdTool::disconnectOnInactive()
    {
        m_preRenderConnection.disconnect();
        m_buttonPressConnection.disconnect();
        m_dragBeginConnection.disconnect();
    }

#   if GAFFER_COMPATIBILITY_VERSION >= MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
    void CsVisualiseVertexIdTool::contextChanged()
    {
        // Context changes can change the scene, which in turn
        // dirties our selection.
        selectedPathsChanged();
    }

    void CsVisualiseVertexIdTool::selectedPathsChanged()
    {
        m_selectionDirty = true;
        m_gadgetDirty = true;
        m_priorityPathsDirty = true;
    }
#   else
    void CsVisualiseVertexIdTool::connectToViewContext()
    {
        m_contextChangedConnection = view()->getContext()->changedSignal().connect(
            boost::bind( & CsVisualiseVertexIdTool::contextChanged, this, boost::placeholders::_2 ) );
    }

    void CsVisualiseVertexIdTool::contextChanged
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

    bool CsVisualiseVertexIdTool::mouseMove
    (
        GafferUI::ButtonEvent const& event
    )
    {
        if( m_initiatedDrag )
        {
            return false;
        }

        updateCursorPos( event, true );

        // NOTE : only schedule redraw if tool active

        if( activePlug()->getValue() )
        {
            view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
        }

        return false;
    }

    void CsVisualiseVertexIdTool::enter
    (
        GafferUI::ButtonEvent const& event
    )
    {
        updateCursorPos( event, true );
        
        // NOTE : only schedule redraw if tool active
        
        if( activePlug()->getValue() )
        {
            view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
        }
    }

    void CsVisualiseVertexIdTool::leave
    (
        GafferUI::ButtonEvent const& event
    )
    {
        updateCursorPos( event, false );

        // NOTE : only schedule redraw if tool active
        
        if( activePlug()->getValue() )
        {
            view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
        }
    }

    bool CsVisualiseVertexIdTool::keyPress
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

    bool CsVisualiseVertexIdTool::buttonPress
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

    bool CsVisualiseVertexIdTool::buttonRelease
    (
        GafferUI::ButtonEvent const& event
    )
    {
        m_acceptedButtonPress = false;
        m_initiatedDrag = false;

        return false;
    }

    IECore::RunTimeTypedPtr
    CsVisualiseVertexIdTool::dragBegin
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
            m_cursorPosValid = false;
            view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
            GafferUI::Pointer::setCurrent( "values" );
        }

        return m_cursorValue;
    }

    bool CsVisualiseVertexIdTool::dragEnd
    (
        GafferUI::DragDropEvent const& event
    )
    {
        if( ! m_initiatedDrag )
        {
            return false;
        }

        m_initiatedDrag = false;
        updateCursorPos( event, true );
        GafferUI::Pointer::setCurrent( "" );
        return true;
    }

    void CsVisualiseVertexIdTool::plugDirtied
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
        if( ( plug == sizePlug() ) ||
            ( plug == colourPlug() ) ||
            ( plug == cursorColourPlug() ) ||
            ( plug == cursorRadiusPlug() ) )
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

    void CsVisualiseVertexIdTool::metadataChanged
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

    void CsVisualiseVertexIdTool::updateSelection() const
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

    void CsVisualiseVertexIdTool::preRender()
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

    void CsVisualiseVertexIdTool::updateCursorPos
    (
        GafferUI::ButtonEvent const& event,
        bool const valid
    )
    {
        // update cursor raster position
        //
        // NOTE : the cursor position is stored in raster space so it is free of camera
        //        transformations so we do not need to track camera changes.

        if( valid )
        {
            assert( view() );
            assert( view()->viewportGadget() );

            m_cursorPos = view()->viewportGadget()->gadgetToRasterSpace( event.line.p1, sceneGadget() );
        }

        m_cursorPosValid = valid;
    }

    void CsVisualiseVertexIdTool::updateCursorValue()
    {
        IECore::DataPtr cursorValue = m_cursorValue;
        m_cursorValue.reset();

        // NOTE : cursor value invalid when cursor position is invalid (during drag or no cursor focus)

        if( ! m_cursorPosValid || m_cursorVertexId == -1 )
        {
            return;
        }

        // store cursor value

        IECore::IntDataPtr data =
            IECore::runTimeCast< IECore::IntData >( cursorValue );
        if( ! data ) data.reset( new IECore::IntData() );
        data->writable() = m_cursorVertexId;
        cursorValue = data;

        m_cursorValue = cursorValue;
    }

    GafferSceneUI::SceneGadget* CsVisualiseVertexIdTool::sceneGadget()
    {
        return const_cast< GafferSceneUI::SceneGadget* >(
            static_cast< CsVisualiseVertexIdTool const* >( this )->sceneGadget() );
    }

    GafferSceneUI::SceneGadget const* CsVisualiseVertexIdTool::sceneGadget() const
    {
        return IECore::runTimeCast< GafferSceneUI::SceneGadget const >(
            view()->viewportGadget()->getPrimaryChild() );
    }

    CsVisualiseVertexIdTool::Selection::Selection
    (
        GafferScene::ScenePlug const& scene,
        GafferScene::ScenePlug::ScenePath const& path,
        Gaffer::Context const& context
    )
    : m_scene( & scene )
    , m_path( path )
    , m_context( & context )
    {}

    GafferScene::ScenePlug const& CsVisualiseVertexIdTool::Selection::scene() const
    {
        return *( m_scene );
    }

    GafferScene::ScenePlug::ScenePath const& CsVisualiseVertexIdTool::Selection::path() const
    {
        return m_path;
    }

    Gaffer::Context const& CsVisualiseVertexIdTool::Selection::context() const
    {
        return *( m_context );
    }

} // CSGafferUI
