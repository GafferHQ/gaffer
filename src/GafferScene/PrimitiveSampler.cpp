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

#include "GafferScene/PrimitiveSampler.h"

#include "GafferScene/SceneAlgo.h"

#include "Gaffer/Private/IECorePreview/ParallelAlgo.h"

#include "IECoreScene/MeshAlgo.h"
#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/PrimitiveEvaluator.h"

#include "tbb/parallel_for.h"

using namespace std;
using namespace tbb;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

using OutputVariableFunction = std::function<void ( size_t, const PrimitiveEvaluator::Result & )>;

M44f matrix( const M44f &transform, GeometricData::Interpretation interpretation )
{
	switch( interpretation )
	{
		case GeometricData::Point :
			return transform;
		case GeometricData::Vector : {
			// Don't apply translation to vectors.
			M44f x = transform;
			x[3][0] = x[3][1] = x[3][2] = 0.0f;
			return x;
		}
		case GeometricData::Normal : {
			// Use the transpose of the inverse
			// for transforming normals. Also,
			// don't apply translation.
			M44f x = transform;
			x[3][0] = x[3][1] = x[3][2] = 0.0f;
			x = x.inverse();
			x.transpose();
			return x;
		}
		default :
			return M44f();
	}
}

OutputVariableFunction addPrimitiveVariable( Primitive *outputPrimitive, const std::string &name, const PrimitiveVariable &sourceVariable, PrimitiveVariable::Interpolation outputInterpolation, const M44f &transform )
{
	const size_t size = outputPrimitive->variableSize( outputInterpolation );
	switch( sourceVariable.data->typeId() )
	{
		case V3fVectorDataTypeId : {
			V3fVectorDataPtr data = new V3fVectorData;
			data->writable().resize( size, V3f( 0 ) );
			const GeometricData::Interpretation interpretation = static_cast<const V3fVectorData *>( sourceVariable.data.get() )->getInterpretation();
			data->setInterpretation( interpretation );
			outputPrimitive->variables[name] = PrimitiveVariable( outputInterpolation, data );
			V3f *d = data->writable().data();
			const M44f m = matrix( transform, interpretation );
			return [d, &sourceVariable, m ] ( size_t index, const PrimitiveEvaluator::Result &result ) {
				d[index] = result.vectorPrimVar( sourceVariable ) * m;
			};
		}
		case V2fVectorDataTypeId : {
			V2fVectorDataPtr data = new V2fVectorData;
			data->writable().resize( size, V2f( 0 ) );
			data->setInterpretation( static_cast<const V2fVectorData *>( sourceVariable.data.get() )->getInterpretation() );
			outputPrimitive->variables[name] = PrimitiveVariable( outputInterpolation, data );
			V2f *d = data->writable().data();
			return [d, &sourceVariable] ( size_t index, const PrimitiveEvaluator::Result &result ) {
				d[index] = result.vec2PrimVar( sourceVariable );
			};
		}
		case Color3fVectorDataTypeId : {
			Color3fVectorDataPtr data = new Color3fVectorData;
			data->writable().resize( size, Color3f( 0 ) );
			outputPrimitive->variables[name] = PrimitiveVariable( outputInterpolation, data );
			Color3f *d = data->writable().data();
			return [d, &sourceVariable] ( size_t index, const PrimitiveEvaluator::Result &result ) {
				d[index] = result.colorPrimVar( sourceVariable );
			};
		}
		case FloatVectorDataTypeId : {
			FloatVectorDataPtr data = new FloatVectorData;
			data->writable().resize( size, 0 );
			outputPrimitive->variables[name] = PrimitiveVariable( outputInterpolation, data );
			float *d = data->writable().data();
			return [d, &sourceVariable] ( size_t index, const PrimitiveEvaluator::Result &result ) {
				d[index] = result.floatPrimVar( sourceVariable );
			};
		}
		case IntVectorDataTypeId : {
			IntVectorDataPtr data = new IntVectorData;
			data->writable().resize( size, 0 );
			outputPrimitive->variables[name] = PrimitiveVariable( outputInterpolation, data );
			int *d = data->writable().data();
			return [d, &sourceVariable] ( size_t index, const PrimitiveEvaluator::Result &result ) {
				d[index] = result.intPrimVar( sourceVariable );
			};
		}
		default :
			// Unsupported type
			return OutputVariableFunction();
	};

}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Sampler
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( PrimitiveSampler );

size_t PrimitiveSampler::g_firstPlugIndex = 0;

PrimitiveSampler::PrimitiveSampler( const std::string &name )
	:	Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ScenePlug( "source" ) );
	addChild( new StringPlug( "sourceLocation" ) );
	addChild( new StringPlug( "primitiveVariables" ) );
	addChild( new StringPlug( "prefix" ) );
	addChild( new StringPlug( "status" ) );
}

PrimitiveSampler::~PrimitiveSampler()
{
}

ScenePlug *PrimitiveSampler::sourcePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *PrimitiveSampler::sourcePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *PrimitiveSampler::sourceLocationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *PrimitiveSampler::sourceLocationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *PrimitiveSampler::primitiveVariablesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *PrimitiveSampler::primitiveVariablesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *PrimitiveSampler::prefixPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *PrimitiveSampler::prefixPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *PrimitiveSampler::statusPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *PrimitiveSampler::statusPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

bool PrimitiveSampler::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		Deformer::affectsProcessedObject( input ) ||
		input == sourcePlug() ||
		input == sourceLocationPlug() ||
		input == primitiveVariablesPlug() ||
		input == prefixPlug() ||
		input == statusPlug() ||
		input == sourcePlug()->objectPlug() ||
		input == inPlug()->transformPlug() ||
		input == sourcePlug()->transformPlug() ||
		affectsSamplingFunction( input )
	;
}

void PrimitiveSampler::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Deformer::hashProcessedObject( path, context, h );

	const string sourceLocation = sourceLocationPlug()->getValue();
	const string primitiveVariables = primitiveVariablesPlug()->getValue();
	const string status = statusPlug()->getValue();
	if( sourceLocation.empty() || ( primitiveVariables.empty() && status.empty() ) )
	{
		return;
	}

	ScenePlug::ScenePath sourcePath;
	ScenePlug::stringToPath( sourceLocation, sourcePath );
	if( !SceneAlgo::exists( sourcePlug(), sourcePath ) )
	{
		return;
	}

	h.append( sourcePlug()->objectHash( sourcePath ) );
	h.append( primitiveVariables );
	prefixPlug()->hash( h );
	h.append( status );
	h.append( inPlug()->fullTransformHash( path ) );
	h.append( sourcePlug()->fullTransformHash( sourcePath ) );
	hashSamplingFunction( h );
}

IECore::ConstObjectPtr PrimitiveSampler::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const Primitive *inputPrimitive = runTimeCast<const Primitive>( inputObject );
	if( !inputPrimitive )
	{
		return inputObject;
	}

	const string sourceLocation = sourceLocationPlug()->getValue();
	const string primitiveVariables = primitiveVariablesPlug()->getValue();
	const string status = statusPlug()->getValue();
	if( sourceLocation.empty() || ( primitiveVariables.empty() && status.empty() ) )
	{
		return inputObject;
	}

	PrimitiveVariable::Interpolation outputInterpolation = PrimitiveVariable::Invalid;
	SamplingFunction samplingFunction = computeSamplingFunction( inputPrimitive, outputInterpolation );
	if( !samplingFunction || outputInterpolation == PrimitiveVariable::Invalid )
	{
		return inputObject;
	}

	ScenePlug::ScenePath sourcePath;
	ScenePlug::stringToPath( sourceLocation, sourcePath );
	if( !SceneAlgo::exists( sourcePlug(), sourcePath ) )
	{
		return inputObject;
	}

	ConstObjectPtr sourceObject = sourcePlug()->object( sourcePath );
	const Primitive *sourcePrimitive = runTimeCast<const Primitive>( sourceObject.get() );
	if( !sourcePrimitive )
	{
		return inputObject;
	}

	ConstPrimitivePtr preprocessedSourcePrimitive = sourcePrimitive;
	if( auto mesh = runTimeCast<const MeshPrimitive>( preprocessedSourcePrimitive.get() ) )
	{
		preprocessedSourcePrimitive = MeshAlgo::triangulate( mesh );
	}
	PrimitiveEvaluatorPtr evaluator = PrimitiveEvaluator::create( preprocessedSourcePrimitive );
	if( !evaluator )
	{
		return inputObject;
	}

	PrimitivePtr outputPrimitive = inputPrimitive->copy();
	const size_t size = outputPrimitive->variableSize( outputInterpolation );

	const string prefix = prefixPlug()->getValue();
	const M44f transform = inPlug()->fullTransform( path );
	const M44f sourceTransform = sourcePlug()->fullTransform( sourcePath );
	const M44f primitiveVariableTransform = sourceTransform * transform.inverse();

	vector<OutputVariableFunction> outputVariables;
	for( auto &p : preprocessedSourcePrimitive->variables )
	{
		if( !StringAlgo::matchMultiple( p.first, primitiveVariables ) )
		{
			continue;
		}

		if( auto o = addPrimitiveVariable( outputPrimitive.get(), prefix + p.first, p.second, outputInterpolation, primitiveVariableTransform ) )
		{
			outputVariables.push_back( o );
		}
	}

	BoolVectorDataPtr statusData;
	if( !status.empty() )
	{
		statusData = new BoolVectorData();
		statusData->writable().resize( size, false );
		outputPrimitive->variables[status] = PrimitiveVariable( outputInterpolation, statusData );
	}

	const M44f samplingTransform = transform * sourceTransform.inverse();

	auto rangeSampler = [&]( const blocked_range<size_t> &r ) {
		PrimitiveEvaluator::ResultPtr evaluatorResult = evaluator->createResult();
		for( size_t i = r.begin(); i != r.end(); ++i )
		{
			Canceller::check( context->canceller() );
			if( samplingFunction( *evaluator, i, samplingTransform, *evaluatorResult ) )
			{
				for( const auto &o : outputVariables )
				{
					o( i, *evaluatorResult );
				}
				if( statusData )
				{
					statusData->writable()[i] = true;
				}
			}
		}
	};

	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );
	parallel_for( blocked_range<size_t>( 0, size ), rangeSampler, taskGroupContext );

	return outputPrimitive;
}

Gaffer::ValuePlug::CachePolicy PrimitiveSampler::processedObjectComputeCachePolicy() const
{
	return ValuePlug::CachePolicy::TaskCollaboration;
}

bool PrimitiveSampler::adjustBounds() const
{
	return
		Deformer::adjustBounds() &&
		prefixPlug()->getValue().empty() &&
		StringAlgo::matchMultiple( "P", primitiveVariablesPlug()->getValue() )
	;
}

bool PrimitiveSampler::affectsSamplingFunction( const Gaffer::Plug *input ) const
{
	return false;
}

void PrimitiveSampler::hashSamplingFunction( IECore::MurmurHash &h ) const
{
}

