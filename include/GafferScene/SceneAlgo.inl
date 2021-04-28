//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Context.h"

#include "tbb/parallel_for.h"

namespace GafferScene
{

namespace Detail
{

template<typename ThreadableFunctor>
void parallelProcessLocationsWalk( const GafferScene::ScenePlug *scene, const Gaffer::ThreadState &threadState, const ScenePlug::ScenePath &path, ThreadableFunctor &f, tbb::task_group_context &taskGroupContext )
{
	ScenePlug::PathScope pathScope( threadState, &path );

	if( !f( scene, path ) )
	{
		return;
	}

	IECore::ConstInternedStringVectorDataPtr childNamesData = scene->childNamesPlug()->getValue();
	const std::vector<IECore::InternedString> &childNames = childNamesData->readable();
	if( childNames.empty() )
	{
		return;
	}

	using ChildNameRange = tbb::blocked_range<std::vector<IECore::InternedString>::const_iterator>;
	const ChildNameRange loopRange( childNames.begin(), childNames.end() );

	auto loopBody = [&] ( const ChildNameRange &range ) {
		ScenePlug::ScenePath childPath = path;
		childPath.push_back( IECore::InternedString() ); // Space for the child name
		for( auto &childName : range )
		{
			ThreadableFunctor childFunctor( f );
			childPath.back() = childName;
			parallelProcessLocationsWalk( scene, threadState, childPath, childFunctor, taskGroupContext );
		}
	};

	if( childNames.size() > 1 )
	{
		tbb::parallel_for( loopRange, loopBody, taskGroupContext );
	}
	else
	{
		// Serial execution
		loopBody( loopRange );
	}
}

template <class ThreadableFunctor>
struct ThreadableFilteredFunctor
{
	ThreadableFilteredFunctor( ThreadableFunctor &f, const GafferScene::FilterPlug *filter ): m_f( f ), m_filter( filter ){}

	bool operator()( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &path )
	{
		IECore::PathMatcher::Result match = (IECore::PathMatcher::Result)m_filter->match( scene );

		if( match & IECore::PathMatcher::ExactMatch )
		{
			if( !m_f( scene, path ) )
			{
				return false;
			}
		}

		return ( match & IECore::PathMatcher::DescendantMatch ) != 0;
	}

	ThreadableFunctor &m_f;
	const FilterPlug *m_filter;

};

template<class ThreadableFunctor>
struct PathMatcherFunctor
{

	PathMatcherFunctor( ThreadableFunctor &f, const IECore::PathMatcher &filter )
		: m_f( f ), m_filter( filter )
	{
	}

	bool operator()( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &path )
	{
		const unsigned match = m_filter.match( path );
		if( match & IECore::PathMatcher::ExactMatch )
		{
			if( !m_f( scene, path ) )
			{
				return false;
			}
		}

		return match & IECore::PathMatcher::DescendantMatch;
	}

	private :

		ThreadableFunctor &m_f;
		const IECore::PathMatcher &m_filter;

};

} // namespace Detail

namespace SceneAlgo
{

template <class ThreadableFunctor>
void parallelProcessLocations( const GafferScene::ScenePlug *scene, ThreadableFunctor &f, const ScenePlug::ScenePath &root )
{
	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated ); // Prevents outer tasks silently cancelling our tasks
	Detail::parallelProcessLocationsWalk( scene, Gaffer::ThreadState::current(), root, f, taskGroupContext );
}

template <class ThreadableFunctor>
void parallelTraverse( const ScenePlug *scene, ThreadableFunctor &f, const ScenePlug::ScenePath &root )
{
	// `parallelProcessLocations()` takes a copy of the functor at each location, whereas
	// `parallelTraverse()` is intended to use the same functor for all locations. Wrap the
	// functor in a cheap-to-copy lambda, so that the functor itself won't be copied.
	auto reference = [&f] ( const ScenePlug *scene, const ScenePlug::ScenePath &path ) {
		return f( scene, path );
	};
	parallelProcessLocations( scene, reference, root );
}

template <class ThreadableFunctor>
void filteredParallelTraverse( const ScenePlug *scene, const GafferScene::FilterPlug *filterPlug, ThreadableFunctor &f, const ScenePlug::ScenePath &root )
{
	Detail::ThreadableFilteredFunctor<ThreadableFunctor> ff( f, filterPlug );
	parallelTraverse( scene, ff, root );
}

template <class ThreadableFunctor>
void filteredParallelTraverse( const ScenePlug *scene, const IECore::PathMatcher &filter, ThreadableFunctor &f, const ScenePlug::ScenePath &root )
{
	Detail::PathMatcherFunctor<ThreadableFunctor> ff( f, filter );
	parallelTraverse( scene, ff, root );
}

} // namespace SceneAlgo

} // namespace GafferScene
