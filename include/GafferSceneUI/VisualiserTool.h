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

#ifndef CSGAFFERUI_TOOLS_CSVISUALISEVALUETOOL_H
#define CSGAFFERUI_TOOLS_CSVISUALISEVALUETOOL_H

#include "../../GafferTypeIds.h"

#include <Gaffer/Version.h>
#include <Gaffer/StringPlug.h>
#include <Gaffer/NumericPlug.h>
#include <GafferUI/ButtonEvent.h>
#include <GafferUI/DragDropEvent.h>
#include <GafferUI/KeyEvent.h>
#include <GafferUI/ViewportGadget.h>
#include <GafferScene/ScenePlug.h>
#include <GafferSceneUI/SelectionTool.h>

namespace CSGafferUI
{
    /**
     * @brief Tool that displays a named primitive variable of type float/V2f/V3f
     *        of a MeshPrimitive as a coloured overlay.
     */
    struct CsVisualiseValueTool
    : public GafferSceneUI::SelectionTool
    {
        /**
         * @brief ctor
         * @param view parent view
         * @param name name for node
         */
        explicit
        CsVisualiseValueTool
        (
            GafferSceneUI::SceneView* view,
            std::string const& name = Gaffer::GraphComponent::defaultName< CsVisualiseValueTool >()
        );

        /**
         * @brief dtor
         */
        ~CsVisualiseValueTool() override;

        /**
         * @name GafferPlugAccessors
         * @brief Gaffer plug accessor functions
         * @{
         */

        Gaffer::StringPlug* namePlug();
        Gaffer::StringPlug const* namePlug() const;

        Gaffer::FloatPlug* opacityPlug();
        Gaffer::FloatPlug const* opacityPlug() const;

        Gaffer::V3fPlug* valueMinPlug();
        Gaffer::V3fPlug const* valueMinPlug() const;

        Gaffer::V3fPlug* valueMaxPlug();
        Gaffer::V3fPlug const* valueMaxPlug() const;

        Gaffer::FloatPlug* sizePlug();
        Gaffer::FloatPlug const* sizePlug() const;

        Gaffer::Color3fPlug* colourPlug();
        Gaffer::Color3fPlug const* colourPlug() const;

        /**
         * @}
         */

        GAFFER_NODE_DECLARE_TYPE(
            CSGafferUI::CsVisualiseValueTool,
            CSInternalTypes::CsVisualiseValueToolTypeId,
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

        /**
         * @brief Get the cursor position in raster space
         * @return cursor position in raster space
         */
        Imath::V2f cursorPos() const;

        /**
         * @brief Get the value at current cursor position
         * @return value at current cursor position (nullptr if invalid)
         */
        IECore::Data const* cursorValue() const;

    private:

        GafferScene::ScenePlug* internalScenePlug();
        GafferScene::ScenePlug const* internalScenePlug() const;

        void connectOnActive();
        void disconnectOnInactive();
        bool mouseMove( GafferUI::ButtonEvent const& event );
        void enter( GafferUI::ButtonEvent const& event );
        void leave( GafferUI::ButtonEvent const& event );
        bool keyPress( GafferUI::KeyEvent const& event );
        bool buttonPress( GafferUI::ButtonEvent const& event );
        bool buttonRelease( GafferUI::ButtonEvent const& event );
        IECore::RunTimeTypedPtr dragBegin( GafferUI::DragDropEvent const& event );
        bool dragEnd( GafferUI::DragDropEvent const& event );
        void plugDirtied( Gaffer::Plug const* plug );
        void plugSet( Gaffer::Plug* plug );
        void metadataChanged( IECore::InternedString const& key );
        void updateSelection() const;
        void preRender();
        void updateCursorPos( GafferUI::ButtonEvent const& event );
        void updateCursorValue();
        GafferSceneUI::SceneGadget* sceneGadget();
        GafferSceneUI::SceneGadget const* sceneGadget() const;

#       if GAFFER_COMPATIBILITY_VERSION >= MAKE_GAFFER_COMPATIBILITY_VERSION( 1, 5 )
        void contextChanged();
        void selectedPathsChanged();
#       else
        void connectToViewContext();
        void contextChanged( IECore::InternedString const& name );
        Gaffer::Signals::ScopedConnection m_contextChangedConnection;
#       endif
        Gaffer::Signals::ScopedConnection m_preRenderConnection;
        Gaffer::Signals::ScopedConnection m_buttonPressConnection;
        Gaffer::Signals::ScopedConnection m_dragBeginConnection;

        GafferUI::GadgetPtr m_gadget;
        mutable std::vector< Selection > m_selection;
        Imath::V2i m_cursorPos;
        bool m_cursorPosValid;
        IECore::DataPtr m_cursorValue;
        bool m_gadgetDirty;
        mutable bool m_selectionDirty;
        bool m_priorityPathsDirty;
        bool m_acceptedButtonPress;
        bool m_initiatedDrag;

        static ToolDescription< CsVisualiseValueTool, GafferSceneUI::SceneView > m_toolDescription;
        static size_t m_firstPlugIndex;
    };

} // CSGafferUI

#endif // CSGAFFERUI_TOOLS_CSVISUALISEVALUETOOL_H
