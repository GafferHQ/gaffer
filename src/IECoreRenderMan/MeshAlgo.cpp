//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "GeometryAlgo.h"

#include "IECoreScene/MeshPrimitive.h"

#include "RixPredefinedStrings.hpp"

#include "fmt/format.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreRenderMan;

namespace
{

int interpolateBoundary( const IECoreScene::MeshPrimitive *mesh, const std::string &messageContext  )
{
	const InternedString s = mesh->getInterpolateBoundary();
	if( s == IECoreScene::MeshPrimitive::interpolateBoundaryNone )
	{
		return 0;
	}
	else if( s == IECoreScene::MeshPrimitive::interpolateBoundaryEdgeAndCorner )
	{
		return 1;
	}
	else if( s == IECoreScene::MeshPrimitive::interpolateBoundaryEdgeOnly )
	{
		return 2;
	}
	else
	{
		msg( Msg::Error, messageContext, fmt::format( "Unknown boundary interpolation \"{}\"", s.string() ) );
		return 0;
	}
}

int faceVaryingInterpolateBoundary( const IECoreScene::MeshPrimitive *mesh, const std::string &messageContext  )
{
	const InternedString s = mesh->getFaceVaryingLinearInterpolation();
	if( s == IECoreScene::MeshPrimitive::faceVaryingLinearInterpolationNone )
	{
		return 2;
	}
	else if(
		s == IECoreScene::MeshPrimitive::faceVaryingLinearInterpolationCornersOnly ||
		s == IECoreScene::MeshPrimitive::faceVaryingLinearInterpolationCornersPlus1 ||
		s == IECoreScene::MeshPrimitive::faceVaryingLinearInterpolationCornersPlus2
	)
	{
		return 1;
	}
	else if( s == IECoreScene::MeshPrimitive::faceVaryingLinearInterpolationBoundaries )
	{
		return 3;
	}
	else if( s == IECoreScene::MeshPrimitive::faceVaryingLinearInterpolationAll )
	{
		return 0;
	}
	else
	{
		msg( Msg::Error, messageContext, fmt::format( "Unknown facevarying linear interpolation \"{}\"", s.string() ) );
		return 0;
	}
}

int smoothTriangles( const IECoreScene::MeshPrimitive *mesh, const std::string &messageContext  )
{
	const InternedString s = mesh->getTriangleSubdivisionRule();
	if( s == IECoreScene::MeshPrimitive::triangleSubdivisionRuleCatmullClark )
	{
		return 0;
	}
	else if( s == IECoreScene::MeshPrimitive::triangleSubdivisionRuleSmooth )
	{
		return 2;
	}
	else
	{
		msg( Msg::Error, messageContext, fmt::format( "Unknown triangle subdivision rule \"{}\"", s.string() ) );
		return 0;
	}
}

RtUString convertMeshTopology( const IECoreScene::MeshPrimitive *mesh, RtPrimVarList &primVars, const std::string &messageContext  )
{
	primVars.SetDetail(
		mesh->variableSize( PrimitiveVariable::Uniform ),
		mesh->variableSize( PrimitiveVariable::Vertex ),
		mesh->variableSize( PrimitiveVariable::Varying ),
		mesh->variableSize( PrimitiveVariable::FaceVarying )
	);

	primVars.SetIntegerDetail( Rix::k_Ri_nvertices, mesh->verticesPerFace()->readable().data(), RtDetailType::k_uniform );
	primVars.SetIntegerDetail( Rix::k_Ri_vertices, mesh->vertexIds()->readable().data(), RtDetailType::k_facevarying );

	RtUString geometryType = Rix::k_Ri_PolygonMesh;
	if( mesh->interpolation() != MeshPrimitive::interpolationLinear.string() )
	{
		geometryType = Rix::k_Ri_SubdivisionMesh;
		if( mesh->interpolation() == MeshPrimitive::interpolationCatmullClark.string() )
		{
			primVars.SetString( Rix::k_Ri_scheme, Rix::k_catmullclark );
		}
		else if( mesh->interpolation() == MeshPrimitive::interpolationLoop.string() )
		{
			primVars.SetString( Rix::k_Ri_scheme, Rix::k_loop );
		}
		else
		{
			msg( Msg::Error, messageContext, fmt::format( "Unknown mesh interpolation \"{}\"", mesh->interpolation() ) );
			primVars.SetString( Rix::k_Ri_scheme, Rix::k_catmullclark );
		}

		vector<RtUString> tagNames;
		vector<RtInt> tagArgCounts;
		vector<RtInt> tagIntArgs;
		vector<RtFloat> tagFloatArgs;

		// Creases

		for( int creaseLength : mesh->creaseLengths()->readable() )
		{
			tagNames.push_back( Rix::k_crease );
			tagArgCounts.push_back( creaseLength ); // integer argument count
			tagArgCounts.push_back( 1 ); // float argument count
			tagArgCounts.push_back( 0 ); // string argument count
		}

		tagIntArgs = mesh->creaseIds()->readable();
		tagFloatArgs = mesh->creaseSharpnesses()->readable();

		// Corners

		if( mesh->cornerIds()->readable().size() )
		{
			tagNames.push_back( Rix::k_corner );
			tagArgCounts.push_back( mesh->cornerIds()->readable().size() ); // integer argument count
			tagArgCounts.push_back( mesh->cornerIds()->readable().size() ); // float argument count
			tagArgCounts.push_back( 0 ); // string argument count
			tagIntArgs.insert( tagIntArgs.end(), mesh->cornerIds()->readable().begin(), mesh->cornerIds()->readable().end() );
			tagFloatArgs.insert( tagFloatArgs.end(), mesh->cornerSharpnesses()->readable().begin(), mesh->cornerSharpnesses()->readable().end() );
		}

		// Interpolation rules

		tagNames.push_back( Rix::k_interpolateboundary );
		tagArgCounts.insert( tagArgCounts.end(), { 1, 0, 0 } );
		tagIntArgs.push_back( interpolateBoundary( mesh, messageContext ) );

		tagNames.push_back( Rix::k_facevaryinginterpolateboundary );
		tagArgCounts.insert( tagArgCounts.end(), { 1, 0, 0 } );
		tagIntArgs.push_back( faceVaryingInterpolateBoundary( mesh, messageContext ) );

		tagNames.push_back( Rix::k_smoothtriangles );
		tagArgCounts.insert( tagArgCounts.end(), { 1, 0, 0 } );
		tagIntArgs.push_back( smoothTriangles( mesh, messageContext ) );

		// Pseudo-primvars to hold the tags

		primVars.SetStringArray( Rix::k_Ri_subdivtags, tagNames.data(), tagNames.size() );
		primVars.SetIntegerArray( Rix::k_Ri_subdivtagnargs, tagArgCounts.data(), tagArgCounts.size() );
		primVars.SetFloatArray( Rix::k_Ri_subdivtagfloatargs, tagFloatArgs.data(), tagFloatArgs.size() );
		primVars.SetIntegerArray( Rix::k_Ri_subdivtagintargs, tagIntArgs.data(), tagIntArgs.size() );
	}

	return geometryType;
}

RtUString convertStaticMesh( const IECoreScene::MeshPrimitive *mesh, RtPrimVarList &primVars, const std::string &messageContext )
{
	const RtUString result = convertMeshTopology( mesh, primVars, messageContext );
	GeometryAlgo::convertPrimitiveVariables( mesh, primVars, messageContext );
	return result;
}

RtUString convertAnimatedMesh( const std::vector<const IECoreScene::MeshPrimitive *> &samples, const std::vector<float> &sampleTimes, RtPrimVarList &primVars, const std::string &messageContext )
{
	const RtUString result = convertMeshTopology( samples[0], primVars, messageContext );
	GeometryAlgo::convertPrimitiveVariables( reinterpret_cast<const std::vector<const IECoreScene::Primitive *> &>( samples ), sampleTimes, primVars, messageContext );
	return result;
}

GeometryAlgo::ConverterDescription<MeshPrimitive> g_meshConverterDescription( convertStaticMesh, convertAnimatedMesh );

} // namespace
