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

#include "GafferSceneUI/ScriptNodeAlgo.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePath.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/VisibleSet.h"

#include "GafferUI/PathColumn.h"

#include "Gaffer/Context.h"
#include "Gaffer/Path.h"
#include "Gaffer/PathFilter.h"
#include "Gaffer/ScriptNode.h"

#include "IECorePython/RefCountedBinding.h"

#include "IECore/StringAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/python/suite/indexing/container_utils.hpp"

using namespace std;
using namespace boost::python;
using namespace boost::placeholders;
using namespace IECore;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

namespace
{

//////////////////////////////////////////////////////////////////////////
// InclusionsColumn - displays and modifies inclusions membership of the
// VisibleSet in the provided context.
//////////////////////////////////////////////////////////////////////////

class InclusionsColumn : public PathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( InclusionsColumn )

		InclusionsColumn( ScriptNodePtr script )
			:	PathColumn(), m_script( script ), m_visibleSet( ScriptNodeAlgo::getVisibleSet( script.get() ) )
		{
			buttonPressSignal().connect( boost::bind( &InclusionsColumn::buttonPress, this, ::_3 ) );
			buttonReleaseSignal().connect( boost::bind( &InclusionsColumn::buttonRelease, this, ::_1, ::_2, ::_3 ) );
			ScriptNodeAlgo::visibleSetChangedSignal( script.get() ).connect( boost::bind( &InclusionsColumn::visibleSetChanged, this ) );
		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override
		{
			CellData result;

			auto scenePath = IECore::runTimeCast<const ScenePath>( &path );
			if( !scenePath )
			{
				return result;
			}

			const auto inclusionsMatch = m_visibleSet.inclusions.match( scenePath->names() );
			const auto locationExcluded = m_visibleSet.exclusions.match( scenePath->names() ) & (IECore::PathMatcher::Result::ExactMatch | IECore::PathMatcher::Result::AncestorMatch);

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
				else if( m_visibleSet.expansions.match( scenePath->names() ) & IECore::PathMatcher::Result::ExactMatch )
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
			return CellData( /* value = */ nullptr, /* icon = */ m_visibleSet.inclusions.isEmpty() ? g_ancestorIncludedIconName : g_locationIncludedIconName, /* background = */ nullptr, /* tooltip = */ new StringData( "Visible Set Inclusions" ) );
		}

	private :

		void visibleSetChanged()
		{
			// We take a copy, because `cellData()` is called from background threads,
			// and it's not safe to call `getVisibleSet()` concurrently with modifications
			// on the foreground thread.
			m_visibleSet = ScriptNodeAlgo::getVisibleSet( m_script.get() );
			changedSignal()( this );
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

			auto paths = IECore::PathMatcher();
			paths.addPath( scenePath->names() );
			const auto selection = widget.getSelection();
			if( std::holds_alternative<std::vector<IECore::PathMatcher>>( selection ) )
			{
				// Permit bulk editing of a selection of paths when clicking on one of the selected paths
				const auto selectedPaths = std::get<std::vector<IECore::PathMatcher>>( selection );
				if( selectedPaths.size() && selectedPaths[0].match( scenePath->names() ) & IECore::PathMatcher::Result::ExactMatch )
				{
					paths = selectedPaths[0];
				}
			}

			bool update = false;
			auto visibleSet = m_visibleSet;
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
				ScriptNodeAlgo::setVisibleSet( m_script.get(), visibleSet );
			}

			return true;
		}

		ScriptNodePtr m_script;
		VisibleSet m_visibleSet;

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

		ExclusionsColumn( ScriptNodePtr script )
			:	PathColumn(), m_script( script ), m_visibleSet( ScriptNodeAlgo::getVisibleSet( script.get() ) )
		{
			buttonPressSignal().connect( boost::bind( &ExclusionsColumn::buttonPress, this, ::_3 ) );
			buttonReleaseSignal().connect( boost::bind( &ExclusionsColumn::buttonRelease, this, ::_1, ::_2, ::_3 ) );
			ScriptNodeAlgo::visibleSetChangedSignal( script.get() ).connect( boost::bind( &ExclusionsColumn::visibleSetChanged, this ) );
		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override
		{
			CellData result;

			auto scenePath = IECore::runTimeCast<const ScenePath>( &path );
			if( !scenePath )
			{
				return result;
			}

			auto exclusionsMatch = m_visibleSet.exclusions.match( scenePath->names() );

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
			return CellData( /* value = */ nullptr, /* icon = */ m_visibleSet.exclusions.isEmpty() ? g_ancestorExcludedIconName : g_locationExcludedIconName, /* background = */ nullptr, /* tooltip = */ new StringData( "Visible Set Exclusions" ) );
		}

	private :

		void visibleSetChanged()
		{
			// We take a copy, because `cellData()` is called from background threads,
			// and it's not safe to call `getVisibleSet()` concurrently with modifications
			// on the foreground thread.
			m_visibleSet = ScriptNodeAlgo::getVisibleSet( m_script.get() );
			changedSignal()( this );
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

			auto paths = IECore::PathMatcher();
			paths.addPath( scenePath->names() );
			const auto selection = widget.getSelection();
			if( std::holds_alternative<std::vector<IECore::PathMatcher>>( selection ) )
			{
				// Permit bulk editing of a selection of paths when clicking on one of the selected paths
				const auto selectedPaths = std::get<std::vector<IECore::PathMatcher>>( selection );
				if( selectedPaths.size() && selectedPaths[0].match( scenePath->names() ) & IECore::PathMatcher::Result::ExactMatch )
				{
					paths = selectedPaths[0];
				}
			}

			bool update = false;
			auto visibleSet = m_visibleSet;
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
				ScriptNodeAlgo::setVisibleSet( m_script.get(), visibleSet );
			}

			return true;
		}

		ScriptNodePtr m_script;
		VisibleSet m_visibleSet;

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

	RefCountedClass<InclusionsColumn, GafferUI::PathColumn>( "_HierarchyViewInclusionsColumn" )
		.def( init<ScriptNodePtr>() )
	;

	RefCountedClass<ExclusionsColumn, GafferUI::PathColumn>( "_HierarchyViewExclusionsColumn" )
		.def( init<ScriptNodePtr>() )
	;

}
