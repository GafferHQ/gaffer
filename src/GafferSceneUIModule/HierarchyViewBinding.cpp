//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "boost/python.hpp"

#include "HierarchyViewBinding.h"

#include "GafferSceneUI/ContextAlgo.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePath.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/VisibleSet.h"

#include "GafferUI/PathColumn.h"

#include "Gaffer/Context.h"
#include "Gaffer/Path.h"
#include "Gaffer/PathFilter.h"

#include "IECorePython/RefCountedBinding.h"

#include "IECore/StringAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/python/suite/indexing/container_utils.hpp"

using namespace std;
using namespace boost::python;
using namespace IECore;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

namespace
{

//////////////////////////////////////////////////////////////////////////
// HierarchyViewFilter - base class for PathFilters which need a scene
// and a context. Designed for internal use in the HierarchyView.
//
// \todo The "track dirtiness from a context and plug" behaviour implemented
// here is common across many UI elements - perhaps it could be encapsulated
// in a utility class at some point?
// \todo Consider making these filters part of the public API at some point,
// and also allowing the HierarchyView widget to be customised with
// custom filters.
//////////////////////////////////////////////////////////////////////////

class HierarchyViewFilter : public Gaffer::PathFilter
{

	public :

		IE_CORE_DECLAREMEMBERPTR( HierarchyViewFilter )

		HierarchyViewFilter( IECore::CompoundDataPtr userData = nullptr )
			:	PathFilter( userData ), m_context( new Context )
		{
		}

		void setScene( ConstScenePlugPtr scene )
		{
			if( scene == m_scene )
			{
				return;
			}
			m_scene = scene;
			Node *node = nullptr;
			if( m_scene )
			{
				node = const_cast<Node *>( m_scene->node() );
				for( ValuePlug::Iterator it( m_scene.get() ); !it.done(); ++it )
				{
					sceneDirtied( it->get() );
				}
			}
			if( node )
			{
				m_plugDirtiedConnection = node->plugDirtiedSignal().connect(
					boost::bind( &HierarchyViewFilter::plugDirtied, this, ::_1 )
				);
			}
			else
			{
				m_plugDirtiedConnection.disconnect();
			}
		}

		const ScenePlug *getScene() const
		{
			return m_scene.get();
		}

		void setContext( Gaffer::ContextPtr context )
		{
			if( context == m_context )
			{
				return;
			}
			ConstContextPtr oldContext = m_context;
			m_context = context;
			if( m_context )
			{
				m_contextChangedConnection = const_cast<Context *>( m_context.get() )->changedSignal().connect(
					boost::bind( &HierarchyViewFilter::contextChanged, this, ::_2 )
				);
			}
			else
			{
				m_contextChangedConnection.disconnect();
			}

			// Give derived classes a chance to react to the changes
			// between the old and new contexts. First compare all the
			// variables in the new context with their equivalents in
			// the old.
			vector<InternedString> names;
			m_context->names( names );
			for( vector<InternedString>::const_iterator it = names.begin(), eIt = names.end(); it != eIt; ++it )
			{
				IECore::DataPtr newValue = m_context->getAsData( *it );
				IECore::DataPtr oldValue = oldContext->getAsData( *it, nullptr );
				if( !oldValue || !newValue->isEqualTo( oldValue.get() ) )
				{
					contextChanged( *it );
				}
			}
			// Next see if any variables from the old context are not
			// present in the new one, and signal for those too.
			names.clear();
			oldContext->names( names );
			for( vector<InternedString>::const_iterator it = names.begin(), eIt = names.end(); it != eIt; ++it )
			{
				if( !m_context->getAsData( *it, nullptr ) )
				{
					contextChanged( *it );
				}
			}
		}

		const Gaffer::Context *getContext() const
		{
			return m_context.get();
		}

	protected :

		// May be implemented by derived classes to be notified
		// when a part of the scene has been dirtied.
		virtual void sceneDirtied( const ValuePlug *child )
		{
		}

		// May be implemented by derived classes to be notified
		// when the context has changed.
		virtual void contextChanged( const IECore::InternedString &variableName )
		{
		}

	private :

		void plugDirtied( const Plug *plug )
		{
			if( plug->parent<ScenePlug>() == m_scene )
			{
				sceneDirtied( static_cast<const ValuePlug *>( plug ) );
			}
		}

		ConstScenePlugPtr m_scene;
		ConstContextPtr m_context;

		Signals::ScopedConnection m_plugDirtiedConnection;
		Signals::ScopedConnection m_contextChangedConnection;

};

// Wrapper functions

ScenePlugPtr getScene( HierarchyViewFilter &f )
{
	return const_cast<ScenePlug *>( f.getScene() );
}

ContextPtr getContext( HierarchyViewFilter &f )
{
	return const_cast<Context *>( f.getContext() );
}

//////////////////////////////////////////////////////////////////////////
// HierarchyViewSetFilter - filters based on membership in a
// list of sets.
//////////////////////////////////////////////////////////////////////////

class HierarchyViewSetFilter : public HierarchyViewFilter
{

	public :

		IE_CORE_DECLAREMEMBERPTR( HierarchyViewSetFilter )

		HierarchyViewSetFilter( IECore::CompoundDataPtr userData = nullptr )
			:	HierarchyViewFilter( userData ), m_setsDirty( true )
		{
		}

		void setSetNames( const vector<InternedString> &setNames )
		{
			if( m_setNames == setNames )
			{
				return;
			}
			m_setNames = setNames;
			m_setsDirty = true;
			changedSignal()( this );
		}

		const vector<InternedString> &getSetNames() const
		{
			return m_setNames;
		}

	protected :

		void sceneDirtied( const ValuePlug *child ) override
		{
			if(
				child == getScene()->setNamesPlug() ||
				child == getScene()->setPlug()
			)
			{
				m_setsDirty = true;
				changedSignal()( this );
			}
		}

		void contextChanged( const IECore::InternedString &variableName ) override
		{
			if( !boost::starts_with( variableName.c_str(), "ui:" ) )
			{
				m_setsDirty = true;
				changedSignal()( this );
			}
		}

		void doFilter( vector<Gaffer::PathPtr> &paths, const IECore::Canceller *canceller ) const override
		{
			if( paths.empty() )
			{
				return;
			}

			updateSets();

			paths.erase(
				remove_if(
					paths.begin(),
					paths.end(),
					boost::bind( &HierarchyViewSetFilter::remove, this, ::_1 )
				),
				paths.end()
			);
		}

	private :

		bool remove( const Gaffer::PathPtr &path ) const
		{
			for( vector<PathMatcher>::const_iterator it = m_sets.begin(), eIt = m_sets.end(); it != eIt; ++it )
			{
				if( it->match( path->names() ) )
				{
					return false;
				}
			}
			return true;
		}

		void updateSets() const
		{
			if( !m_setsDirty )
			{
				return;
			}

			m_sets.clear();
			if( !getScene() || !getContext() )
			{
				return;
			}

			Context::Scope scopedContext( getContext() );
			for( vector<InternedString>::const_iterator it = m_setNames.begin(), eIt = m_setNames.end(); it != eIt; ++it )
			{
				try
				{
					ConstPathMatcherDataPtr set = getScene()->set( *it );
					m_sets.push_back( set->readable() );
				}
				catch( ... )
				{
					// We can leave it to the other UI elements to report the error.
				}
			}
			m_setsDirty = false;
		}

		vector<InternedString> m_setNames;
		mutable bool m_setsDirty;
		mutable vector<PathMatcher> m_sets;

};

// Wrapper functions

void setSetNames( HierarchyViewSetFilter &f, object pythonSetNames )
{
	std::vector<InternedString> setNames;
	boost::python::container_utils::extend_container( setNames, pythonSetNames );
	f.setSetNames( setNames );
}

boost::python::list getSetNames( HierarchyViewSetFilter &f )
{
	boost::python::list result;
	const std::vector<InternedString> &s = f.getSetNames();
	for( std::vector<InternedString>::const_iterator it = s.begin(), eIt = s.end(); it != eIt; ++it )
	{
		result.append( it->string() );
	}
	return result;
}

//////////////////////////////////////////////////////////////////////////
// HierarchyViewSearchFilter - filters based on a match pattern. This
// is different from MatchPatternPathFilter, because it performs a full
// search of the entire scene, whereas MatchPatternPathFilter can only
// match against leaf paths.
//////////////////////////////////////////////////////////////////////////

class HierarchyViewSearchFilter : public HierarchyViewFilter
{

	public :

		IE_CORE_DECLAREMEMBERPTR( HierarchyViewSearchFilter )

		HierarchyViewSearchFilter( IECore::CompoundDataPtr userData = nullptr )
			:	HierarchyViewFilter( userData ), m_pathMatcherDirty( true )
		{
		}

		void setMatchPattern( const string &matchPattern )
		{
			if( m_matchPattern == matchPattern )
			{
				return;
			}
			m_matchPattern = matchPattern;
			m_pathMatcherDirty = true;
			changedSignal()( this );
		}

		const string &getMatchPattern() const
		{
			return m_matchPattern;
		}

	protected :

		void sceneDirtied( const ValuePlug *child ) override
		{
			if( child == getScene()->childNamesPlug() )
			{
				m_pathMatcherDirty = true;
				changedSignal()( this );
			}
		}

		void contextChanged( const IECore::InternedString &variableName ) override
		{
			if( !boost::starts_with( variableName.c_str(), "ui:" ) )
			{
				m_pathMatcherDirty = true;
				changedSignal()( this );
			}
		}

		void doFilter( vector<Gaffer::PathPtr> &paths, const IECore::Canceller *canceller ) const override
		{
			if( m_matchPattern.empty() || paths.empty() )
			{
				return;
			}

			updatePathMatcher();

			paths.erase(
				remove_if(
					paths.begin(),
					paths.end(),
					boost::bind( &HierarchyViewSearchFilter::remove, this, ::_1 )
				),
				paths.end()
			);
		}

	private :

		bool remove( const Gaffer::PathPtr &path ) const
		{
			return !m_pathMatcher.match( path->names() );
		}

		void updatePathMatcher() const
		{
			if( !m_pathMatcherDirty )
			{
				return;
			}

			PathMatcher toMatch;
			if( m_matchPattern.find( '/' ) != string::npos )
			{
				// The user has entered a full match path.
				toMatch.addPath( m_matchPattern );
			}
			else if( StringAlgo::hasWildcards( m_matchPattern ) )
			{
				// The user has used some wildcards, we
				// just need to make sure the pattern is
				// searched for everywhere.
				toMatch.addPath( "/.../" + m_matchPattern );
			}
			else
			{
				// The user hasn't used wildcards - add some to
				// help find a match.
				toMatch.addPath( "/.../*" + m_matchPattern + "*" );
			}

			// Here we literally have to search the entire scene
			// to find matches wherever they may be. We're at the
			// mercy of SceneAlgo::matchingPaths() and just have to
			// hope that it can do things quickly enough.
			m_pathMatcher.clear();
			try
			{
				SceneAlgo::matchingPaths( toMatch, getScene(), m_pathMatcher );
			}
			catch( ... )
			{
				// We can leave it to the other UI elements to report the error.
			}

			m_pathMatcherDirty = false;
		}

		std::string m_matchPattern;
		mutable bool m_pathMatcherDirty;
		mutable PathMatcher m_pathMatcher;

};

//////////////////////////////////////////////////////////////////////////
// InclusionsColumn - displays and modifies inclusions membership of the
// VisibleSet in the provided context.
//////////////////////////////////////////////////////////////////////////

class InclusionsColumn : public PathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( InclusionsColumn )

		InclusionsColumn( ContextPtr context )
			:	PathColumn(), m_context( context )
		{
			buttonPressSignal().connect( boost::bind( &InclusionsColumn::buttonPress, this, ::_3 ) );
			buttonReleaseSignal().connect( boost::bind( &InclusionsColumn::buttonRelease, this, ::_1, ::_2, ::_3 ) );
			m_context->changedSignal().connect( boost::bind( &InclusionsColumn::contextChanged, this, ::_2 ) );
		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override
		{
			CellData result;

			auto scenePath = IECore::runTimeCast<const ScenePath>( &path );
			if( !scenePath )
			{
				return result;
			}

			Context::EditableScope scope( m_context.get() );
			scope.setCanceller( canceller );

			if( scenePath->getScene()->childNames( scenePath->names() )->readable().empty() )
			{
				// To limit the amount of duplicate information presented we don't provide custom cellData to leaf locations
				return result;
			}

			const auto visibleSet = ContextAlgo::getVisibleSet( m_context.get() );
			const auto inclusionsMatch = visibleSet.inclusions.match( scenePath->names() );
			const auto locationExcluded = visibleSet.exclusions.match( scenePath->names() ) & (IECore::PathMatcher::Result::ExactMatch | IECore::PathMatcher::Result::AncestorMatch);

			auto iconData = new CompoundData;
			iconData->writable()["state:highlighted"] = g_locationIncludedHighlightedTransparentIconName;
			result.icon = iconData;

			if( !locationExcluded )
			{
				if( inclusionsMatch & IECore::PathMatcher::Result::ExactMatch )
				{
					iconData->writable()["state:highlighted"] = g_locationIncludedHighlightedIconName;
					iconData->writable()["state:normal"] = g_locationIncludedIconName;
					result.toolTip = g_locationIncludedToolTip;
				}
				else if( inclusionsMatch & IECore::PathMatcher::Result::AncestorMatch )
				{
					iconData->writable()["state:normal"] = g_ancestorIncludedIconName;
					result.toolTip = g_ancestorIncludedToolTip;
				}
				else if( inclusionsMatch & IECore::PathMatcher::Result::DescendantMatch )
				{
					iconData->writable()["state:normal"] =  g_descendantIncludedIconName;
					result.toolTip = g_descendantIncludedToolTip;
				}
				else if( visibleSet.expansions.match( scenePath->names() ) & IECore::PathMatcher::Result::ExactMatch )
				{
					iconData->writable()["state:normal"] = g_locationExpandedIconName;
					result.toolTip = g_locationExpandedToolTip;
				}
				else
				{
					result.toolTip = g_inclusionToolTip;
				}
			}
			else
			{
				if( inclusionsMatch & IECore::PathMatcher::Result::ExactMatch )
				{
					iconData->writable()["state:highlighted"] = g_locationIncludedHighlightedIconName;
					iconData->writable()["state:normal"] = g_locationIncludedDisabledIconName;
					result.toolTip = g_locationIncludedOverrideToolTip;
				}
				else if( inclusionsMatch & IECore::PathMatcher::Result::DescendantMatch )
				{
					iconData->writable()["state:normal"] = g_descendantIncludedTransparentIconName;
					result.toolTip = g_descendantIncludedOverrideToolTip;
				}
				else
				{
					result.toolTip = g_inclusionOverrideToolTip;
				}
			}

			return result;
		}

		CellData headerData( const IECore::Canceller *canceller ) const override
		{
			return CellData( /* value = */ nullptr, /* icon = */ g_locationIncludedIconName, /* background = */ nullptr, /* tooltip = */ new StringData( "Visible Set Inclusions" ) );
		}

	private :

		void contextChanged( const IECore::InternedString &name )
		{
			if( ContextAlgo::affectsVisibleSet( name ) )
			{
				changedSignal()( this );
			}
		}

		bool buttonPress( const ButtonEvent &event )
		{
			if( event.buttons != ButtonEvent::Left )
			{
				return false;
			}

			return true;
		}

		bool buttonRelease( const Gaffer::Path &path, const GafferUI::PathListingWidget &widget, const ButtonEvent &event )
		{
			auto scenePath = IECore::runTimeCast<const ScenePath>( &path );
			if( !scenePath )
			{
				return false;
			}

			Context::EditableScope scope( m_context.get() );

			if( scenePath->getScene()->childNames( scenePath->names() )->readable().empty() )
			{
				// Leaf locations are not treated as clickable, user interaction should occur at the parent location
				return false;
			}

			auto paths = IECore::PathMatcher();
			paths.addPath( scenePath->names() );
			const auto selection = widget.getSelection();
			if( std::holds_alternative<IECore::PathMatcher>( selection ) )
			{
				// Permit bulk editing of a selection of paths when clicking on one of the selected paths
				const auto selectedPaths = std::get<IECore::PathMatcher>( selection );
				if( selectedPaths.match( scenePath->names() ) & IECore::PathMatcher::Result::ExactMatch )
				{
					paths = selectedPaths;
				}
			}

			bool update = false;
			auto visibleSet = ContextAlgo::getVisibleSet( m_context.get() );
			if( event.button == ButtonEvent::Left && !event.modifiers )
			{
				if( visibleSet.inclusions.match( scenePath->names() ) & IECore::PathMatcher::Result::ExactMatch )
				{
					update = visibleSet.inclusions.removePaths( paths );
				}
				else
				{
					update = visibleSet.inclusions.addPaths( paths );
				}
			}
			else if( event.button == ButtonEvent::Left && event.modifiers == ButtonEvent::Modifiers::Shift )
			{
				for( IECore::PathMatcher::Iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
				{
					update |= visibleSet.inclusions.prune( *it );
				}
			}

			if( update )
			{
				ContextAlgo::setVisibleSet( m_context.get(), visibleSet );
			}

			return true;
		}

		ContextPtr m_context;

		static IECore::StringDataPtr g_descendantIncludedIconName;
		static IECore::StringDataPtr g_descendantIncludedTransparentIconName;
		static IECore::StringDataPtr g_locationExpandedIconName;
		static IECore::StringDataPtr g_locationIncludedIconName;
		static IECore::StringDataPtr g_locationIncludedDisabledIconName;
		static IECore::StringDataPtr g_ancestorIncludedIconName;
		static IECore::StringDataPtr g_locationIncludedHighlightedIconName;
		static IECore::StringDataPtr g_locationIncludedHighlightedTransparentIconName;

		static IECore::StringDataPtr g_inclusionToolTip;
		static IECore::StringDataPtr g_inclusionOverrideToolTip;
		static IECore::StringDataPtr g_locationExpandedToolTip;
		static IECore::StringDataPtr g_locationIncludedToolTip;
		static IECore::StringDataPtr g_locationIncludedOverrideToolTip;
		static IECore::StringDataPtr g_ancestorIncludedToolTip;
		static IECore::StringDataPtr g_descendantIncludedToolTip;
		static IECore::StringDataPtr g_descendantIncludedOverrideToolTip;

};

StringDataPtr InclusionsColumn::g_descendantIncludedIconName = new StringData( "descendantIncluded.png" );
StringDataPtr InclusionsColumn::g_descendantIncludedTransparentIconName = new StringData( "descendantIncludedTransparent.png" );
StringDataPtr InclusionsColumn::g_locationExpandedIconName = new StringData( "locationExpanded.png" );
StringDataPtr InclusionsColumn::g_locationIncludedIconName = new StringData( "locationIncluded.png" );
StringDataPtr InclusionsColumn::g_locationIncludedDisabledIconName = new StringData( "locationIncludedDisabled.png" );
StringDataPtr InclusionsColumn::g_ancestorIncludedIconName = new StringData( "locationIncludedTransparent.png" );
StringDataPtr InclusionsColumn::g_locationIncludedHighlightedIconName = new StringData( "locationIncludedHighlighted.png" );
StringDataPtr InclusionsColumn::g_locationIncludedHighlightedTransparentIconName = new StringData( "locationIncludedHighlightedTransparent.png" );

StringDataPtr InclusionsColumn::g_inclusionToolTip = new StringData( "Click to include this branch in the Visible Set, causing it to always appear in Viewers." );
StringDataPtr InclusionsColumn::g_inclusionOverrideToolTip = new StringData(
	"Click to include this branch in the Visible Set, even though it will be overridden by an existing exclusion."
);
StringDataPtr InclusionsColumn::g_locationExpandedToolTip = new StringData(
	"Location expanded.\n\n"
	"Click to include this branch in the Visible Set, causing it to always appear in Viewers even if collapsed."
);
StringDataPtr InclusionsColumn::g_locationIncludedToolTip = new StringData(
	"This branch is in the Visible Set, causing it to always appear in Viewers.\n\n"
	"Click to remove from the Visible Set.\n"
	"Shift-click to remove all locations within this branch from the Visible Set."
);
StringDataPtr InclusionsColumn::g_locationIncludedOverrideToolTip = new StringData(
	"This branch is in the Visible Set, but isn't visible due to being overridden by an exclusion.\n\n"
	"Click to remove from the Visible Set.\n"
	"Shift-click to remove all locations within this branch from the Visible Set."
);
StringDataPtr InclusionsColumn::g_ancestorIncludedToolTip = new StringData(
	"An ancestor is in the Visible Set, causing this location and its descendants to always appear in Viewers.\n\n"
	"Click to also include this branch in the Visible Set.\n"
	"Shift-click to remove all locations within this branch from the Visible Set."
);
/// \todo Reword this once the RenderController is updated to allow for independent visibility of sibling locations.
StringDataPtr InclusionsColumn::g_descendantIncludedToolTip = new StringData(
	"One or more descendants are in the Visible Set, causing them to be visible even when this location is collapsed.\n\n"
	"Click to also include this branch in the Visible Set.\n"
	"Shift-click to remove all locations within this branch from the Visible Set."
);
StringDataPtr InclusionsColumn::g_descendantIncludedOverrideToolTip = new StringData(
	"One or more descendants are in the Visible Set, but they aren't visible due to this location being overridden by an exclusion.\n\n"
	"Click to include this branch in the Visible Set, even though it will also be overridden by an existing exclusion.\n"
	"Shift-click to remove all locations within this branch from the Visible Set."
);

//////////////////////////////////////////////////////////////////////////
// ExclusionsColumn - displays and modifies exclusions membership of the
// VisibleSet in the provided context.
//////////////////////////////////////////////////////////////////////////

class ExclusionsColumn : public PathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( ExclusionsColumn )

		ExclusionsColumn( ContextPtr context )
			:	PathColumn(), m_context( context )
		{
			buttonPressSignal().connect( boost::bind( &ExclusionsColumn::buttonPress, this, ::_3 ) );
			buttonReleaseSignal().connect( boost::bind( &ExclusionsColumn::buttonRelease, this, ::_1, ::_2, ::_3 ) );
			m_context->changedSignal().connect( boost::bind( &ExclusionsColumn::contextChanged, this, ::_2 ) );
		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override
		{
			CellData result;

			auto scenePath = IECore::runTimeCast<const ScenePath>( &path );
			if( !scenePath )
			{
				return result;
			}

			Context::EditableScope scope( m_context.get() );
			scope.setCanceller( canceller );

			if( scenePath->getScene()->childNames( scenePath->names() )->readable().empty() )
			{
				// To limit the amount of duplicate information presented we don't provide custom cellData to leaf locations
				return result;
			}

			auto visibleSet = ContextAlgo::getVisibleSet( m_context.get() );
			auto exclusionsMatch = visibleSet.exclusions.match( scenePath->names() );

			auto iconData = new CompoundData;
			iconData->writable()["state:highlighted"] = g_locationExcludedHighlightedTransparentIconName;
			result.icon = iconData;

			if( exclusionsMatch & IECore::PathMatcher::Result::ExactMatch )
			{
				iconData->writable()["state:highlighted"] = g_locationExcludedHighlightedIconName;
				iconData->writable()["state:normal"] = g_locationExcludedIconName;
				result.toolTip = g_locationExcludedToolTip;
			}
			else if( exclusionsMatch & IECore::PathMatcher::Result::AncestorMatch )
			{
				iconData->writable()["state:normal"] = g_ancestorExcludedIconName;
				result.toolTip = g_ancestorExcludedToolTip;
			}
			else if( exclusionsMatch & IECore::PathMatcher::Result::DescendantMatch )
			{
				iconData->writable()["state:normal"] = g_descendantExcludedIconName;
				result.toolTip = g_descendantExcludedToolTip;
			}
			else
			{
				result.toolTip = g_exclusionToolTip;
			}

			return result;
		}

		CellData headerData( const IECore::Canceller *canceller ) const override
		{
			return CellData( /* value = */ nullptr, /* icon = */ g_locationExcludedIconName, /* background = */ nullptr, /* tooltip = */ new StringData( "Visible Set Exclusions" ) );
		}

	private :

		void contextChanged( const IECore::InternedString &name )
		{
			if( ContextAlgo::affectsVisibleSet( name ) )
			{
				changedSignal()( this );
			}
		}

		bool buttonPress( const ButtonEvent &event )
		{
			if( event.buttons != ButtonEvent::Left )
			{
				return false;
			}

			return true;
		}

		bool buttonRelease( const Gaffer::Path &path, const GafferUI::PathListingWidget &widget, const ButtonEvent &event )
		{
			auto scenePath = IECore::runTimeCast<const ScenePath>( &path );
			if( !scenePath )
			{
				return false;
			}

			Context::EditableScope scope( m_context.get() );

			if( scenePath->getScene()->childNames( scenePath->names() )->readable().empty() )
			{
				// Leaf locations are not treated as clickable, user interaction should occur at the parent location
				return false;
			}

			auto paths = IECore::PathMatcher();
			paths.addPath( scenePath->names() );
			const auto selection = widget.getSelection();
			if( std::holds_alternative<IECore::PathMatcher>( selection ) )
			{
				// Permit bulk editing of a selection of paths when clicking on one of the selected paths
				const auto selectedPaths = std::get<IECore::PathMatcher>( selection );
				if( selectedPaths.match( scenePath->names() ) & IECore::PathMatcher::Result::ExactMatch )
				{
					paths = selectedPaths;
				}
			}

			bool update = false;
			auto visibleSet = ContextAlgo::getVisibleSet( m_context.get() );
			if( event.button == ButtonEvent::Left && !event.modifiers )
			{
				if( visibleSet.exclusions.match( scenePath->names() ) & IECore::PathMatcher::Result::ExactMatch )
				{
					update = visibleSet.exclusions.removePaths( paths );
				}
				else
				{
					update = visibleSet.exclusions.addPaths( paths );
				}
			}
			else if( event.button == ButtonEvent::Left && event.modifiers == ButtonEvent::Modifiers::Shift )
			{
				for( IECore::PathMatcher::Iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
				{
					update |= visibleSet.exclusions.prune( *it );
				}
			}

			if( update )
			{
				ContextAlgo::setVisibleSet( m_context.get(), visibleSet );
			}

			return true;
		}

		ContextPtr m_context;

		static IECore::StringDataPtr g_descendantExcludedIconName;
		static IECore::StringDataPtr g_locationExcludedIconName;
		static IECore::StringDataPtr g_ancestorExcludedIconName;
		static IECore::StringDataPtr g_locationExcludedHighlightedIconName;
		static IECore::StringDataPtr g_locationExcludedHighlightedTransparentIconName;

		static IECore::StringDataPtr g_exclusionToolTip;
		static IECore::StringDataPtr g_locationExcludedToolTip;
		static IECore::StringDataPtr g_ancestorExcludedToolTip;
		static IECore::StringDataPtr g_descendantExcludedToolTip;
};

StringDataPtr ExclusionsColumn::g_descendantExcludedIconName = new StringData( "descendantExcluded.png" );
StringDataPtr ExclusionsColumn::g_locationExcludedIconName = new StringData( "locationExcluded.png" );
StringDataPtr ExclusionsColumn::g_ancestorExcludedIconName = new StringData( "locationExcludedTransparent.png" );
StringDataPtr ExclusionsColumn::g_locationExcludedHighlightedIconName = new StringData( "locationExcludedHighlighted.png" );
StringDataPtr ExclusionsColumn::g_locationExcludedHighlightedTransparentIconName = new StringData( "locationExcludedHighlightedTransparent.png" );

StringDataPtr ExclusionsColumn::g_exclusionToolTip = new StringData( "Click to exclude this branch from the Visible Set, causing it to not appear in Viewers." );
StringDataPtr ExclusionsColumn::g_locationExcludedToolTip = new StringData(
	"This branch is excluded from the Visible Set, causing it to not appear in Viewers.\n\n"
	"Click to remove the exclusion.\n"
	"Shift-click to remove all excluded locations within this branch."
);
StringDataPtr ExclusionsColumn::g_ancestorExcludedToolTip = new StringData(
	"An ancestor is excluded from the Visible Set, causing this location and its descendants to not appear in Viewers.\n\n"
	"Click to also exclude this branch."
);
StringDataPtr ExclusionsColumn::g_descendantExcludedToolTip = new StringData(
	"One or more descendants are excluded from the Visible Set.\n\n"
	"Click to also exclude this branch.\n"
	"Shift-click to remove all excluded locations within this branch."
);

} // namespace

void GafferSceneUIModule::bindHierarchyView()
{

	// Deliberately using RefCountedClass rather than RunTimeTypedClass
	// to avoid having to register unique type ids and names for otherwise
	// private classes.

	RefCountedClass<HierarchyViewFilter, PathFilter>( "_HierarchyViewFilter" )
		.def( "setScene", &HierarchyViewFilter::setScene )
		.def( "getScene", &getScene )
		.def( "setContext", &HierarchyViewFilter::setContext )
		.def( "getContext", &getContext )

		.def( "setSetNames", &setSetNames )
		.def( "getSetNames", &getSetNames )
	;

	RefCountedClass<HierarchyViewSetFilter, HierarchyViewFilter>( "_HierarchyViewSetFilter" )
		.def( init<IECore::CompoundDataPtr>( ( boost::python::arg( "userData" ) = object() ) ) )
		.def( "setSetNames", &setSetNames )
		.def( "getSetNames", &getSetNames )
	;

	RefCountedClass<HierarchyViewSearchFilter, HierarchyViewFilter>( "_HierarchyViewSearchFilter" )
		.def( init<IECore::CompoundDataPtr>( ( boost::python::arg( "userData" ) = object() ) ) )
		.def( "setMatchPattern", &HierarchyViewSearchFilter::setMatchPattern )
		.def( "getMatchPattern", &HierarchyViewSearchFilter::getMatchPattern, return_value_policy<copy_const_reference>() )
	;

	RefCountedClass<InclusionsColumn, GafferUI::PathColumn>( "_HierarchyViewInclusionsColumn" )
		.def( init< ContextPtr >() )
	;

	RefCountedClass<ExclusionsColumn, GafferUI::PathColumn>( "_HierarchyViewExclusionsColumn" )
		.def( init< ContextPtr >() )
	;

}
