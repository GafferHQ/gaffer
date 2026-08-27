//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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
//      * Neither the name of Image Engine Design Inc nor the names of
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

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"

namespace GafferScene
{

class GAFFERSCENE_API RandomPrimitiveVariable : public Deformer
{

	public :

		explicit RandomPrimitiveVariable( const std::string &name=defaultName<RandomPrimitiveVariable>() );
		~RandomPrimitiveVariable() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::RandomPrimitiveVariable, RandomPrimitiveVariableTypeId, Deformer );

		enum Distribution
		{
			UniformInt,
			UniformFloat,
			Gaussian,
			WeightedChoice,
			HollowSphere,
		};

		Gaffer::StringPlug *namePlug();
		const Gaffer::StringPlug *namePlug() const;

		Gaffer::IntPlug *interpolationPlug();
		const Gaffer::IntPlug *interpolationPlug() const;

		Gaffer::IntPlug *seedPlug();
		const Gaffer::IntPlug *seedPlug() const;

		Gaffer::StringPlug *seedPrimitiveVariablePlug();
		const Gaffer::StringPlug *seedPrimitiveVariablePlug() const;

		Gaffer::IntPlug *distributionPlug();
		const Gaffer::IntPlug *distributionPlug() const;

		Gaffer::V2iPlug *intRangePlug();
		const Gaffer::V2iPlug *intRangePlug() const;

		Gaffer::V2fPlug *floatRangePlug();
		const Gaffer::V2fPlug *floatRangePlug() const;

		Gaffer::FloatPlug *meanPlug();
		const Gaffer::FloatPlug *meanPlug() const;

		Gaffer::FloatPlug *deviationPlug();
		const Gaffer::FloatPlug *deviationPlug() const;

		Gaffer::ValuePlug *choicesPlug();
		const Gaffer::ValuePlug *choicesPlug() const;

		template<typename T=Gaffer::ValuePlug>
		T *choicesValuesPlug();
		template<typename T=Gaffer::ValuePlug>
		const T *choicesValuesPlug() const;

		Gaffer::FloatVectorDataPlug *choicesWeightsPlug();
		const Gaffer::FloatVectorDataPlug *choicesWeightsPlug() const;

		Gaffer::FloatPlug *radiusPlug();
		const Gaffer::FloatPlug *radiusPlug() const;

		Gaffer::IntPlug *interpretationPlug();
		const Gaffer::IntPlug *interpretationPlug() const;

		/// Sets up the `choicesValuesPlug()`. The name of this
		/// function isn't ideal, but is needed for compatibility
		/// with PlugCreationWidget.
		void setup( const Gaffer::ValuePlug *plug );

	protected :

		bool adjustBounds() const override;

		bool affectsProcessedObject( const Gaffer::Plug *input ) const override;
		void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const override;
		Gaffer::ValuePlug::CachePolicy processedObjectComputeCachePolicy() const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( RandomPrimitiveVariable )

} // namespace GafferScene

#include "GafferScene/RandomPrimitiveVariable.inl"
