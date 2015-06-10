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

#include "tbb/task.h"
#include "Gaffer/Context.h"

namespace GafferScene
{

namespace Detail
{

template <class ThreadableFunctor>
class TraverseTask : public tbb::task
{

	public :

		TraverseTask(
			const GafferScene::ScenePlug *scene,
			const Gaffer::Context *context,
			ThreadableFunctor &f
		)
			:	m_scene( scene ), m_context( context ), m_f( f )
		{
		}

		virtual ~TraverseTask()
		{
		}

		virtual task *execute()
		{

			Gaffer::ContextPtr context = new Gaffer::Context( *m_context, Gaffer::Context::Borrowed );
			context->set( ScenePlug::scenePathContextName, m_path );
			Gaffer::Context::Scope scopedContext( context.get() );

			if( m_f( m_scene, m_path ) )
			{
				IECore::ConstInternedStringVectorDataPtr childNamesData = m_scene->childNamesPlug()->getValue();
				const std::vector<IECore::InternedString> &childNames = childNamesData->readable();

				set_ref_count( 1 + childNames.size() );

				ScenePlug::ScenePath childPath = m_path;
				childPath.push_back( IECore::InternedString() ); // space for the child name
				for( std::vector<IECore::InternedString>::const_iterator it = childNames.begin(), eIt = childNames.end(); it != eIt; it++ )
				{
					childPath[m_path.size()] = *it;
					TraverseTask *t = new( allocate_child() ) TraverseTask( *this, childPath );
					spawn( *t );
				}
				wait_for_all();
			}

			return NULL;
		}

	protected :

		TraverseTask( const TraverseTask &other, const ScenePlug::ScenePath &path )
			:	m_scene( other.m_scene ),
				m_context( other.m_context ),
				m_f( other.m_f ),
				m_path( path )
		{
		}

	private :

		const GafferScene::ScenePlug *m_scene;
		const Gaffer::Context *m_context;
		ThreadableFunctor &m_f;
		GafferScene::ScenePlug::ScenePath m_path;

};

template <class ThreadableFunctor>
struct ThreadableFilteredFunctor
{
    ThreadableFilteredFunctor( ThreadableFunctor &f, const Gaffer::IntPlug *filter ): m_f( f ), m_filter( filter ){}

    bool operator()( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &path )
    {
		const GafferScene::Filter::Result match = (GafferScene::Filter::Result)m_filter->getValue();
		if( match & GafferScene::Filter::ExactMatch )
		{
			if( !m_f( scene, path ) ) return false;
		}

		return ( match & GafferScene::Filter::DescendantMatch ) != 0;
    }

	ThreadableFunctor &m_f;
	const Gaffer::IntPlug *m_filter;

};

} // namespace

template <class ThreadableFunctor>
void parallelTraverse( const GafferScene::ScenePlug *scene, ThreadableFunctor &f )
{
	Gaffer::ContextPtr c = new Gaffer::Context( *Gaffer::Context::current(), Gaffer::Context::Borrowed );
	GafferScene::Filter::setInputScene( c.get(), scene );
	Detail::TraverseTask<ThreadableFunctor> *task = new( tbb::task::allocate_root() ) Detail::TraverseTask<ThreadableFunctor>( scene, c.get(), f );
	tbb::task::spawn_root_and_wait( *task );
}

template <class ThreadableFunctor>
void filteredParallelTraverse( const GafferScene::ScenePlug *scene, const GafferScene::Filter *filter, ThreadableFunctor &f )
{
	filteredParallelTraverse( scene, filter->outPlug(), f );
}

template <class ThreadableFunctor>
void filteredParallelTraverse( const GafferScene::ScenePlug *scene, const Gaffer::IntPlug *filterPlug, ThreadableFunctor &f )
{
	Detail::ThreadableFilteredFunctor<ThreadableFunctor> ff( f, filterPlug );
	parallelTraverse( scene, ff );
}

}
