//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2014, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERSCENEUI_SCENEVIEW_H
#define GAFFERSCENEUI_SCENEVIEW_H

#include "GafferUI/View3D.h"

#include "GafferScene/ScenePlug.h"
#include "GafferScene/PathMatcherData.h"
#include "GafferScene/PathFilter.h"

#include "GafferSceneUI/TypeIds.h"
#include "GafferSceneUI/SceneGadget.h"

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( SceneProcessor )

} // namespace GafferScene

namespace GafferSceneUI
{

/// \todo As we add more features to the View classes, they're feeling a
/// bit monolithic, and not in the modular "plug it together how you like"
/// spirit of the rest of Gaffer. Internally the various features are implemented
/// as their own little classes though, so perhaps it would make sense to expose
/// these in the public API as optional "bolt on" components that applications can
/// use as they see fit. If we do this, we need to consider how these relate to
/// Tools, which could also be seen as viewer components.
class SceneView : public GafferUI::View3D
{

	public :

		SceneView( const std::string &name = defaultName<SceneView>() );
		virtual ~SceneView();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferSceneUI::SceneView, SceneViewTypeId, GafferUI::View3D );

		Gaffer::IntPlug *minimumExpansionDepthPlug();
		const Gaffer::IntPlug *minimumExpansionDepthPlug() const;

		Gaffer::ValuePlug *lookThroughPlug();
		const Gaffer::ValuePlug *lookThroughPlug() const;

		Gaffer::ValuePlug *gridPlug();
		const Gaffer::ValuePlug *gridPlug() const;

		Gaffer::ValuePlug *gnomonPlug();
		const Gaffer::ValuePlug *gnomonPlug() const;

		void expandSelection( size_t depth = 1 );
		void collapseSelection();

		virtual void setContext( Gaffer::ContextPtr context );

		/// If the view is locked to a particular camera,
		/// this returns the bound of the resolution gate
		/// in raster space - this can be useful when
		/// drawing additional overlays. If the view is not
		/// locked to a particular camera then returns an
		/// empty bound.
		const Imath::Box2f &resolutionGate() const;

		typedef boost::function<GafferScene::SceneProcessorPtr ()> ShadingModeCreator;

		static void registerShadingMode( const std::string &name, ShadingModeCreator );
		static void registeredShadingModes( std::vector<std::string> &names );

	protected :

		virtual void contextChanged( const IECore::InternedString &name );
		virtual Imath::Box3f framingBound() const;

	private :

		// The filter for a preprocessing node used to hide things.
		GafferScene::PathFilter *hideFilter();
		const GafferScene::PathFilter *hideFilter() const;

		bool keyPress( GafferUI::GadgetPtr gadget, const GafferUI::KeyEvent &event );
		void transferSelectionToContext();
		void plugSet( Gaffer::Plug *plug );

		GafferScene::PathMatcherData *expandedPaths();
		// Returns true if the expansion or selection were modified, false otherwise.
		bool expandWalk( const GafferScene::ScenePlug::ScenePath &path, size_t depth, GafferScene::PathMatcher &expanded, GafferScene::PathMatcher &selected );

		boost::signals::scoped_connection m_selectionChangedConnection;

		void baseStateChanged();

		SceneGadgetPtr m_sceneGadget;

		class LookThrough;
		boost::shared_ptr<LookThrough> m_lookThrough;
		class Grid;
		boost::shared_ptr<Grid> m_grid;
		class Gnomon;
		boost::shared_ptr<Gnomon> m_gnomon;
		class ShadingMode;
		boost::shared_ptr<ShadingMode> m_shadingMode;

		static size_t g_firstPlugIndex;
		static ViewDescription<SceneView> g_viewDescription;

};

IE_CORE_DECLAREPTR( SceneView );

} // namespace GafferSceneUI

#endif // GAFFERSCENEUI_SCENEVIEW_H
