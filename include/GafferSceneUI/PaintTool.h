//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "GafferSceneUI/SelectionTool.h"
#include "GafferSceneUI/TypeIds.h"

#include "GafferSceneUI/Private/PrimitiveVariableInspector.h"

#include "GafferScene/EditScopeAlgo.h"
#include "GafferScene/PrimitiveVariablePaint.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePlug.h"

#include "GafferUI/KeyEvent.h"

#include "Gaffer/EditScope.h"

#include "IECoreScene/MeshPrimitive.h"

#include "IECoreGL/Buffer.h"

#include "IECore/KDTree.h"

namespace GafferSceneUI
{

IE_CORE_FORWARDDECLARE( SceneView )

// Forward declaration of class with no public visibility
IE_CORE_FORWARDDECLARE( DepthRender )

class GAFFERSCENEUI_API PaintTool : public GafferSceneUI::SelectionTool
{

	public :

		enum class PaintMode
		{
			Over,
			Erase
		};

		PaintTool( SceneView *view, const std::string &name = defaultName<PaintTool>() );
		~PaintTool() override;

		GAFFER_NODE_DECLARE_TYPE( GafferSceneUI::PaintTool, PaintToolTypeId, SelectionTool );

		Gaffer::StringPlug *variableNamePlug();
		const Gaffer::StringPlug *variableNamePlug() const;

		Gaffer::IntPlug *variableTypePlug();
		const Gaffer::IntPlug *variableTypePlug() const;

		Gaffer::IntPlug *modePlug();
		const Gaffer::IntPlug *modePlug() const;

		Gaffer::FloatPlug *sizePlug();
		const Gaffer::FloatPlug *sizePlug() const;

		Gaffer::FloatPlug *floatValuePlug();
		const Gaffer::FloatPlug *floatValuePlug() const;

		Gaffer::Color3fPlug *colorValuePlug();
		const Gaffer::Color3fPlug *colorValuePlug() const;

		Gaffer::Color3fPlug *colorBackgroundPlug();
		const Gaffer::Color3fPlug *colorBackgroundPlug() const;

		Gaffer::FloatPlug *opacityPlug();
		const Gaffer::FloatPlug *opacityPlug() const;

		Gaffer::FloatPlug *hardnessPlug();
		const Gaffer::FloatPlug *hardnessPlug() const;

		const std::unordered_set< std::string > &warnings() const;

		std::unordered_set< const Gaffer::GraphComponent* > editTargets();
		std::map< std::string, const Gaffer::GraphComponent* > editTargetPerPath();

		/// Returns true only if the selection is non-empty
		/// and every item is editable.
		bool selectionEditable();

		using StatusChangedSignal = Gaffer::Signals::Signal<void (PaintTool &), Gaffer::Signals::CatchingCombiner<void> >;
		StatusChangedSignal &statusChangedSignal();

		void paint( const IECore::InternedString &variableName, const Imath::M44f &projectionMatrix, const std::variant<float, Imath::Color3f> &value, float opacity, float hardness, PaintMode mode );

		void applyCurrentStroke();

		IECore::CompoundDataPtr targetVariableTypes();

		using ColorChooserFunction = std::function<void ( Gaffer::PlugPtr )>;

		static void registerColorChooserFunction( ColorChooserFunction f );

	protected :

		/// The scene being edited.
		GafferScene::ScenePlug *scenePlug();
		const GafferScene::ScenePlug *scenePlug() const;

		std::string undoMergeGroup() const;

	private :

		IE_CORE_FORWARDDECLARE( PaintGadget );
		IE_CORE_FORWARDDECLARE( BrushOutline );

		PaintGadget *paintGadget();

		class LocationCache;
		using LocationCacheVector = std::vector<std::unique_ptr<LocationCache> >;

		LocationCacheVector &locationCaches();

		// \todo : This is a weird API ... the const version is only valid to call if the
		// non-const version was previously called. Not sure the right solution. Give this
		// function a weird name to reflect its weird purpose? Or make everything involved
		// with the location caches mutable?
		const LocationCacheVector &locationCaches() const;

		void inspectorDirtied();

		void contextChanged();
		void selectedPathsChanged();
		void plugDirtied( const Gaffer::Plug *plug );
		void metadataChanged( IECore::InternedString key );

		void preRender();

		bool enter( const GafferUI::ButtonEvent &event );
		bool leave( const GafferUI::ButtonEvent &event );
		bool mouseMove( const GafferUI::ButtonEvent &event );
		bool buttonPress( const GafferUI::ButtonEvent &event );
		bool buttonRelease( const GafferUI::ButtonEvent &event );
		bool keyPress( const GafferUI::KeyEvent &event );
		bool keyRelease( const GafferUI::KeyEvent &event );
		IECore::RunTimeTypedPtr dragBegin( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event );
		bool dragEnter( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event );
		bool dragMove( const GafferUI::DragDropEvent &event );
		bool dragEnd( const GafferUI::DragDropEvent &event );

		void updateCursor();

		Gaffer::Signals::ScopedConnection m_preRenderConnection;

		PaintGadgetPtr m_gadget;

		LocationCacheVector m_locationCaches;
		bool m_selectionDirty;
		bool m_locationCachesDirty;
		StatusChangedSignal m_statusChangedSignal;

		std::unordered_set< std::string > m_warnings;

		Imath::V2f m_dragPosition;
		bool m_buttonPressIsOurs;
		int m_mergeGroupId;

		std::unique_ptr<DepthRender> m_depthRender;

		BrushOutlinePtr m_brushOutline;

		bool m_mouseIn;
		GafferUI::ModifiableEvent::Modifiers m_eventModifiers;
		GafferUI::ButtonEvent::Buttons m_eventButtons;

		enum class MouseMoveMode
		{
			Default,
			Size,
			Opacity,
			Hardness

		};
		MouseMoveMode m_mouseMoveMode;
		float m_mouseMoveStartValue;
		Imath::V2f m_cursorPos;

		GafferSceneUI::Private::PrimitiveVariableInspectorPtr m_inspector;

		static ToolDescription<PaintTool, SceneView> g_toolDescription;
		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( PaintTool )

} // namespace GafferSceneUI
