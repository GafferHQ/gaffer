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

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePlug.h"

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
using namespace GafferScene;

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

		boost::signals::scoped_connection m_plugDirtiedConnection;
		boost::signals::scoped_connection m_contextChangedConnection;

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

}
