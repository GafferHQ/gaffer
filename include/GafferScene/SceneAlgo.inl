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

#include "tbb/spin_mutex.h"
#include "tbb/task.h"
#include "tbb/parallel_for.h"

#include "IECore/MatrixMotionTransform.h"
#include "IECore/Camera.h"

#include "Gaffer/Context.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/Filter.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/PathMatcher.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace GafferScene
{

namespace
{

template <class ThreadableFunctor>
class FilteredTraverseTask : public tbb::task
{

	public :

		FilteredTraverseTask(
			const Gaffer::IntPlug *filter,
			const ScenePlug *scene,
			const Gaffer::Context *context,
			ThreadableFunctor &f
		)
			:	m_filter( filter ), m_scene( scene ), m_context( context ), m_f( f )
		{
		}

		virtual ~FilteredTraverseTask()
		{
		}

		virtual task *execute()
		{

			ContextPtr context = new Context( *m_context, Context::Borrowed );
			context->set( ScenePlug::scenePathContextName, m_path );
			Context::Scope scopedContext( context.get() );

			const Filter::Result match = (Filter::Result)m_filter->getValue();
			if( match & Filter::ExactMatch )
			{
				m_f( m_path );
			}

			if( match & Filter::DescendantMatch )
			{
				ConstInternedStringVectorDataPtr childNamesData = m_scene->childNamesPlug()->getValue();
				const vector<InternedString> &childNames = childNamesData->readable();

				set_ref_count( 1 + childNames.size() );

				ScenePlug::ScenePath childPath = m_path;
				childPath.push_back( InternedString() ); // space for the child name
				for( vector<InternedString>::const_iterator it = childNames.begin(), eIt = childNames.end(); it != eIt; it++ )
				{
					childPath[m_path.size()] = *it;
					FilteredTraverseTask *t = new( allocate_child() ) FilteredTraverseTask( *this, childPath );
					spawn( *t );
				}
				wait_for_all();
			}

			return NULL;
		}

	protected :

		FilteredTraverseTask( const FilteredTraverseTask &other, const ScenePlug::ScenePath &path )
			:	m_filter( other.m_filter ),
				m_scene( other.m_scene ),
				m_context( other.m_context ),
				m_f( other.m_f ),
				m_path( path )
		{
		}

	private :

		const IntPlug *m_filter;
		const ScenePlug *m_scene;
		const Context *m_context;
		ThreadableFunctor &m_f;
		ScenePlug::ScenePath m_path;

};

} // namespace

template <class ThreadableFunctor>
void filteredParallelTraverse( const Filter *filter, const ScenePlug *scene, ThreadableFunctor &f )
{
	filteredParallelTraverse( filter->outPlug(), scene, f );
}

template <class ThreadableFunctor>
void filteredParallelTraverse( const Gaffer::IntPlug *filterPlug, const ScenePlug *scene, ThreadableFunctor &f )
{
	ContextPtr context = new Context( *Context::current(), Context::Borrowed );
	Filter::setInputScene( context.get(), scene );
	FilteredTraverseTask<ThreadableFunctor> *task = new( tbb::task::allocate_root() ) FilteredTraverseTask<ThreadableFunctor>( filterPlug, scene, context.get(), f );
	tbb::task::spawn_root_and_wait( *task );
}

}
