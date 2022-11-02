//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERSCENE_SCENEREADER_H
#define GAFFERSCENE_SCENEREADER_H

#include "GafferScene/SceneNode.h"

#include "IECoreScene/SceneInterface.h"

#include "tbb/enumerable_thread_specific.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )
IE_CORE_FORWARDDECLARE( TransformPlug )

} // namespace Gaffer

namespace GafferScene
{

class GAFFERSCENE_API SceneReader : public SceneNode
{

	public :

		SceneReader( const std::string &name=defaultName<SceneReader>() );
		~SceneReader() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::SceneReader, SceneReaderTypeId, SceneNode )

		/// Holds the name of the file to be loaded.
		Gaffer::StringPlug *fileNamePlug();
		const Gaffer::StringPlug *fileNamePlug() const;

		/// Number of times the node has been refreshed.
		Gaffer::IntPlug *refreshCountPlug();
		const Gaffer::IntPlug *refreshCountPlug() const;

		Gaffer::StringPlug *tagsPlug();
		const Gaffer::StringPlug *tagsPlug() const;

		Gaffer::TransformPlug *transformPlug();
		const Gaffer::TransformPlug *transformPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

		static size_t supportedExtensions( std::vector<std::string> &extensions );

	protected :

		/// \todo These methods defer to SceneInterface::hash() to do most of the work, but we could go further.
		/// Currently we still hash in fileNamePlug() and refreshCountPlug() because we don't trust the current
		/// implementation of SceneCache::hash() - it should hash the filename and modification time, but instead
		/// it hashes some pointer value which isn't guaranteed to be unique (see sceneHash() in IECore/SceneCache.cpp).
		/// Additionally, we don't have a way of hashing in the tags, which we would need in hashChildNames().
		void hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;

		Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstInternedStringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstCompoundObjectPtr computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstInternedStringVectorDataPtr computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstPathMatcherDataPtr computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const override;

	private :

		void plugSet( Gaffer::Plug *plug );

		// The typical access patterns for the SceneReader include accessing
		// the same file repeatedly, and also the same path within the file
		// repeatedly (to hash a value then compute it for instance, or to get
		// the bound and then the object). We take advantage of that by storing
		// the last accessed scene in thread local storage - we can then avoid
		// the relatively expensive lookups necessary to find the appropriate
		// SceneInterfacePtr for a query.
		struct LastScene
		{
			std::string fileName;
			IECoreScene::ConstSceneInterfacePtr fileNameScene;
			ScenePlug::ScenePath path;
			IECoreScene::ConstSceneInterfacePtr pathScene;
		};
		mutable tbb::enumerable_thread_specific<LastScene> m_lastScene;
		// Returns the SceneInterface for the current filename (in the current Context)
		// and specified path, using m_lastScene to accelerate the lookups.
		IECoreScene::ConstSceneInterfacePtr scene( const ScenePath &path ) const;

		static const double g_frameRate;
		static size_t g_firstPlugIndex;

		// SceneInterface has two different APIs related to sets : the legacy tags API and the
		// new sets API. We prefer the sets API for standard formats like Alembic and USD, but
		// fall back to the tags API for legacy SceneInterfaces.
		friend class SceneWriter;
		static bool useSetsAPI( const IECoreScene::SceneInterface *scene );

};

IE_CORE_DECLAREPTR( SceneReader )

} // namespace GafferScene

#endif // GAFFERSCENE_SCENEREADER_H
