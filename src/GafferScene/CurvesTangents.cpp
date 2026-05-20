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

#include "GafferScene/CurvesTangents.h"

#include "Gaffer/ThreadState.h"

#include "IECoreScene/CurvesAlgo.h"
#include "IECoreScene/CurvesPrimitive.h"

#include "IECore/Canceller.h"
#include "IECore/VectorTypedData.h"

#include "tbb/blocked_range.h"
#include "tbb/parallel_for.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

/// \todo Feels like it'd be useful to expose this somewhere in Cortex.
array<V3f, 4> segmentPoints( PrimitiveVariable::IndexedView<V3f> &points, size_t segmentIndex, size_t numSegments, size_t numVertices, int step, CurvesPrimitive::Wrap wrap, size_t vertexOffset )
{
	array<V3f, 4> result;
	if( wrap == CurvesPrimitive::Wrap::Pinned )
	{
		if( segmentIndex == 0 )
		{
			result[0] = points[vertexOffset] * 2 - points[vertexOffset+1];
		}
		else
		{
			vertexOffset += (segmentIndex - 1) * step;
			result[0] = points[vertexOffset];
			vertexOffset++;
		}

		result[1] = points[vertexOffset];
		result[2] = points[vertexOffset+1];

		if( segmentIndex == numSegments - 1 )
		{
			result[3] = points[vertexOffset+1] * 2 - points[vertexOffset];
		}
		else
		{
			result[3] = points[vertexOffset+2];
		}
	}
	else if( wrap == CurvesPrimitive::Wrap::Periodic )
	{
		const int vertexIndex = segmentIndex * step - 1;
		result[0] = points[vertexOffset + (vertexIndex % numVertices)];
		result[1] = points[vertexOffset + ((vertexIndex + 1) % numVertices)];
		result[2] = points[vertexOffset + ((vertexIndex + 2) % numVertices)];
		result[3] = points[vertexOffset + ((vertexIndex + 3) % numVertices)];
	}
	else // wrap == NonPeriodic
	{
		vertexOffset += segmentIndex * step;
		result[0] = points[vertexOffset];
		result[1] = points[vertexOffset+1];
		result[2] = points[vertexOffset+2];
		result[3] = points[vertexOffset+3];
	}

	return result;
}

} // namespace

GAFFER_NODE_DEFINE_TYPE( CurvesTangents );

size_t CurvesTangents::g_firstPlugIndex = 0;

CurvesTangents::CurvesTangents( const std::string &name )
	:	ObjectProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "mode", Plug::In, (int)Mode::CentralDifference, (int)Mode::FirstDifference, (int)Mode::Derivative ) );
	addChild( new BoolPlug( "normalize" ) );
	addChild( new StringPlug( "position", Plug::In, "P" ) );
	addChild( new StringPlug( "tangent", Plug::In, "tangent" ) );
}

CurvesTangents::~CurvesTangents()
{
}

Gaffer::IntPlug *CurvesTangents::modePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *CurvesTangents::modePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *CurvesTangents::normalizePlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *CurvesTangents::normalizePlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *CurvesTangents::positionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *CurvesTangents::positionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *CurvesTangents::tangentPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *CurvesTangents::tangentPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::ValuePlug::CachePolicy CurvesTangents::processedObjectComputeCachePolicy() const
{
	return ValuePlug::CachePolicy::TaskCollaboration;
}

bool CurvesTangents::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input == modePlug() ||
		input == normalizePlug() ||
		input == positionPlug() ||
		input == tangentPlug()
	;
}

void CurvesTangents::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ObjectProcessor::hashProcessedObject( path, context, h );
	modePlug()->hash( h );
	normalizePlug()->hash( h );
	positionPlug()->hash( h );
	tangentPlug()->hash( h );
}

IECore::ConstObjectPtr CurvesTangents::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const CurvesPrimitive *curves = runTimeCast<const CurvesPrimitive>( inputObject );
	if( !curves )
	{
		return inputObject;
	}

	Mode mode = (Mode)modePlug()->getValue();
	const auto interpolation = mode == Mode::Derivative ? PrimitiveVariable::Interpolation::Varying : PrimitiveVariable::Interpolation::Vertex;
	if( mode == Mode::Derivative && curves->basis().standardBasis() == StandardCubicBasis::Linear )
	{
		// This is equivalent, and means that we only need to consider
		// cubic curves in our derivative calculations.
		mode = Mode::FirstDifference;
	}
	const bool normalize = normalizePlug()->getValue();
	const std::string positionName = positionPlug()->getValue();
	const std::string tangentName = tangentPlug()->getValue();

	if( positionName.empty() || tangentName.empty() )
	{
		return inputObject;
	}

	auto positionView = curves->variableIndexedView<V3fVectorData>(
		positionName, PrimitiveVariable::Interpolation::Vertex,
		/* throwIfInvalid = */ true
	);

	// Compute per-curve offsets into the vertex data. This gives
	// us the random access we need to do multithreaded execution below.

	const size_t numCurves = curves->numCurves();
	const vector<int> &verticesPerCurve = curves->verticesPerCurve()->readable();

	std::vector<size_t> vertexOffsets;
	vertexOffsets.reserve( numCurves );
	size_t vertexOffset = 0;
	for( size_t curveIndex = 0; curveIndex < numCurves; ++curveIndex )
	{
		vertexOffsets.push_back( vertexOffset );
		vertexOffset += verticesPerCurve[curveIndex];
	}

	// Do the same for varying data if we need it.

	std::array<float, 4> derivativeCoefficients0, derivativeCoefficients1;
	curves->basis().derivativeCoefficients( 0.0f, derivativeCoefficients0.data() );
	curves->basis().derivativeCoefficients( 1.0f, derivativeCoefficients1.data() );
	std::vector<size_t> varyingOffsets;
	if( mode == Mode::Derivative )
	{
		varyingOffsets.reserve( numCurves );
		size_t varyingOffset = 0;
		for( size_t curveIndex = 0; curveIndex < numCurves; ++curveIndex )
		{
			varyingOffsets.push_back( varyingOffset );
			varyingOffset += curves->variableSize( PrimitiveVariable::Varying, curveIndex );
		}
	}

	// Prepare container for tangents.

	V3fVectorDataPtr tangentData = new V3fVectorData();
	tangentData->setInterpretation( GeometricData::Interpretation::Vector );
	auto &tangents = tangentData->writable();
	tangents.resize( curves->variableSize( mode == Mode::Derivative ? PrimitiveVariable::Varying : PrimitiveVariable::Vertex ) );

	// Compute tangents, parallelising across curves.

	const ThreadState &threadState = ThreadState::current();
	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );
	using Wrap = CurvesPrimitive::Wrap;
	Wrap wrap = curves->wrap();
	if( wrap == Wrap::Pinned && !CurvesAlgo::isPinned( curves ) )
	{
		// Basis not compatible with pinning.
		wrap = Wrap::NonPeriodic;
	}

	tbb::parallel_for(
		tbb::blocked_range<size_t>( 0, numCurves ),
		[&]( const tbb::blocked_range<size_t> &range )
		{
			ThreadState::Scope threadStateScope( threadState );

			for( size_t curveIndex = range.begin(); curveIndex != range.end(); ++curveIndex )
			{
				IECore::Canceller::check(  context->canceller() );
				size_t vertexOffset = vertexOffsets[curveIndex];
				const int numVertices = verticesPerCurve[curveIndex];
				if( mode == Mode::Derivative )
				{
					const size_t varyingOffset = varyingOffsets[curveIndex];
					const int numSegments = curves->numSegments( curveIndex );
					for( int segmentIndex = 0; segmentIndex < numSegments; ++segmentIndex )
					{
						// Add tangent for start of segment.
						array<V3f, 4> p = segmentPoints( *positionView, segmentIndex, numSegments, numVertices, curves->basis().step, wrap, vertexOffset );
						const auto &w = derivativeCoefficients0;
						V3f tangent = p[0] * w[0] + p[1] * w[1] + p[2] * w[2] + p[3] * w[3];
						if( normalize )
						{
							tangent.normalize();
						}
						tangents[varyingOffset + segmentIndex] = tangent;
						// If this is the last segment, add tangent for end of segment.
						if( segmentIndex == numSegments - 1 && wrap != CurvesPrimitive::Wrap::Periodic )
						{
							const auto &w = derivativeCoefficients1;
							V3f tangent = p[0] * w[0] + p[1] * w[1] + p[2] * w[2] + p[3] * w[3];
							if( normalize )
							{
								tangent.normalize();
							}
							tangents[varyingOffset + segmentIndex + 1] = tangent;
						}
					}
				}
				else // mode == FirstDifference || mode == CentralDifference
				{
					for( int vertexIndex = 0; vertexIndex < numVertices; ++vertexIndex )
					{
						int i0, i1;
						if( mode == Mode::FirstDifference )
						{
							i0 = vertexIndex < numVertices - 1 ? vertexIndex : ( wrap == Wrap::Periodic ? vertexIndex : vertexIndex - 1 );
							i1 = vertexIndex < numVertices - 1 ? vertexIndex + 1 : ( wrap == Wrap::Periodic ? 0 : vertexIndex );
						}
						else // mode == CentralDifference
						{
							i0 = vertexIndex > 0 ? vertexIndex -1 : ( wrap == Wrap::Periodic ? numVertices -1 : 0 );
							i1 = vertexIndex < numVertices -1 ? vertexIndex + 1 : ( wrap == Wrap::Periodic ? 0 : numVertices -1 );
						}

						V3f tangent = (*positionView)[i1+vertexOffset] - (*positionView)[i0+vertexOffset];
						if( normalize )
						{
							tangent.normalize();
						}
						tangents[vertexOffset + vertexIndex] = tangent;
					}
				}
			}
		},
		taskGroupContext
	);

	// Copy input and add tangent primitive variable.

	CurvesPrimitivePtr result = runTimeCast<CurvesPrimitive>( curves->copy() );
	result->variables[tangentName] = PrimitiveVariable( interpolation, tangentData );

	return result;
}
