//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, John Haddon. All rights reserved.
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

#include "GafferScene/Deformer.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/PrimitiveEvaluator.h"

namespace GafferScene
{

/// Base class for nodes which use an `IECoreScene::PrimitiveEvaluator`
/// to sample primitive variables from another object.
class GAFFERSCENE_API PrimitiveSampler : public Deformer
{

	public :

		~PrimitiveSampler() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::PrimitiveSampler, PrimitiveSamplerTypeId, Deformer );

		ScenePlug *sourcePlug();
		const ScenePlug *sourcePlug() const;

		Gaffer::StringPlug *sourceLocationPlug();
		const Gaffer::StringPlug *sourceLocationPlug() const;

		Gaffer::StringPlug *primitiveVariablesPlug();
		const Gaffer::StringPlug *primitiveVariablesPlug() const;

		Gaffer::StringPlug *prefixPlug();
		const Gaffer::StringPlug *prefixPlug() const;

		Gaffer::StringPlug *statusPlug();
		const Gaffer::StringPlug *statusPlug() const;

	protected :

		explicit PrimitiveSampler( const std::string &name = defaultName<PrimitiveSampler>() );

		/// SamplingFunction
		/// ================
		///
		/// Derived classes are responsible for generating a `SamplingFunction`, which
		/// performs an `IECoreScene::PrimitiveEvaluator` query for a single index within the
		/// destination primitive. The base class takes care of everything else.

		using SamplingFunction = std::function<bool (
			/// The PrimitiveEvaluator to use for sampling
			/// the source primitive.
			const IECoreScene::PrimitiveEvaluator &evaluator,
			/// The index within the destination primitive to
			/// sample for.
			size_t index,
			/// A transform that must be applied to any geometric
			/// data before querying the `evaluator`. This converts
			/// from the object space of the destination primitive into
			/// the object space of the source primitive.
			const Imath::M44f &transform,
			/// The destination for the result of the `evaluator`
			/// query.
			IECoreScene::PrimitiveEvaluator::Result &result
		)>;

		/// Must be implemented to return true if the specified plug affects the
		/// generation of the `SamplingFunction`. All implementations should call
		/// the base implementation first, and return `true` if it does.
		virtual bool affectsSamplingFunction( const Gaffer::Plug *input ) const = 0;
		/// Must be implemented to hash all plugs that are used in `computeSamplingFunction()`.
		/// All implementation should call the base class implementation first.
		virtual void hashSamplingFunction( IECore::MurmurHash &h ) const = 0;
		/// Must be implemented to return a `SamplingFunction` that will perform queries
		/// on behalf of the destination primitive. The `interpolation` output parameter
		/// must be filled with the interpolation of the primitive variables to be added
		/// to the destination primitive. The sampling function will then be queried with
		/// `index` values in the interval `[ 0, destinationPrimitive->variableSize( interpolation ) )`.
		virtual SamplingFunction computeSamplingFunction( const IECoreScene::Primitive *destinationPrimitive, IECoreScene::PrimitiveVariable::Interpolation &interpolation ) const = 0;

	private :

		bool affectsProcessedObject( const Gaffer::Plug *input ) const final;
		void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const final;
		IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const final;
		Gaffer::ValuePlug::CachePolicy processedObjectComputeCachePolicy() const final;

		bool adjustBounds() const final;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( PrimitiveSampler )

} // namespace GafferScene
