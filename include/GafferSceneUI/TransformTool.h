//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014-2016, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENEUI_TRANSFORMTOOL_H
#define GAFFERSCENEUI_TRANSFORMTOOL_H

#include "GafferSceneUI/SelectionTool.h"
#include "GafferSceneUI/TypeIds.h"

#include "GafferScene/EditScopeAlgo.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePlug.h"

#include "GafferUI/KeyEvent.h"

#include "Gaffer/EditScope.h"
#include "Gaffer/TransformPlug.h"

namespace GafferSceneUI
{

IE_CORE_FORWARDDECLARE( SceneView )

class GAFFERSCENEUI_API TransformTool : public GafferSceneUI::SelectionTool
{

	public :

		~TransformTool() override;

		GAFFER_NODE_DECLARE_TYPE( GafferSceneUI::TransformTool, TransformToolTypeId, SelectionTool );

		enum Orientation
		{
			Local,
			Parent,
			World
		};

		Gaffer::FloatPlug *sizePlug();
		const Gaffer::FloatPlug *sizePlug() const;

		struct Selection
		{

			// Constructs an empty selection.
			Selection();

			// Constructs a selection for the specified
			// viewed scene.
			Selection(
				const GafferScene::ConstScenePlugPtr scene,
				const GafferScene::ScenePlug::ScenePath &path,
				const Gaffer::ConstContextPtr &context,
				const Gaffer::EditScopePtr &editScope
			);

			/// Viewed scene
			/// ============
			///
			/// The scene being viewed.
			const GafferScene::ScenePlug *scene() const;
			/// The location within the viewed scene that is being
			/// edited.
			const GafferScene::ScenePlug::ScenePath &path() const;
			/// The context the scene is being viewed in.
			const Gaffer::Context *context() const;

			/// Upstream scene
			/// ==============
			///
			/// Often, the scene being viewed isn't actually the
			/// scene where the transform originates. Instead, the
			/// transform originates with an upstream node, and the
			/// user is viewing a downstream node to see the transform
			/// in the context of later changes. The `upstreamScene`
			/// is the output from the node where the transform
			/// originates.
			const GafferScene::ScenePlug *upstreamScene() const;
			/// The hierarchies of the upstream and viewed scenes may
			/// differ. The upstreamPath is the equivalent of
			/// the viewed path but in the upstream scene.
			const GafferScene::ScenePlug::ScenePath &upstreamPath() const;
			/// The upstream context is the equivalent of the
			/// viewed context, but for the upstream scene.
			const Gaffer::Context *upstreamContext() const;

			/// Status and editing
			/// ==================

			/// Returns true if the selected transform may be edited
			/// using `acquireTransformEdit()` and `transformSpace()`.
			bool editable() const;
			/// Returns a warning message, or "" if there are no
			/// warnings.
			const std::string &warning() const;

			using TransformEdit = GafferScene::EditScopeAlgo::TransformEdit;
			/// Returns the plugs to edit. Throws if `status() != Editable`.
			/// > Caution : When using EditScopes, this may edit the graph
			/// > to create the plug unless `createIfNecessary == false`.
			boost::optional<TransformEdit> acquireTransformEdit( bool createIfNecessary = true ) const;
			/// The EditScope passed to the constructor.
			const Gaffer::EditScope *editScope() const;
			/// Returns the GraphComponent that will be edited.
			/// Unlike `acquireTransformEdit()`, this never edits the graph,
			/// instead returning an `EditScope *` if an EditScope
			/// is in use but no TransformEdit has been created yet.
			/// Throws if `status() != Editable`.
			Gaffer::GraphComponent *editTarget() const;
			/// Returns the coordinate system within which the
			/// transform is applied by the upstream node.
			/// This is relative to the world space of the
			/// upstream scene. Throws if `!editable()`.
			const Imath::M44f &transformSpace() const;

			/// Utilities
			/// =========
			///
			/// Returns the equivalent of `acquireTransformEdit()->matrix()` and
			/// fills `translate`, `rotate`, `scale` and `pivot` with values
			/// for each component of the edit.
			/// Throws if `status() != Editable`.
			/// > Note : Where a TransformEdit has not yet been created for
			/// > an EditScope, this will return the values that it will
			/// > be given upon creation. It will never modify the graph.
			Imath::M44f transform( Imath::V3f &translate, Imath::V3f &rotate, Imath::V3f &scale, Imath::V3f &pivot ) const;
			/// Returns a matrix which converts from world
			/// space in `scene` to `transformSpace`.
			/// Throws if `!editable()`.
			Imath::M44f sceneToTransformSpace() const;
			/// Returns a matrix suitable for positioning
			/// transform handles in `scene's` world space.
			/// Throws if `!editable()`.
			Imath::M44f orientedTransform( Orientation orientation ) const;

			private :

				void initFromSceneNode( const GafferScene::SceneAlgo::History *history );
				void initWalk( const GafferScene::SceneAlgo::History *history, bool &editScopeFound );
				void throwIfNotEditable() const;
				Imath::M44f transformToLocalSpace() const;

				GafferScene::ConstScenePlugPtr m_scene;
				GafferScene::ScenePlug::ScenePath m_path;
				Gaffer::ConstContextPtr m_context;

				GafferScene::ConstScenePlugPtr m_upstreamScene;
				GafferScene::ScenePlug::ScenePath m_upstreamPath;
				Gaffer::ConstContextPtr m_upstreamContext;

				bool m_editable;
				std::string m_warning;
				Gaffer::EditScopePtr m_editScope;
				mutable boost::optional<TransformEdit> m_transformEdit;
				Imath::M44f m_transformSpace;
				bool m_aimConstraint;

		};

		/// Returns the current selection.
		const std::vector<Selection> &selection() const;
		/// Returns true only if the selection is non-empty
		/// and every item is editable.
		bool selectionEditable() const;

		using SelectionChangedSignal = boost::signal<void (TransformTool &)>;
		SelectionChangedSignal &selectionChangedSignal();

		/// Returns the transform of the handles. Throws
		/// if the selection is invalid because then the
		/// transform would be meaningless. This is
		/// exposed primarily for the unit tests.
		Imath::M44f handlesTransform();

	protected :

		TransformTool( SceneView *view, const std::string &name );

		/// The scene being edited.
		GafferScene::ScenePlug *scenePlug();
		const GafferScene::ScenePlug *scenePlug() const;

		/// Gadget under which derived classes
		/// should parent their handles.
		GafferUI::Gadget *handles();
		const GafferUI::Gadget *handles() const;

		/// Must be implemented by derived classes to return true if
		/// the input plug is used in updateHandles(). Implementation
		/// must call the base class implementation first, returning true
		/// if it does.
		virtual bool affectsHandles( const Gaffer::Plug *input ) const = 0;
		/// Must be implemented by derived classes to update the
		/// handles appropriately. Typically this means setting their
		/// transform and matching their enabled state to the editability
		/// of the selection.
		virtual void updateHandles( float rasterScale ) = 0;

		/// Must be called by derived classes when they begin
		/// a drag.
		void dragBegin();
		/// Must be called by derived classes when they end
		/// a drag.
		void dragEnd();
		/// Should be used in UndoScopes created by
		/// derived classes.
		std::string undoMergeGroup() const;

		/// Utilities to help derived classes update plug values.
		static bool canSetValueOrAddKey( const Gaffer::FloatPlug *plug );
		static void setValueOrAddKey( Gaffer::FloatPlug *plug, float time, float value );

	private :

		void connectToViewContext();
		void contextChanged( const IECore::InternedString &name );
		void plugDirtied( const Gaffer::Plug *plug );
		void metadataChanged( IECore::InternedString key );
		void updateSelection() const;
		void preRender();
		bool keyPress( const GafferUI::KeyEvent &event );

		boost::signals::scoped_connection m_contextChangedConnection;
		boost::signals::scoped_connection m_preRenderConnection;

		GafferUI::GadgetPtr m_handles;
		bool m_handlesDirty;

		mutable std::vector<Selection> m_selection;
		mutable bool m_selectionDirty;
		bool m_priorityPathsDirty;
		SelectionChangedSignal m_selectionChangedSignal;

		bool m_dragging;
		int m_mergeGroupId;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( TransformTool )

} // namespace GafferSceneUI

#endif // GAFFERSCENEUI_TRANSFORMTOOL_H
