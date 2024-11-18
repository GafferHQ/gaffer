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

#ifndef CSGAFFERUI_TOOLS_CSVISUALISEVECTORTOOL_H
#define CSGAFFERUI_TOOLS_CSVISUALISEVECTORTOOL_H

#include "../../GafferTypeIds.h"

#include <Gaffer/Version.h>
#include <Gaffer/StringPlug.h>
#include <Gaffer/NumericPlug.h>
#include <GafferUI/KeyEvent.h>
#include <GafferScene/ScenePlug.h>
#include <GafferSceneUI/SelectionTool.h>

namespace CSGafferUI
{
    /**
     * @brief Tool that displays a named primitive variable of type Imath::V3f as line vectors
     *
     * The data is interpreted and visualised based on the format plug.
     */
    struct CsVisualiseVectorTool
    : public GafferSceneUI::SelectionTool
    {
        /**
         * @brief Data formats
         */
        enum class Format
        {
            Point = 0,  /**< Interpret data as points */
            Vector,     /**< Interpret data as vectors */ 
            Bivector    /**< Interpret data as bivectors */
        };

        /**
         * @brief ctor
         * @param view parent view
         * @param name name for node
         */
        explicit
        CsVisualiseVectorTool
        (
            GafferSceneUI::SceneView* view,
            std::string const& name = Gaffer::GraphComponent::defaultName< CsVisualiseVectorTool >()
        );

        /**
         * @brief dtor
         */
        ~CsVisualiseVectorTool() override;

        /**
         * @name GafferPlugAccessors
         * @brief Gaffer plug accessor functions
         * @{
         */

        Gaffer::StringPlug* namePlug();
        Gaffer::StringPlug const* namePlug() const;

        Gaffer::IntPlug* formatPlug();
        Gaffer::IntPlug const* formatPlug() const;

        Gaffer::FloatPlug* scalePlug();
        Gaffer::FloatPlug const* scalePlug() const;

        Gaffer::Color3fPlug* colourPlug();
        Gaffer::Color3fPlug const* colourPlug() const;

        /**
         * @}
         */

        GAFFER_NODE_DECLARE_TYPE(
            CSGafferUI::CsVisualiseVectorTool,
            CSInternalTypes::CsVisualiseVectorToolTypeId,
            GafferSceneUI::SelectionTool );
        
        /**
         * @brief Class encapsulating a selected scene location
         */
        struct Selection
        {
            /**
             * @brief ctor
             * @param scene scene
             * @param path scene path
             * @param context context
             */
            Selection
            (
                GafferScene::ScenePlug const& scene,
                GafferScene::ScenePlug::ScenePath const& path,
                Gaffer::Context const& context
            );

            /**
             * @brief Get the scene
             * @return scene
             */
            GafferScene::ScenePlug const& scene() const;

            /**
             * @brief Get the scene path
             * @return scene path
             */
            GafferScene::ScenePlug::ScenePath const& path() const;

            /**
             * @brief Get the context
             * @return context
             */
            Gaffer::Context const& context() const;

        private:

            GafferScene::ConstScenePlugPtr m_scene;
            GafferScene::ScenePlug::ScenePath m_path;
            Gaffer::ConstContextPtr m_context;
        };

        /**
         * @brief Get the current selection
         * @return current selection
         */
        std::vector< Selection > const& selection() const;

    private:

        GafferScene::ScenePlug* internalScenePlug();
        GafferScene::ScenePlug const* internalScenePlug() const;

        void plugDirtied( Gaffer::Plug const* plug );
        void metadataChanged( IECore::InternedString const& key );
        void updateSelection() const;
        void preRender();
        bool keyPress( GafferUI::KeyEvent const& event );

#       if GAFFER_COMPATIBILITY_VERSION >= MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
        void contextChanged();
        void selectedPathsChanged();
#       else
        void connectToViewContext();
        void contextChanged( IECore::InternedString const& name );
        Gaffer::Signals::ScopedConnection m_contextChangedConnection;
#       endif
        Gaffer::Signals::ScopedConnection m_preRenderConnection;

        GafferUI::GadgetPtr m_gadget;
        mutable std::vector< Selection > m_selection;
        bool m_gadgetDirty;
        mutable bool m_selectionDirty;
        bool m_priorityPathsDirty;

        static ToolDescription< CsVisualiseVectorTool, GafferSceneUI::SceneView > m_toolDescription;
        static size_t m_firstPlugIndex;
    };

} // CSGafferUI

#endif // CSGAFFERUI_TOOLS_CSVISUALISEVECTORTOOL_H
