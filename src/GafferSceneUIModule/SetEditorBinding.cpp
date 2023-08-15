//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "SetEditorBinding.h"

#include "GafferSceneUI/ContextAlgo.h"
#include "GafferSceneUI/TypeIds.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePlug.h"

#include "GafferUI/PathColumn.h"

#include "GafferBindings/PathBinding.h"

#include "Gaffer/Context.h"
#include "Gaffer/Node.h"
#include "Gaffer/Path.h"
#include "Gaffer/PathFilter.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECorePython/RefCountedBinding.h"

#include "IECore/StringAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"
#include "boost/container/flat_set.hpp"

using namespace std;
using namespace boost::placeholders;
using namespace boost::python;
using namespace IECore;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

namespace
{

const boost::container::flat_set<InternedString> g_standardSets = {
	"__lights",
	"__lightFilters",
	"__cameras",
	"__coordinateSystems",
	"defaultLights",
	"soloLights"
};

Path::Names parent( InternedString setName )
{
	if( g_standardSets.contains( setName ) )
	{
		return { "Standard" };
	}
	else
	{
		Path::Names result;
		StringAlgo::tokenize( setName.string(), ':', result );
		result.pop_back();
		return result;
	}
}

//////////////////////////////////////////////////////////////////////////
// LRU cache of PathMatchers built from set names
//////////////////////////////////////////////////////////////////////////

struct PathMatcherCacheGetterKey
{

	PathMatcherCacheGetterKey()
		:	setNames( nullptr )
	{
	}

	PathMatcherCacheGetterKey( const IECore::MurmurHash &hash, ConstInternedStringVectorDataPtr setNames )
		:	hash( hash ), setNames( setNames )
	{
	}

	operator const IECore::MurmurHash & () const
	{
		return hash;
	}

	const MurmurHash hash;
	const ConstInternedStringVectorDataPtr setNames;

};

PathMatcher pathMatcherCacheGetter( const PathMatcherCacheGetterKey &key, size_t &cost, const IECore::Canceller *canceller )
{
	cost = 1;

	PathMatcher result;

	for( const auto &setName : key.setNames->readable() )
	{
		Path::Names path = parent( setName );
		path.push_back( setName );
		result.addPath( path );
	}

	return result;
}

using PathMatcherCache = IECorePreview::LRUCache<IECore::MurmurHash, IECore::PathMatcher, IECorePreview::LRUCachePolicy::Parallel, PathMatcherCacheGetterKey>;
PathMatcherCache g_pathMatcherCache( pathMatcherCacheGetter, 25 );

const InternedString g_setNamePropertyName( "setPath:setName" );
const InternedString g_memberCountPropertyName( "setPath:memberCount" );

//////////////////////////////////////////////////////////////////////////
// SetPath
//////////////////////////////////////////////////////////////////////////

class SetPath : public Gaffer::Path
{

	public :

		SetPath( ScenePlugPtr scene, Gaffer::ContextPtr context, Gaffer::PathFilterPtr filter = nullptr )
			:	Path( filter )
		{
			setScene( scene );
			setContext( context );
		}

		SetPath( ScenePlugPtr scene, Gaffer::ContextPtr context, const Names &names, const IECore::InternedString &root = "/", Gaffer::PathFilterPtr filter = nullptr )
			:	Path( names, root, filter )
		{
			setScene( scene );
			setContext( context );
		}

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( SetPath, GafferSceneUI::SetPathTypeId, Gaffer::Path );

		~SetPath() override
		{
		}

		void setScene( ScenePlugPtr scene )
		{
			if( m_scene == scene )
			{
				return;
			}

			m_scene = scene;
			m_plugDirtiedConnection = scene->node()->plugDirtiedSignal().connect( boost::bind( &SetPath::plugDirtied, this, ::_1 ) );

			emitPathChanged();
		}

		ScenePlug *getScene()
		{
			return m_scene.get();
		}

		const ScenePlug *getScene() const
		{
			return m_scene.get();
		}

		void setContext( Gaffer::ContextPtr context )
		{
			if( m_context == context )
			{
				return;
			}

			m_context = context;
			m_contextChangedConnection = context->changedSignal().connect( boost::bind( &SetPath::contextChanged, this, ::_2 ) );

			emitPathChanged();
		}

		Gaffer::Context *getContext()
		{
			return m_context.get();
		}

		const Gaffer::Context *getContext() const
		{
			return m_context.get();
		}

		bool isValid( const IECore::Canceller *canceller = nullptr ) const override
		{
			if( !Path::isValid() )
			{
				return false;
			}

			const PathMatcher p = pathMatcher( canceller );
			return p.match( names() ) & ( PathMatcher::ExactMatch | PathMatcher::DescendantMatch );
		}

		bool isLeaf( const IECore::Canceller *canceller ) const override
		{
			const PathMatcher p = pathMatcher( canceller );
			const unsigned match = p.match( names() );
			return match & PathMatcher::ExactMatch && !( match & PathMatcher::DescendantMatch );
		}

		PathPtr copy() const override
		{
			return new SetPath( m_scene, m_context, names(), root(), const_cast<PathFilter *>( getFilter() ) );
		}

		void propertyNames( std::vector<IECore::InternedString> &names, const IECore::Canceller *canceller = nullptr ) const override
		{
			Path::propertyNames( names, canceller );
			names.push_back( g_setNamePropertyName );
			names.push_back( g_memberCountPropertyName );
		}

		IECore::ConstRunTimeTypedPtr property( const IECore::InternedString &name, const IECore::Canceller *canceller = nullptr ) const override
		{
			if( name == g_setNamePropertyName )
			{
				const PathMatcher p = pathMatcher( canceller );
				if( p.match( names() ) & PathMatcher::ExactMatch )
				{
					return new StringData( names().back().string() );
				}
			}
			else if( name == g_memberCountPropertyName )
			{
				const PathMatcher p = pathMatcher( canceller );
				if( p.match( names() ) & PathMatcher::ExactMatch )
				{
					Context::EditableScope scopedContext( getContext() );
					if( canceller )
					{
						scopedContext.setCanceller( canceller );
					}
					const auto setMembers = getScene()->set( names().back().string() );
					return new IntData( setMembers->readable().size() );
				}
			}
			return Path::property( name, canceller );
		}

		const Gaffer::Plug *cancellationSubject() const override
		{
			return m_scene.get();
		}

	protected :

		void doChildren( std::vector<PathPtr> &children, const IECore::Canceller *canceller ) const override
		{
			const PathMatcher p = pathMatcher( canceller );

			auto it = p.find( names() );
			if( it == p.end() )
			{
				return;
			}

			++it;
			while( it != p.end() && it->size() == names().size() + 1 )
			{
				children.push_back( new SetPath( m_scene, m_context, *it, root(), const_cast<PathFilter *>( getFilter() ) ) );
				it.prune();
				++it;
			}

			std::sort(
				children.begin(), children.end(),
				[]( const PathPtr &a, const PathPtr &b ) {
					return a->names().back().string() < b->names().back().string();
				}
			);
		}


	private :

		const IECore::PathMatcher pathMatcher( const IECore::Canceller *canceller ) const
		{
			Context::EditableScope scopedContext( m_context.get() );
			if( canceller )
			{
				scopedContext.setCanceller( canceller );
			}
			const PathMatcherCacheGetterKey key( m_scene.get()->setNamesHash(), m_scene.get()->setNames() );
			return g_pathMatcherCache.get( key );
		}

		void contextChanged( const IECore::InternedString &key )
		{
			if( !boost::starts_with( key.c_str(), "ui:" ) )
			{
				emitPathChanged();
			}
		}

		void plugDirtied( Gaffer::Plug *plug )
		{
			if( plug == m_scene->setNamesPlug() || plug == m_scene->setPlug() )
			{
				emitPathChanged();
			}
		}

		Gaffer::NodePtr m_node;
		ScenePlugPtr m_scene;
		Gaffer::ContextPtr m_context;
		Gaffer::Signals::ScopedConnection m_plugDirtiedConnection;
		Gaffer::Signals::ScopedConnection m_contextChangedConnection;

};

IE_CORE_DEFINERUNTIMETYPED( SetPath );

SetPath::Ptr constructor1( ScenePlug &scene, Context &context, PathFilterPtr filter )
{
	return new SetPath( &scene, &context, filter );
}

SetPath::Ptr constructor2( ScenePlug &scene, Context &context, const std::vector<IECore::InternedString> &names, const IECore::InternedString &root, PathFilterPtr filter )
{
	return new SetPath( &scene, &context, names, root, filter );
}

//////////////////////////////////////////////////////////////////////////
// SetNameColumn
//////////////////////////////////////////////////////////////////////////

ConstStringDataPtr g_emptySetIcon = new StringData( "emptySet.png" );
ConstStringDataPtr g_populatedSetIcon = new StringData( "populatedSet.png" );
ConstStringDataPtr g_setFolderIcon = new StringData( "setFolder.png" );

class SetNameColumn : public StandardPathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( SetNameColumn )

		SetNameColumn()
			:	StandardPathColumn( "Name", "name", GafferUI::PathColumn::SizeMode::Stretch )
		{
		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override
		{
			CellData result = StandardPathColumn::cellData( path, canceller );

			const auto setName = runTimeCast<const IECore::StringData>( path.property( g_setNamePropertyName, canceller ) );
			if( !setName )
			{
				result.icon = g_setFolderIcon;
			}
			else
			{
				const auto memberCount = runTimeCast<const IECore::IntData>( path.property( g_memberCountPropertyName, canceller ) );
				if( memberCount )
				{
					result.icon = memberCount->readable() > 0 ? g_populatedSetIcon : g_emptySetIcon;
				}
			}

			return result;
		}

};

//////////////////////////////////////////////////////////////////////////
// VisibleSetInclusionsColumn - displays and modifies inclusions membership
// of the VisibleSet in the provided context.
//////////////////////////////////////////////////////////////////////////

class VisibleSetInclusionsColumn : public PathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( VisibleSetInclusionsColumn )

		VisibleSetInclusionsColumn( ContextPtr context )
			:	PathColumn(), m_context( context )
		{
			buttonPressSignal().connect( boost::bind( &VisibleSetInclusionsColumn::buttonPress, this, ::_3 ) );
			buttonReleaseSignal().connect( boost::bind( &VisibleSetInclusionsColumn::buttonRelease, this, ::_1, ::_2, ::_3 ) );
			m_context->changedSignal().connect( boost::bind( &VisibleSetInclusionsColumn::contextChanged, this, ::_2 ) );
		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override
		{
			CellData result;

			auto setPath = IECore::runTimeCast<const SetPath>( &path );
			if( !setPath )
			{
				return result;
			}

			const auto setName = runTimeCast<const IECore::StringData>( setPath->property( g_setNamePropertyName ) );
			if( !setName )
			{
				// We only interact with locations representing sets
				return result;
			}

			auto iconData = new CompoundData;
			iconData->writable()["state:highlighted"] = g_setIncludedHighlightedTransparentIconName;
			result.icon = iconData;
			result.toolTip = g_inclusionToolTip;

			const auto visibleSet = ContextAlgo::getVisibleSet( m_context.get() );
			if( visibleSet.inclusions.isEmpty() )
			{
				result.value = new IntData( 0 );
				return result;
			}

			Context::Scope scopedContext( m_context.get() );
			const auto setMembers = setPath->getScene()->set( setName->readable() );
			const auto includedSetMembers = setMembers->readable().intersection( visibleSet.inclusions );
			result.value = new IntData( includedSetMembers.size() );
			if( includedSetMembers.isEmpty() )
			{
				return result;
			}

			size_t excludedSetMemberCount = 0;
			if( !visibleSet.exclusions.isEmpty() )
			{
				for( IECore::PathMatcher::Iterator it = includedSetMembers.begin(), eIt = includedSetMembers.end(); it != eIt; ++it )
				{
					const auto visibility = visibleSet.visibility( *it );
					if( visibility.drawMode != GafferScene::VisibleSet::Visibility::Visible )
					{
						excludedSetMemberCount++;
					}
				}
			}

			iconData->writable()["state:highlighted"] = g_setIncludedHighlightedIconName;
			const bool allSetMembersIncluded = includedSetMembers.size() == setMembers->readable().size();
			if( excludedSetMemberCount == 0 )
			{
				iconData->writable()["state:normal"] = allSetMembersIncluded ? g_setIncludedIconName : g_setPartiallyIncludedIconName;
				result.toolTip = allSetMembersIncluded ? g_setIncludedToolTip : g_setPartiallyIncludedToolTip;
			}
			else if( includedSetMembers.size() == excludedSetMemberCount )
			{
				iconData->writable()["state:normal"] = g_setIncludedDisabledIconName;
				result.toolTip = allSetMembersIncluded ? g_setIncludedOverrideToolTip : g_setPartiallyIncludedOverrideToolTip;
			}
			else
			{
				iconData->writable()["state:normal"] = g_setPartiallyDisabledIconName;
				result.toolTip = allSetMembersIncluded ? g_setIncludedPartialOverrideToolTip : g_setPartiallyIncludedPartialOverrideToolTip;
			}

			return result;
		}

		CellData headerData( const IECore::Canceller *canceller ) const override
		{
			const auto visibleSet = ContextAlgo::getVisibleSet( m_context.get() );
			return CellData( /* value = */ nullptr, /* icon = */ visibleSet.inclusions.isEmpty() ? g_inclusionsEmptyIconName : g_setIncludedIconName, /* background = */ nullptr, /* tooltip = */ new StringData( "Visible Set Inclusions" ) );
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
			auto setPath = IECore::runTimeCast<const SetPath>( &path );
			if( !setPath )
			{
				return false;
			}

			const auto setName = runTimeCast<const IECore::StringData>( setPath->property( g_setNamePropertyName ) );
			if( !setName )
			{
				// We only interact with locations representing sets
				return false;
			}

			Context::Scope scopedContext( m_context.get() );
			const auto setMembers = setPath->getScene()->set( setName->readable() );
			auto pathsToInclude = IECore::PathMatcher( setMembers->readable() );
			const auto selection = widget.getSelection();
			if( std::holds_alternative<IECore::PathMatcher>( selection ) )
			{
				// Permit bulk editing of a selection of set names when clicking on one of the selected set names
				const auto selectedPaths = std::get<IECore::PathMatcher>( selection );
				if( selectedPaths.match( setPath->names() ) & IECore::PathMatcher::Result::ExactMatch )
				{
					auto selectedSetPath = setPath->copy();
					for( IECore::PathMatcher::Iterator it = selectedPaths.begin(), eIt = selectedPaths.end(); it != eIt; ++it )
					{
						selectedSetPath->setFromString( ScenePlug::pathToString( *it ) );
						const auto selectedSetName = runTimeCast<const IECore::StringData>( selectedSetPath->property( g_setNamePropertyName ) );
						if( selectedSetName && selectedSetName->readable() != setName->readable() )
						{
							pathsToInclude.addPaths( setPath->getScene()->set( selectedSetName->readable() )->readable() );
						}
					}
				}
			}

			bool update = false;
			auto visibleSet = ContextAlgo::getVisibleSet( m_context.get() );
			if( event.button == ButtonEvent::Left && !event.modifiers )
			{
				const auto includedSetMembers = setMembers->readable().intersection( visibleSet.inclusions );
				if( includedSetMembers.isEmpty() )
				{
					update = visibleSet.inclusions.addPaths( pathsToInclude );
				}
				else
				{
					update = visibleSet.inclusions.removePaths( pathsToInclude );
				}
			}
			else if( event.button == ButtonEvent::Left && event.modifiers == ButtonEvent::Modifiers::Shift )
			{
				update = visibleSet.inclusions.addPaths( pathsToInclude );
			}

			if( update )
			{
				ContextAlgo::setVisibleSet( m_context.get(), visibleSet );
			}

			return true;
		}

		ContextPtr m_context;

		static IECore::StringDataPtr g_setIncludedIconName;
		static IECore::StringDataPtr g_setIncludedDisabledIconName;
		static IECore::StringDataPtr g_setIncludedHighlightedIconName;
		static IECore::StringDataPtr g_setIncludedHighlightedTransparentIconName;
		static IECore::StringDataPtr g_setPartiallyIncludedIconName;
		static IECore::StringDataPtr g_setPartiallyDisabledIconName;
		static IECore::StringDataPtr g_inclusionsEmptyIconName;

		static IECore::StringDataPtr g_inclusionToolTip;
		static IECore::StringDataPtr g_setIncludedToolTip;
		static IECore::StringDataPtr g_setIncludedOverrideToolTip;
		static IECore::StringDataPtr g_setIncludedPartialOverrideToolTip;
		static IECore::StringDataPtr g_setPartiallyIncludedToolTip;
		static IECore::StringDataPtr g_setPartiallyIncludedOverrideToolTip;
		static IECore::StringDataPtr g_setPartiallyIncludedPartialOverrideToolTip;

};

StringDataPtr VisibleSetInclusionsColumn::g_setIncludedIconName = new StringData( "locationIncluded.png" );
StringDataPtr VisibleSetInclusionsColumn::g_setIncludedDisabledIconName = new StringData( "locationIncludedDisabled.png" );
StringDataPtr VisibleSetInclusionsColumn::g_setIncludedHighlightedIconName = new StringData( "locationIncludedHighlighted.png" );
StringDataPtr VisibleSetInclusionsColumn::g_setIncludedHighlightedTransparentIconName = new StringData( "locationIncludedHighlightedTransparent.png" );
StringDataPtr VisibleSetInclusionsColumn::g_setPartiallyIncludedIconName = new StringData( "descendantIncluded.png" );
StringDataPtr VisibleSetInclusionsColumn::g_setPartiallyDisabledIconName = new StringData( "descendantIncludedTransparent.png" );
StringDataPtr VisibleSetInclusionsColumn::g_inclusionsEmptyIconName = new StringData( "locationIncludedTransparent.png" );

StringDataPtr VisibleSetInclusionsColumn::g_inclusionToolTip = new StringData( "Click to include the current members of this set in the Visible Set, causing them to always appear in Viewers." );
StringDataPtr VisibleSetInclusionsColumn::g_setIncludedToolTip = new StringData(
	"All members are in the Visible Set, causing them to always appear in Viewers.\n\n"
	"Click to remove members from the Visible Set."
);
StringDataPtr VisibleSetInclusionsColumn::g_setIncludedOverrideToolTip = new StringData(
	"All members are in the Visible Set, but aren't visible due to being overridden by an exclusion.\n\n"
	"Click to remove members from the Visible Set."
);
StringDataPtr VisibleSetInclusionsColumn::g_setIncludedPartialOverrideToolTip = new StringData(
	"All members are in the Visible Set, but some aren't visible due to being overridden by an exclusion.\n\n"
	"Click to remove members from the Visible Set."
);
StringDataPtr VisibleSetInclusionsColumn::g_setPartiallyIncludedToolTip = new StringData(
	"Some members are in the Visible Set, causing them to always appear in Viewers.\n\n"
	"Click to remove members from the Visible Set.\n"
	"Shift-click to include members in the Visible Set."
);
StringDataPtr VisibleSetInclusionsColumn::g_setPartiallyIncludedOverrideToolTip = new StringData(
	"Some members are in the Visible Set, but aren't visible due to being overridden by an exclusion.\n\n"
	"Click to remove members from the Visible Set.\n"
	"Shift-click to include members in the Visible Set."
);
StringDataPtr VisibleSetInclusionsColumn::g_setPartiallyIncludedPartialOverrideToolTip = new StringData(
	"Some members are in the Visible Set, but some aren't visible due to being overridden by an exclusion.\n\n"
	"Click to remove members from the Visible Set.\n"
	"Shift-click to include members in the Visible Set."
);

//////////////////////////////////////////////////////////////////////////
// VisibleSetExclusionsColumn - displays and modifies exclusions membership
// of the VisibleSet in the provided context.
//////////////////////////////////////////////////////////////////////////

class VisibleSetExclusionsColumn : public PathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( VisibleSetExclusionsColumn )

		VisibleSetExclusionsColumn( ContextPtr context )
			:	PathColumn(), m_context( context )
		{
			buttonPressSignal().connect( boost::bind( &VisibleSetExclusionsColumn::buttonPress, this, ::_3 ) );
			buttonReleaseSignal().connect( boost::bind( &VisibleSetExclusionsColumn::buttonRelease, this, ::_1, ::_2, ::_3 ) );
			m_context->changedSignal().connect( boost::bind( &VisibleSetExclusionsColumn::contextChanged, this, ::_2 ) );
		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override
		{
			CellData result;

			auto setPath = IECore::runTimeCast<const SetPath>( &path );
			if( !setPath )
			{
				return result;
			}

			const auto setName = runTimeCast<const IECore::StringData>( setPath->property( g_setNamePropertyName ) );
			if( !setName )
			{
				// We only interact with locations representing sets
				return result;
			}

			auto iconData = new CompoundData;
			iconData->writable()["state:highlighted"] = g_setExcludedHighlightedTransparentIconName;
			result.icon = iconData;
			result.toolTip = g_exclusionToolTip;

			const auto visibleSet = ContextAlgo::getVisibleSet( m_context.get() );
			if( visibleSet.exclusions.isEmpty() )
			{
				result.value = new IntData( 0 );
				return result;
			}

			Context::Scope scopedContext( m_context.get() );
			const auto setMembers = setPath->getScene()->set( setName->readable() );
			const auto excludedSetMembers = setMembers->readable().intersection( visibleSet.exclusions );
			result.value = new IntData( excludedSetMembers.size() );
			if( excludedSetMembers.isEmpty() )
			{
				return result;
			}

			const bool allSetMembersExcluded = excludedSetMembers.size() == setMembers->readable().size();
			iconData->writable()["state:highlighted"] = g_setExcludedHighlightedIconName;
			iconData->writable()["state:normal"] = allSetMembersExcluded ? g_setExcludedIconName : g_setPartiallyExcludedIconName;
			result.toolTip = allSetMembersExcluded ? g_setExcludedToolTip : g_setPartiallyExcludedToolTip;

			return result;
		}

		CellData headerData( const IECore::Canceller *canceller ) const override
		{
			const auto visibleSet = ContextAlgo::getVisibleSet( m_context.get() );
			return CellData( /* value = */ nullptr, /* icon = */ visibleSet.exclusions.isEmpty() ? g_exclusionsEmptyIconName : g_setExcludedIconName, /* background = */ nullptr, /* tooltip = */ new StringData( "Visible Set Exclusions" ) );
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
			auto setPath = IECore::runTimeCast<const SetPath>( &path );
			if( !setPath )
			{
				return false;
			}

			const auto setName = runTimeCast<const IECore::StringData>( setPath->property( g_setNamePropertyName ) );
			if( !setName )
			{
				// We only interact with locations representing sets
				return false;
			}

			Context::Scope scopedContext( m_context.get() );
			const auto setMembers = setPath->getScene()->set( setName->readable() );
			auto pathsToExclude = IECore::PathMatcher( setMembers->readable() );
			const auto selection = widget.getSelection();
			if( std::holds_alternative<IECore::PathMatcher>( selection ) )
			{
				// Permit bulk editing of a selection of set names when clicking on one of the selected set names
				const auto selectedPaths = std::get<IECore::PathMatcher>( selection );
				if( selectedPaths.match( setPath->names() ) & IECore::PathMatcher::Result::ExactMatch )
				{
					auto selectedSetPath = setPath->copy();
					for( IECore::PathMatcher::Iterator it = selectedPaths.begin(), eIt = selectedPaths.end(); it != eIt; ++it )
					{
						selectedSetPath->setFromString( ScenePlug::pathToString( *it ) );
						const auto selectedSetName = runTimeCast<const IECore::StringData>( selectedSetPath->property( g_setNamePropertyName ) );
						if( selectedSetName && selectedSetName->readable() != setName->readable() )
						{
							pathsToExclude.addPaths( setPath->getScene()->set( selectedSetName->readable() )->readable() );
						}
					}
				}
			}

			bool update = false;
			auto visibleSet = ContextAlgo::getVisibleSet( m_context.get() );
			if( event.button == ButtonEvent::Left && !event.modifiers )
			{
				const auto excludedSetMembers = setMembers->readable().intersection( visibleSet.exclusions );
				if( excludedSetMembers.isEmpty() )
				{
					update = visibleSet.exclusions.addPaths( pathsToExclude );
				}
				else
				{
					update = visibleSet.exclusions.removePaths( pathsToExclude );
				}
			}
			else if( event.button == ButtonEvent::Left && event.modifiers == ButtonEvent::Modifiers::Shift )
			{
				update = visibleSet.exclusions.addPaths( pathsToExclude );
			}

			if( update )
			{
				ContextAlgo::setVisibleSet( m_context.get(), visibleSet );
			}

			return true;
		}

		ContextPtr m_context;

		static IECore::StringDataPtr g_setExcludedIconName;
		static IECore::StringDataPtr g_setPartiallyExcludedIconName;
		static IECore::StringDataPtr g_setExcludedHighlightedIconName;
		static IECore::StringDataPtr g_setExcludedHighlightedTransparentIconName;
		static IECore::StringDataPtr g_exclusionsEmptyIconName;

		static IECore::StringDataPtr g_exclusionToolTip;
		static IECore::StringDataPtr g_setExcludedToolTip;
		static IECore::StringDataPtr g_setPartiallyExcludedToolTip;
};

StringDataPtr VisibleSetExclusionsColumn::g_setExcludedIconName = new StringData( "locationExcluded.png" );
StringDataPtr VisibleSetExclusionsColumn::g_setPartiallyExcludedIconName = new StringData( "descendantExcluded.png" );
StringDataPtr VisibleSetExclusionsColumn::g_setExcludedHighlightedIconName = new StringData( "locationExcludedHighlighted.png" );
StringDataPtr VisibleSetExclusionsColumn::g_setExcludedHighlightedTransparentIconName = new StringData( "locationExcludedHighlightedTransparent.png" );
StringDataPtr VisibleSetExclusionsColumn::g_exclusionsEmptyIconName = new StringData( "locationExcludedTransparent.png" );

StringDataPtr VisibleSetExclusionsColumn::g_exclusionToolTip = new StringData( "Click to exclude the current members of this set from the Visible Set, causing them to not appear in Viewers." );
StringDataPtr VisibleSetExclusionsColumn::g_setExcludedToolTip = new StringData(
	"All members are excluded from the Visible Set, causing them to not appear in Viewers.\n\n"
	"Click to remove the exclusion."
);
StringDataPtr VisibleSetExclusionsColumn::g_setPartiallyExcludedToolTip = new StringData(
	"Some members are excluded from the Visible Set, causing them to not appear in Viewers.\n\n"
	"Click to remove the exclusion.\n"
	"Shift-click to exclude members from the Visible Set."
);

//////////////////////////////////////////////////////////////////////////
// SetEditorSearchFilter - filters based on a match pattern. This
// removes non-leaf paths if all their children have also been
// removed by the filter.
//////////////////////////////////////////////////////////////////////////

class SetEditorSearchFilter : public Gaffer::PathFilter
{

	public :

		IE_CORE_DECLAREMEMBERPTR( SetEditorSearchFilter )

		SetEditorSearchFilter( IECore::CompoundDataPtr userData = nullptr )
			:	PathFilter( userData )
		{
		}

		void setMatchPattern( const string &matchPattern )
		{
			if( m_matchPattern == matchPattern )
			{
				return;
			}
			m_matchPattern = matchPattern;
			m_wildcardPattern = IECore::StringAlgo::hasWildcards( matchPattern ) ? matchPattern : "*" + matchPattern + "*";

			changedSignal()( this );
		}

		const string &getMatchPattern() const
		{
			return m_matchPattern;
		}

		void doFilter( std::vector<PathPtr> &paths, const IECore::Canceller *canceller ) const override
		{
			if( m_matchPattern.empty() || paths.empty() )
			{
				return;
			}

			paths.erase(
				std::remove_if(
					paths.begin(),
					paths.end(),
					[this] ( const auto &p ) { return remove( p ); }
				),
				paths.end()
			);
		}

		bool remove( PathPtr path ) const
		{
			if( !path->names().size() )
			{
				return true;
			}

			bool leaf = path->isLeaf();
			if( !leaf )
			{
				std::vector<PathPtr> c;
				path->children( c );

				leaf = std::all_of( c.begin(), c.end(), [this] ( const auto &p ) { return remove( p ); } );
			}

			const bool match = IECore::StringAlgo::matchMultiple( path->names().back().string(), m_wildcardPattern );

			return leaf && !match;
		}

	private:

		std::string m_matchPattern;
		std::string m_wildcardPattern;

};

//////////////////////////////////////////////////////////////////////////
// SetEditorEmptySetFilter - filters out paths that have a memberCount
// property value of 0. This also removes non-leaf paths if all their
// children have been removed by the filter.
//////////////////////////////////////////////////////////////////////////

class SetEditorEmptySetFilter : public Gaffer::PathFilter
{

	public :

		IE_CORE_DECLAREMEMBERPTR( SetEditorEmptySetFilter )

		SetEditorEmptySetFilter( IECore::CompoundDataPtr userData = nullptr )
			:	PathFilter( userData )
		{
		}

		void doFilter( std::vector<PathPtr> &paths, const IECore::Canceller *canceller ) const override
		{
			paths.erase(
				std::remove_if(
					paths.begin(),
					paths.end(),
					[this, canceller] ( auto &p ) { return remove( p, canceller ); }
				),
				paths.end()
			);
		}

		bool remove( PathPtr path, const IECore::Canceller *canceller ) const
		{
			if( !path->names().size() )
			{
				return true;
			}

			bool leaf = path->isLeaf();
			if( !leaf )
			{
				std::vector<PathPtr> c;
				path->children( c );

				leaf = std::all_of( c.begin(), c.end(), [this, canceller] ( const auto &p ) { return remove( p, canceller ); } );
			}

			bool members = false;
			if( const auto memberCountData = IECore::runTimeCast<const IECore::IntData>( path->property( g_memberCountPropertyName, canceller ) ) )
			{
				members = memberCountData->readable() > 0;
			}

			return leaf && !members;
		}

	};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Bindings
//////////////////////////////////////////////////////////////////////////

void GafferSceneUIModule::bindSetEditor()
{

	object module( borrowed( PyImport_AddModule( "GafferSceneUI._SetEditor" ) ) );
	scope().attr( "_SetEditor" ) = module;
	scope moduleScope( module );

	PathClass<SetPath>()
		.def(
			"__init__",
			make_constructor(
				constructor1,
				default_call_policies(),
				(
					boost::python::arg( "scene" ),
					boost::python::arg( "context" ),
					boost::python::arg( "filter" ) = object()
				)
			)
		)
		.def(
			"__init__",
			make_constructor(
				constructor2,
				default_call_policies(),
				(
					boost::python::arg( "scene" ),
					boost::python::arg( "context" ),
					boost::python::arg( "names" ),
					boost::python::arg( "root" ) = "/",
					boost::python::arg( "filter" ) = object()
				)
			)
		)
		.def( "setScene", &SetPath::setScene )
		.def( "getScene", (ScenePlug *(SetPath::*)())&SetPath::getScene, return_value_policy<CastToIntrusivePtr>() )
		.def( "setContext", &SetPath::setContext )
		.def( "getContext", (Context *(SetPath::*)())&SetPath::getContext, return_value_policy<CastToIntrusivePtr>() )
	;

	RefCountedClass<SetEditorSearchFilter, PathFilter>( "SearchFilter" )
		.def( init<IECore::CompoundDataPtr>( ( boost::python::arg( "userData" ) = object() ) ) )
		.def( "setMatchPattern", &SetEditorSearchFilter::setMatchPattern )
		.def( "getMatchPattern", &SetEditorSearchFilter::getMatchPattern, return_value_policy<copy_const_reference>() )
	;

	RefCountedClass<SetEditorEmptySetFilter, PathFilter>( "EmptySetFilter" )
		.def( init<IECore::CompoundDataPtr>( ( boost::python::arg( "userData" ) = object() ) ) )
	;

	RefCountedClass<SetNameColumn, GafferUI::PathColumn>( "SetNameColumn" )
		.def( init<>() )
	;

	RefCountedClass<VisibleSetInclusionsColumn, GafferUI::PathColumn>( "VisibleSetInclusionsColumn" )
		.def( init< ContextPtr >() )
	;

	RefCountedClass<VisibleSetExclusionsColumn, GafferUI::PathColumn>( "VisibleSetExclusionsColumn" )
		.def( init< ContextPtr >() )
	;

}
