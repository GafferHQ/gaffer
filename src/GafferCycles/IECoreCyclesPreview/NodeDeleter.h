//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#pragma once

#include "IECore/Export.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "scene/geometry.h"
#include "scene/object.h"
#include "scene/scene.h"
IECORE_POP_DEFAULT_VISIBILITY

namespace IECoreCycles
{

// `ccl::Scene::delete_node()` is the official way of removing a node from the
// scene and deleting it. It is specialised for each node type so that it also
// tags the appropriate object manager for update. In an ideal world we would
// just call it whenever we need to delete a node.
//
// But a single call to `delete_node()` is `O(n)` in the number of nodes in the
// scene, making deletion of all nodes `O(n^2)`, which is unacceptable for large
// scenes. The NodeDeleter class allows us to batch up deletions and use a single
// call to the more performant `ccl::Scene::delete_nodes()` method to delete
// multiple nodes at once.
struct NodeDeleter
{

	NodeDeleter( ccl::Scene *scene )
		:	m_scene( scene )
	{
	}

	// Deleter for use with `std::shared_ptr` and `std::unique_ptr`.
	template<typename T>
	struct Deleter
	{

		Deleter( NodeDeleter *nodeDeleter = nullptr )
			:	m_nodeDeleter( nodeDeleter )
		{
		}

		void operator()( T *node ) const
		{
			if( m_nodeDeleter )
			{
				m_nodeDeleter->scheduleDeletion( node );
			}
		}

		private :

			NodeDeleter *m_nodeDeleter;

	};

	using GeometryDeleter = Deleter<ccl::Geometry>;
	using ObjectDeleter = Deleter<ccl::Object>;

	void doPendingDeletions()
	{
		std::lock_guard lock( m_mutex );
		std::lock_guard sceneLock( m_scene->mutex );

		if( m_pendingObjectDeletions.size() )
		{
			m_scene->delete_nodes( m_pendingObjectDeletions );
			m_pendingObjectDeletions.clear();
		}
		if( m_pendingGeometryDeletions.size() )
		{
			m_scene->delete_nodes( m_pendingGeometryDeletions );
			m_pendingGeometryDeletions.clear();
		}
	}

	private :

		void scheduleDeletion( ccl::Object *object )
		{
			std::lock_guard lock( m_mutex );
			m_pendingObjectDeletions.insert( object );
		}

		void scheduleDeletion( ccl::Geometry *geometry )
		{
			std::lock_guard lock( m_mutex );
			m_pendingGeometryDeletions.insert( geometry );
		}

		ccl::Scene *m_scene;

		std::mutex m_mutex;
		std::set<ccl::Object *> m_pendingObjectDeletions;
		std::set<ccl::Geometry *> m_pendingGeometryDeletions;

};

} // namespace IECoreCycles
