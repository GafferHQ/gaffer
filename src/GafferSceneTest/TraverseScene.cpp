//////////////////////////////////////////////////////////////////////////
//
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

#include "tbb/task.h"

#include "GafferSceneTest/TraverseScene.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace GafferSceneTest
{
namespace Detail
{

class SceneTraversalTask : public tbb::task
{

	public :

		SceneTraversalTask( ScenePlug *scenePlug, Gaffer::Context *context, const ScenePlug::ScenePath &scenePath )
			:	m_scenePlug( scenePlug ), m_context( context ), m_scenePath( scenePath )
		{
		}

		virtual ~SceneTraversalTask()
		{
		}

		virtual task *execute()
		{

			ContextPtr context = new Context( *m_context, Context::Borrowed );
			context->set( ScenePlug::scenePathContextName, m_scenePath );
			Context::Scope scopedContext( context.get() );

			m_scenePlug->transformPlug()->getValue();
			m_scenePlug->boundPlug()->getValue();
			m_scenePlug->attributesPlug()->getValue();
			m_scenePlug->objectPlug()->getValue();

			ConstInternedStringVectorDataPtr childNamesData = m_scenePlug->childNamesPlug()->getValue();
			const vector<InternedString> &childNames = childNamesData->readable();

			set_ref_count( 1 + childNames.size() );

			ScenePlug::ScenePath childPath = m_scenePath;
			childPath.push_back( InternedString() ); // space for the child name
			for( vector<InternedString>::const_iterator it = childNames.begin(), eIt = childNames.end(); it != eIt; it++ )
			{
				childPath[m_scenePath.size()] = *it;
				SceneTraversalTask *t = new( allocate_child() ) SceneTraversalTask( m_scenePlug, m_context, childPath );
				spawn( *t );
			}

			wait_for_all();

			return 0;
		}

	private :

		ScenePlug *m_scenePlug;
		Context *m_context;
		ScenePlug::ScenePath m_scenePath;

};

} // namespace Detail

void traverseScene( GafferScene::ScenePlug *scenePlug, Gaffer::Context *context )
{
	Detail::SceneTraversalTask *task = new( tbb::task::allocate_root() ) Detail::SceneTraversalTask( scenePlug, context, ScenePlug::ScenePath() );
	tbb::task::spawn_root_and_wait( *task );
}

} // namespace GafferSceneTest
