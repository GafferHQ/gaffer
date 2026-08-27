//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, John Haddon. All rights reserved.
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

#include "boost/python.hpp"

#include "PrimitiveVariablesBinding.h"

#include "GafferBindings/DependencyNodeBinding.h"

#include "GafferScene/CollectPrimitiveVariables.h"
#include "GafferScene/DeletePrimitiveVariables.h"
#include "GafferScene/MapOffset.h"
#include "GafferScene/MapProjection.h"
#include "GafferScene/PrimitiveVariableExists.h"
#include "GafferScene/PrimitiveVariables.h"
#include "GafferScene/PrimitiveVariableTweaks.h"
#include "GafferScene/PrimitiveVariableType.h"
#include "GafferScene/QuantizePrimitiveVariables.h"
#include "GafferScene/RandomPrimitiveVariable.h"
#include "GafferScene/ResamplePrimitiveVariables.h"
#include "GafferScene/ShufflePrimitiveVariables.h"

using namespace GafferBindings;
using namespace GafferScene;

namespace
{

void setupBinding( RandomPrimitiveVariable &n, Gaffer::ValuePlug &p )
{
	IECorePython::ScopedGILRelease gilRelease;
	n.setup( &p );
}

class RandomPrimitiveVariableSerialiser : public NodeSerialiser
{

	std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
	{
		std::string result = NodeSerialiser::postConstructor( graphComponent, identifier, serialisation );

		auto valuesPlug = static_cast<const RandomPrimitiveVariable *>( graphComponent )->choicesValuesPlug();
		if( !valuesPlug )
		{
			// `setup()` hasn't been called yet.
			return result;
		}

		if( result.size() )
		{
			result += "\n";
		}

		// Add a call to `setup()` to recreate the plugs.

		const Serialiser *plugSerialiser = Serialisation::acquireSerialiser( valuesPlug );
		result += identifier + ".setup( " + plugSerialiser->constructor( valuesPlug, serialisation ) + " )\n";

		return result;
	}

};

} // namespace

void GafferSceneModule::bindPrimitiveVariables()
{

	GafferBindings::DependencyNodeClass<PrimitiveVariableProcessor>();
	GafferBindings::DependencyNodeClass<DeletePrimitiveVariables>();
	GafferBindings::DependencyNodeClass<PrimitiveVariables>();
	GafferBindings::DependencyNodeClass<ResamplePrimitiveVariables>();
	GafferBindings::DependencyNodeClass<MapProjection>();
	GafferBindings::DependencyNodeClass<MapOffset>();
	GafferBindings::DependencyNodeClass<CollectPrimitiveVariables>();
	GafferBindings::DependencyNodeClass<PrimitiveVariableExists>();
	GafferBindings::DependencyNodeClass<ShufflePrimitiveVariables>();
	GafferBindings::DependencyNodeClass<QuantizePrimitiveVariables>();

	{
		boost::python::scope tweaksScope = GafferBindings::DependencyNodeClass<PrimitiveVariableTweaks>();

		boost::python::enum_<PrimitiveVariableTweaks::SelectionMode>( "SelectionMode" )
			.value( "All", PrimitiveVariableTweaks::SelectionMode::All )
			.value( "IdList", PrimitiveVariableTweaks::SelectionMode::IdList )
			.value( "IdListPrimitiveVariable", PrimitiveVariableTweaks::SelectionMode::IdListPrimitiveVariable )
			.value( "MaskPrimitiveVariable", PrimitiveVariableTweaks::SelectionMode::MaskPrimitiveVariable )
		;
	}

	{
		GafferBindings::DependencyNodeClass<RandomPrimitiveVariable> randomClass;
		boost::python::scope s = randomClass;

		boost::python::enum_<RandomPrimitiveVariable::Distribution>( "Distribution" )
			.value( "UniformInt", RandomPrimitiveVariable::Distribution::UniformInt )
			.value( "UniformFloat", RandomPrimitiveVariable::Distribution::UniformFloat )
			.value( "Gaussian", RandomPrimitiveVariable::Distribution::Gaussian )
			.value( "WeightedChoice", RandomPrimitiveVariable::Distribution::WeightedChoice )
			.value( "HollowSphere", RandomPrimitiveVariable::Distribution::HollowSphere )
		;

		randomClass.def( "setup", &setupBinding );

		Serialisation::registerSerialiser( RandomPrimitiveVariable::staticTypeId(), new RandomPrimitiveVariableSerialiser );
	}

	{
		boost::python::scope s = GafferBindings::DependencyNodeClass<PrimitiveVariableType>();

		boost::python::enum_<PrimitiveVariableType::ElementType>( "ElementType" )
			.value( "UChar", PrimitiveVariableType::ElementType::UChar )
			.value( "Int", PrimitiveVariableType::ElementType::Int )
			.value( "UInt", PrimitiveVariableType::ElementType::UInt )
			.value( "Int64", PrimitiveVariableType::ElementType::Int64 )
			.value( "UInt64", PrimitiveVariableType::ElementType::UInt64 )
			.value( "Half", PrimitiveVariableType::ElementType::Half )
			.value( "Float", PrimitiveVariableType::ElementType::Float )
			.value( "Double", PrimitiveVariableType::ElementType::Double )
			.value( "V2i", PrimitiveVariableType::ElementType::V2i )
			.value( "V2f", PrimitiveVariableType::ElementType::V2f )
			.value( "V2d", PrimitiveVariableType::ElementType::V2d )
			.value( "V3i", PrimitiveVariableType::ElementType::V3i )
			.value( "V3f", PrimitiveVariableType::ElementType::V3f )
			.value( "V3d", PrimitiveVariableType::ElementType::V3d )
			.value( "Color3f", PrimitiveVariableType::ElementType::Color3f )
			.value( "Color4f", PrimitiveVariableType::ElementType::Color4f )
		;
	}
}
