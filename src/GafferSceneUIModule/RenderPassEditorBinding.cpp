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

#include "RenderPassEditorBinding.h"

#include "GafferSceneUI/TypeIds.h"

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

using PathGroupingFunction = std::function<std::vector<InternedString> ( const std::string &renderPassName )>;

struct PathGroupingFunctionWrapper
{
	PathGroupingFunctionWrapper( object fn )
		:	m_fn( fn )
	{
	}

	std::vector<InternedString> operator()( const std::string &renderPassName )
	{
		IECorePython::ScopedGILLock gilock;
		try
		{
			return extract<std::vector<InternedString>>( m_fn( renderPassName ) );
		}
		catch( const error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}

	private:

		object m_fn;
};

PathGroupingFunction &pathGroupingFunction()
{
	// We deliberately make no attempt to free this, because typically a python
	// function is registered here, and we can't free that at exit because python
	// is already shut down by then.
	static PathGroupingFunction *g_pathGroupingFunction = new PathGroupingFunction;
	return *g_pathGroupingFunction;
}

void registerPathGroupingFunction( PathGroupingFunction f )
{
	pathGroupingFunction() = f;
}

void registerPathGroupingFunctionWrapper( object f )
{
	registerPathGroupingFunction( PathGroupingFunctionWrapper( f ) );
}

string pathGroupingFunctionToString( const std::string &renderPassName )
{
	std::string result;
	ScenePlug::pathToString( pathGroupingFunction()( renderPassName ), result );
	return result;
}

object pathGroupingFunctionWrapper()
{
	return make_function(
		pathGroupingFunctionToString,
		default_call_policies(),
		boost::mpl::vector<string, const string &>()
	);
}

//////////////////////////////////////////////////////////////////////////
// LRU cache of PathMatchers built from render passes
//////////////////////////////////////////////////////////////////////////

struct PathMatcherCacheGetterKey
{

	PathMatcherCacheGetterKey()
		:	renderPassNames( nullptr ), grouped( false )
	{
	}

	PathMatcherCacheGetterKey( ConstStringVectorDataPtr renderPassNames, bool grouped )
		:	renderPassNames( renderPassNames ), grouped( grouped )
	{
		renderPassNames->hash( hash );
		hash.append( grouped );
	}

	operator const IECore::MurmurHash & () const
	{
		return hash;
	}

	MurmurHash hash;
	const ConstStringVectorDataPtr renderPassNames;
	const bool grouped;

};

PathMatcher pathMatcherCacheGetter( const PathMatcherCacheGetterKey &key, size_t &cost, const IECore::Canceller *canceller )
{
	cost = 1;

	PathMatcher result;

	if( key.grouped && pathGroupingFunction() )
	{
		for( const auto &renderPass : key.renderPassNames->readable() )
		{
			std::vector<InternedString> path = pathGroupingFunction()( renderPass );
			path.push_back( renderPass );
			result.addPath( path );
		}
	}
	else
	{
		for( const auto &renderPass : key.renderPassNames->readable() )
		{
			result.addPath( renderPass );
		}
	}

	return result;
}

using PathMatcherCache = IECorePreview::LRUCache<IECore::MurmurHash, IECore::PathMatcher, IECorePreview::LRUCachePolicy::Parallel, PathMatcherCacheGetterKey>;
PathMatcherCache g_pathMatcherCache( pathMatcherCacheGetter, 25 );

const InternedString g_renderPassContextName( "renderPass" );
const InternedString g_disableAdaptorsContextName( "renderPassEditor:disableAdaptors" );
const InternedString g_renderPassNamePropertyName( "renderPassPath:name" );
const InternedString g_renderPassEnabledPropertyName( "renderPassPath:enabled" );
const InternedString g_renderPassEnabledWithoutAdaptorsPropertyName( "renderPassPath:enabledWithoutAdaptors" );
const InternedString g_renderPassNamesOption( "option:renderPass:names" );
const InternedString g_renderPassEnabledOption( "option:renderPass:enabled" );

//////////////////////////////////////////////////////////////////////////
// RenderPassPath
//////////////////////////////////////////////////////////////////////////

class RenderPassPath : public Gaffer::Path
{

	public :

		RenderPassPath( ScenePlugPtr scene, Gaffer::ContextPtr context, Gaffer::PathFilterPtr filter = nullptr, const bool grouped = false )
			:	Path( filter ), m_grouped( grouped )
		{
			setScene( scene );
			setContext( context );
		}

		RenderPassPath( ScenePlugPtr scene, Gaffer::ContextPtr context, const Names &names, const IECore::InternedString &root = "/", Gaffer::PathFilterPtr filter = nullptr, const bool grouped = false )
			:	Path( names, root, filter ), m_grouped( grouped )
		{
			setScene( scene );
			setContext( context );
		}

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( RenderPassPath, GafferSceneUI::RenderPassPathTypeId, Gaffer::Path );

		~RenderPassPath() override
		{
		}

		void setScene( ScenePlugPtr scene )
		{
			if( m_scene == scene )
			{
				return;
			}

			m_scene = scene;
			m_plugDirtiedConnection = scene->node()->plugDirtiedSignal().connect( boost::bind( &RenderPassPath::plugDirtied, this, ::_1 ) );

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
			m_contextChangedConnection = context->changedSignal().connect( boost::bind( &RenderPassPath::contextChanged, this, ::_2 ) );

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
			return new RenderPassPath( m_scene, m_context, names(), root(), const_cast<PathFilter *>( getFilter() ), m_grouped );
		}

		void propertyNames( std::vector<IECore::InternedString> &names, const IECore::Canceller *canceller = nullptr ) const override
		{
			Path::propertyNames( names, canceller );
			names.push_back( g_renderPassNamePropertyName );
			names.push_back( g_renderPassEnabledPropertyName );
			names.push_back( g_renderPassEnabledWithoutAdaptorsPropertyName );
		}

		IECore::ConstRunTimeTypedPtr property( const IECore::InternedString &name, const IECore::Canceller *canceller = nullptr ) const override
		{
			if( name == g_renderPassNamePropertyName )
			{
				const PathMatcher p = pathMatcher( canceller );
				if( p.match( names() ) & PathMatcher::ExactMatch )
				{
					return new StringData( names().back().string() );
				}
			}
			else if( name == g_renderPassEnabledPropertyName || name == g_renderPassEnabledWithoutAdaptorsPropertyName )
			{
				const PathMatcher p = pathMatcher( canceller );
				if( p.match( names() ) & PathMatcher::ExactMatch )
				{
					Context::EditableScope scopedContext( getContext() );
					if( name == g_renderPassEnabledWithoutAdaptorsPropertyName )
					{
						const bool disableAdaptors = true;
						scopedContext.set<bool>( g_disableAdaptorsContextName, &disableAdaptors );
					}
					if( canceller )
					{
						scopedContext.setCanceller( canceller );
					}
					scopedContext.set( g_renderPassContextName, &( names().back().string() ) );
					ConstBoolDataPtr enabledData = getScene()->globals()->member<BoolData>( g_renderPassEnabledOption );
					return new BoolData( enabledData ? enabledData->readable() : true );
				}
			}

			return Path::property( name, canceller );
		}

		const Gaffer::Plug *cancellationSubject() const override
		{
			return m_scene.get();
		}

		Gaffer::ContextPtr inspectionContext( const IECore::Canceller *canceller ) const override
		{
			const auto renderPassName = runTimeCast<const IECore::StringData>( property( g_renderPassNamePropertyName, canceller ) );
			if( !renderPassName )
			{
				return nullptr;
			}

			Context::EditableScope scope( getContext() );
			scope.set( g_renderPassContextName, &( renderPassName->readable() ) );
			if( canceller )
			{
				scope.setCanceller( canceller );
			}

			return new Context( *scope.context() );
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
				children.push_back( new RenderPassPath( m_scene, m_context, *it, root(), const_cast<PathFilter *>( getFilter() ), m_grouped ) );
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

		// We construct our path from a pathMatcher as we anticipate users requiring render passes to be organised
		// hierarchically, with the last part of the path representing the render pass name. While it's technically
		// possible to create a render pass name containing one or more '/' characters, we don't expect this to be
		// practical as render pass names are used in output file paths where the included '/' characters would be
		// interpreted as subdirectories. Validation in the UI will prevent users from inserting invalid characters
		// such as '/' into render pass names.
		const IECore::PathMatcher pathMatcher( const IECore::Canceller *canceller ) const
		{
			Context::EditableScope scopedContext( m_context.get() );
			if( canceller )
			{
				scopedContext.setCanceller( canceller );
			}

			if( ConstStringVectorDataPtr renderPassData = m_scene.get()->globals()->member<StringVectorData>( g_renderPassNamesOption ) )
			{
				const PathMatcherCacheGetterKey key( renderPassData, m_grouped );
				return g_pathMatcherCache.get( key );
			}

			return IECore::PathMatcher();
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
			if( plug == m_scene->globalsPlug() )
			{
				emitPathChanged();
			}
		}

		Gaffer::NodePtr m_node;
		ScenePlugPtr m_scene;
		Gaffer::ContextPtr m_context;
		Gaffer::Signals::ScopedConnection m_plugDirtiedConnection;
		Gaffer::Signals::ScopedConnection m_contextChangedConnection;
		bool m_grouped;

};

IE_CORE_DEFINERUNTIMETYPED( RenderPassPath );

RenderPassPath::Ptr constructor1( ScenePlug &scene, Context &context, PathFilterPtr filter, const bool grouped )
{
	return new RenderPassPath( &scene, &context, filter, grouped );
}

RenderPassPath::Ptr constructor2( ScenePlug &scene, Context &context, const std::vector<IECore::InternedString> &names, const IECore::InternedString &root, PathFilterPtr filter, const bool grouped )
{
	return new RenderPassPath( &scene, &context, names, root, filter, grouped );
}

//////////////////////////////////////////////////////////////////////////
// RenderPassNameColumn
//////////////////////////////////////////////////////////////////////////

ConstStringDataPtr g_adaptorDisabledRenderPassIcon = new StringData( "adaptorDisabledRenderPass.png" );
ConstStringDataPtr g_disabledRenderPassIcon = new StringData( "disabledRenderPass.png" );
ConstStringDataPtr g_renderPassIcon = new StringData( "renderPass.png" );
ConstStringDataPtr g_renderPassFolderIcon = new StringData( "renderPassFolder.png" );
ConstStringDataPtr g_disabledToolTip = new StringData( "Disabled." );
ConstStringDataPtr g_adaptorDisabledToolTip = new StringData( "Automatically disabled by a render adaptor.");
const Color4fDataPtr g_dimmedForegroundColor = new Color4fData( Imath::Color4f( 152, 152, 152, 255 ) / 255.0f );

class RenderPassNameColumn : public StandardPathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( RenderPassNameColumn )

		RenderPassNameColumn()
			:	StandardPathColumn( "Name", "name" )
		{
		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override
		{
			CellData result = StandardPathColumn::cellData( path, canceller );

			const auto renderPassName = runTimeCast<const IECore::StringData>( path.property( g_renderPassNamePropertyName, canceller ) );
			if( !renderPassName )
			{
				result.icon = g_renderPassFolderIcon;
			}
			else
			{
				if( const auto renderPassEnabled = runTimeCast<const IECore::BoolData>( path.property( g_renderPassEnabledPropertyName, canceller ) ) )
				{
					if( renderPassEnabled->readable() )
					{
						result.icon = g_renderPassIcon;
					}
					else
					{
						result.foreground = g_dimmedForegroundColor;
						const auto renderPassEnabledWithoutAdaptors = runTimeCast<const IECore::BoolData>( path.property( g_renderPassEnabledWithoutAdaptorsPropertyName, canceller ) );
						if( !renderPassEnabledWithoutAdaptors || !renderPassEnabledWithoutAdaptors->readable() )
						{
							result.icon = g_disabledRenderPassIcon;
							result.toolTip = g_disabledToolTip;
						}
						else
						{
							result.icon = g_adaptorDisabledRenderPassIcon;
							result.toolTip = g_adaptorDisabledToolTip;
						}
					}
				}
				else
				{
					result.icon = g_renderPassIcon;
				}
			}

			return result;
		}

};

//////////////////////////////////////////////////////////////////////////
// RenderPassActiveColumn
//////////////////////////////////////////////////////////////////////////

class RenderPassActiveColumn : public PathColumn
{

	public :

		IE_CORE_DECLAREMEMBERPTR( RenderPassActiveColumn )

		RenderPassActiveColumn()
			:	PathColumn()
		{
		}

		CellData cellData( const Gaffer::Path &path, const IECore::Canceller *canceller ) const override
		{
			CellData result;

			auto renderPassPath = runTimeCast<const RenderPassPath>( &path );
			if( !renderPassPath )
			{
				return result;
			}

			const auto renderPassName = runTimeCast<const IECore::StringData>( path.property( g_renderPassNamePropertyName, canceller ) );
			if( !renderPassName )
			{
				return result;
			}

			auto iconData = new CompoundData;
			result.icon = iconData;

			if( const std::string *currentPassName = renderPassPath->getContext()->getIfExists< std::string >( g_renderPassContextName ) )
			{
				if( *currentPassName == renderPassName->readable() )
				{
					iconData->writable()["state:normal"] = g_activeRenderPassIcon;
					/// \todo This is only to allow sorting, replace with `CellData::sortValue` in Gaffer 1.4
					result.value = new StringData( " " );
					result.toolTip = new StringData( fmt::format( "{} is the currently active render pass.\n\nDouble-click to unset.", renderPassName->readable() ) );

					return result;
				}
			}

			iconData->writable()["state:highlighted"] = g_activeRenderPassFadedHighlightedIcon;
			result.toolTip = new StringData( fmt::format( "Double-click to set {} as the active render pass.", renderPassName->readable() ) );

			return result;
		}

		CellData headerData( const IECore::Canceller *canceller ) const override
		{
			return CellData( nullptr, /* icon = */ g_activeRenderPassIcon, /* background = */ nullptr, new IECore::StringData( "The currently active render pass." ) );
		}

		static IECore::StringDataPtr g_activeRenderPassIcon;
		static IECore::StringDataPtr g_activeRenderPassFadedHighlightedIcon;

};

StringDataPtr RenderPassActiveColumn::g_activeRenderPassIcon = new StringData( "activeRenderPass.png" );
StringDataPtr RenderPassActiveColumn::g_activeRenderPassFadedHighlightedIcon = new StringData( "activeRenderPassFadedHighlighted.png" );

//////////////////////////////////////////////////////////////////////////
// RenderPassEditorSearchFilter - filters based on a match pattern. This
// removes non-leaf paths if all their children have also been
// removed by the filter.
//////////////////////////////////////////////////////////////////////////

/// \todo This is the same as the SetEditorSearchFilter, we'll need the non-leaf
/// path removal functionality when we start grouping render passes by category.
/// Could be worth turning into common functionality?
class RenderPassEditorSearchFilter : public Gaffer::PathFilter
{

	public :

		IE_CORE_DECLAREMEMBERPTR( RenderPassEditorSearchFilter )

		RenderPassEditorSearchFilter( IECore::CompoundDataPtr userData = nullptr )
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
// DisabledRenderPassFilter - filters out paths with a renderPassPath:enabled
// property value of `false`. This also removes non-leaf paths if all their
// children have been removed by the filter.
//////////////////////////////////////////////////////////////////////////

class DisabledRenderPassFilter : public Gaffer::PathFilter
{

	public :

		IE_CORE_DECLAREMEMBERPTR( DisabledRenderPassFilter )

		DisabledRenderPassFilter( IECore::CompoundDataPtr userData = nullptr )
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

			bool enabled = false;
			if( runTimeCast<const IECore::StringData>( path->property( g_renderPassNamePropertyName, canceller ) ) )
			{
				if( const auto enabledData = IECore::runTimeCast<const IECore::BoolData>( path->property( g_renderPassEnabledPropertyName, canceller ) ) )
				{
					enabled = enabledData->readable();
				}
				else
				{
					enabled = true;
				}
			}

			return leaf && !enabled;
		}

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Bindings
//////////////////////////////////////////////////////////////////////////

void GafferSceneUIModule::bindRenderPassEditor()
{

	object module( borrowed( PyImport_AddModule( "GafferSceneUI._RenderPassEditor" ) ) );
	scope().attr( "_RenderPassEditor" ) = module;
	scope moduleScope( module );

	PathClass<RenderPassPath>()
		.def(
			"__init__",
			make_constructor(
				constructor1,
				default_call_policies(),
				(
					boost::python::arg( "scene" ),
					boost::python::arg( "context" ),
					boost::python::arg( "filter" ) = object(),
					boost::python::arg( "grouped" ) = false
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
					boost::python::arg( "filter" ) = object(),
					boost::python::arg( "grouped" ) = false
				)
			)
		)
		.def( "setScene", &RenderPassPath::setScene )
		.def( "getScene", (ScenePlug *(RenderPassPath::*)())&RenderPassPath::getScene, return_value_policy<CastToIntrusivePtr>() )
		.def( "setContext", &RenderPassPath::setContext )
		.def( "getContext", (Context *(RenderPassPath::*)())&RenderPassPath::getContext, return_value_policy<CastToIntrusivePtr>() )
		.def( "registerPathGroupingFunction", &registerPathGroupingFunctionWrapper )
		.staticmethod( "registerPathGroupingFunction" )
		.def( "pathGroupingFunction", &pathGroupingFunctionWrapper )
		.staticmethod( "pathGroupingFunction" )
	;

	RefCountedClass<RenderPassNameColumn, GafferUI::PathColumn>( "RenderPassNameColumn" )
		.def( init<>() )
	;

	RefCountedClass<RenderPassActiveColumn, GafferUI::PathColumn>( "RenderPassActiveColumn" )
		.def( init<>() )
	;

	RefCountedClass<RenderPassEditorSearchFilter, PathFilter>( "SearchFilter" )
		.def( init<IECore::CompoundDataPtr>( ( boost::python::arg( "userData" ) = object() ) ) )
		.def( "setMatchPattern", &RenderPassEditorSearchFilter::setMatchPattern )
		.def( "getMatchPattern", &RenderPassEditorSearchFilter::getMatchPattern, return_value_policy<copy_const_reference>() )
	;

	RefCountedClass<DisabledRenderPassFilter, PathFilter>( "DisabledRenderPassFilter" )
		.def( init<IECore::CompoundDataPtr>( ( boost::python::arg( "userData" ) = object() ) ) )
	;

}
