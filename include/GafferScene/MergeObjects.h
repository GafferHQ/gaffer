//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "GafferScene/FilteredSceneProcessor.h"

#include "Gaffer/TypedObjectPlug.h"

#include "IECore/CompoundData.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferScene
{

/// A base class for scene nodes that merge locations into combined
/// locations. Appropriate for nodes which merge primitives, or convert
/// transforms to points.
///
/// All source locations are merged into their corresponding destination
/// locations, creating the destination if it doesn't exist already. Then
/// all source locations that are not also a destination are pruned.
/// `destination` may depend on `scene:path` to give a unique destination
/// to each filtered source, allowing arbitrary rearrangements of the
/// hierarchy.
///
/// Derived classes just need to implement `mergeObjects()` to do the actual
/// merge.
class GAFFERSCENE_API MergeObjects : public FilteredSceneProcessor
{

	public :

		~MergeObjects() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::MergeObjects, MergeObjectsTypeId, FilteredSceneProcessor );

		GafferScene::ScenePlug *sourcePlug();
		const GafferScene::ScenePlug *sourcePlug() const;

		Gaffer::StringPlug *destinationPlug();
		const Gaffer::StringPlug *destinationPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		MergeObjects( const std::string &name, const std::string &defaultDestination );

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		void hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;
		void hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const override;

		Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstInternedStringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const override;
		IECore::ConstPathMatcherDataPtr computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const override;

		Gaffer::ValuePlug::CachePolicy hashCachePolicy( const Gaffer::ValuePlug *output ) const override;
		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;


		/// @name Actual object merge function
		/// This must be implemented by derived classes. It receives a vector of pairs of objects
		/// and the transform that maps each object into the shared space of the output location.
		///
		virtual IECore::ConstObjectPtr mergeObjects(
			const std::vector< std::pair< IECore::ConstObjectPtr, Imath::M44f > > &sources,
			const Gaffer::Context *context
		) const = 0;

		// \todo - should we offer alternate ways to merge bounds? Can we think of any use cases for this?
		//virtual Imath::Box3f mergeBounds( const std::vector< ScenePath > &sourcePaths, const Gaffer::Context *context ) const;

	protected:

		/// The source plug currently being used for merge sources - will be `source` if connected, otherwise
		/// `in`.
		const GafferScene::ScenePlug *effectiveSourcePlug() const;

	private :

		/// The tree holds all destinations, with their corresponding sources.
		Gaffer::ObjectPlug *treePlug();
		const Gaffer::ObjectPlug *treePlug() const;

		/// The mergeLocation data gives the resulting child names for each location, together with which
		/// sources are needed to evaluate the child locations.
		Gaffer::ObjectPlug *mergeLocationPlug();
		const Gaffer::ObjectPlug *mergeLocationPlug() const;

		/// We use a separate plug for actually computing the object so that we can use TaskCollaboration
		/// for actual merges, but not for pass-throughs
		Gaffer::ObjectPlug *processedObjectPlug();
		const Gaffer::ObjectPlug *processedObjectPlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( MergeObjects )

} // namespace GafferScene
