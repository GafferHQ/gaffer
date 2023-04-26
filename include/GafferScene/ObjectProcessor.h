//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, John Haddon. All rights reserved.
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

namespace GafferScene
{

/// Base class for nodes which manipulate objects (geometry, cameras etc)
/// in some way.
///
/// > Note : If the processing modifies the bounding box of the object,
/// > the Deformer base class should be used instead.
class GAFFERSCENE_API ObjectProcessor : public FilteredSceneProcessor
{

	public :

		~ObjectProcessor() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::ObjectProcessor, ObjectProcessorTypeId, FilteredSceneProcessor );

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		/// Constructs with a single input ScenePlug named "in". Use inPlug()
		/// to access this plug.
		explicit ObjectProcessor( const std::string &name );
		/// Constructs with an ArrayPlug called "in". Use inPlug() as a
		/// convenience for accessing the first child in the array, and use
		/// inPlugs() to access the array itself.
		ObjectProcessor( const std::string &name, size_t minInputs, size_t maxInputs = std::numeric_limits<size_t>::max() );

		/// Must be implemented by derived classes to return true if `input` is used
		/// by `computeProcessedObject()`. Overrides must start by calling the base
		/// class first, and return true if it returns true.
		virtual bool affectsProcessedObject( const Gaffer::Plug *input ) const = 0;
		/// Must be implemented by derived classes to do one of the following :
		///
		/// - Call `ObjectProcessor::hashProcessedObject()` and then append to the hash with all plugs used in `computeProcessedObject()`.
		/// - Assign `h = inPlug()->objectPlug()->hash()` to signify that `computeProcessedObject()` will pass through `inputObject`
		///   unchanged.
		virtual void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		/// Must be implemented by derived classes to return the processed object.
		virtual IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const = 0;
		/// Must be implemented to return an appropriate policy if `computeProcessedObject()` spawns
		/// TBB tasks. The default implementation returns `ValuePlug::CachePolicy::Legacy`.
		virtual Gaffer::ValuePlug::CachePolicy processedObjectComputeCachePolicy() const;

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;
		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;

	private :

		void init();

		/// We compute the processed object on this internal plug rather than on
		/// `out.object` directly. This allows us to use the TaskCollaboration
		/// task policy for processing objects without paying the overhead when
		/// we're just passing them through (when the filter doesn't match).
		Gaffer::ObjectPlug *processedObjectPlug();
		const Gaffer::ObjectPlug *processedObjectPlug() const;

		void hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const final;
		IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const final;

		/// Private constructor and friendship for old nodes which are filtered to everything
		/// by default. This was a mistake, and we want to ensure that we don't repeat the mistake
		/// for new nodes.
		ObjectProcessor( const std::string &name, IECore::PathMatcher::Result filterDefault );
		friend class MeshType;
		friend class MapOffset;
		friend class MapProjection;
		friend class MeshTangents;
		friend class PointsType;
		friend class PrimitiveVariables;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ObjectProcessor )

} // namespace GafferScene
