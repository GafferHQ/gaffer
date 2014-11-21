//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERSCENEUI_SCENEGADGET_H
#define GAFFERSCENEUI_SCENEGADGET_H

#include "IECoreGL/State.h"

#include "Gaffer/Context.h"

#include "GafferUI/Gadget.h"

#include "GafferScene/ScenePlug.h"
#include "GafferScene/PathMatcherData.h"

#include "GafferSceneUI/TypeIds.h"

namespace GafferSceneUI
{

IE_CORE_FORWARDDECLARE( SceneGadget );

class SceneGadget : public GafferUI::Gadget
{

	public :

		SceneGadget();
		virtual ~SceneGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferSceneUI::SceneGadget, SceneGadgetTypeId, Gadget );

		virtual Imath::Box3f bound() const;

		void setScene( GafferScene::ConstScenePlugPtr scene );
		const GafferScene::ScenePlug *getScene() const;

		void setContext( Gaffer::ContextPtr context );
		Gaffer::Context *getContext();
		const Gaffer::Context *getContext() const;

		/// Limits the expanded parts of the scene to those in the specified paths.
		/// Without this, the whole scene is shown. A copy is not taken, but the
		/// SceneGadget will not modify the expanded paths.
		void setExpandedPaths( GafferScene::ConstPathMatcherDataPtr expandedPaths );
		const GafferScene::PathMatcherData *getExpandedPaths() const;

		void setMinimumExpansionDepth( size_t depth );
		size_t getMinimumExpansionDepth() const;

		/// Returns the IECoreGL::State object used as the base display
		/// style for the Renderable. This may be modified freely to
		/// change the display style.
		IECoreGL::State *baseState();

		/// Finds the path of the frontmost object intersecting the specified line
		/// through gadget space. Returns true on success and false if there is no
		/// such object.
		bool objectAt( const IECore::LineSegment3f &lineInGadgetSpace, GafferScene::ScenePlug::ScenePath &path ) const;
		/// Fills paths with all objects intersected by a rectangle in screen space,
		/// defined by two corners in gadget space (as required for drag selection).
		size_t objectsAt(
			const Imath::V3f &corner0InGadgetSpace,
			const Imath::V3f &corner1InGadgetSpace,
			GafferScene::PathMatcher &paths
		) const;

		/// Returns the selection.
		const GafferScene::PathMatcherData *getSelection() const;
		/// Sets the selection. A copy is not taken, but the selection
		/// is const and will not be modified by the SceneGadget.
		void setSelection( GafferScene::ConstPathMatcherDataPtr selection );
		/// Returns the bounding box of all the selected objects.
		Imath::Box3f selectionBound() const;

		/// Implemented to return the name of the object under the mouse.
		virtual std::string getToolTip( const IECore::LineSegment3f &line ) const;

	protected :

		virtual void doRender( const GafferUI::Style *style ) const;

	private :

		void plugDirtied( const Gaffer::Plug *plug );
		void contextChanged( const IECore::InternedString &name );
		void updateSceneGraph() const;
		void renderSceneGraph( const IECoreGL::State *stateToBind ) const;

		boost::signals::scoped_connection m_plugDirtiedConnection;
		boost::signals::scoped_connection m_contextChangedConnection;

		GafferScene::ConstScenePlugPtr m_scene;
		Gaffer::ContextPtr m_context;
		mutable unsigned m_dirtyFlags;
		GafferScene::ConstPathMatcherDataPtr m_expandedPaths;
		size_t m_minimumExpansionDepth;

		class SceneGraph;
		class UpdateTask;

		IECoreGL::StatePtr m_baseState;
		boost::shared_ptr<SceneGraph> m_sceneGraph;

		GafferScene::ConstPathMatcherDataPtr m_selection;

};

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<SceneGadget> > SceneGadgetIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<SceneGadget> > RecursiveSceneGadgetIterator;

} // namespace GafferUI

#endif // GAFFERSCENEUI_SCENEGADGET_H
