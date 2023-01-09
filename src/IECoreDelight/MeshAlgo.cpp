//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
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

#include "IECoreDelight/NodeAlgo.h"
#include "IECoreDelight/ParameterList.h"

#include "IECoreScene/MeshPrimitive.h"

#include <nsi.h>

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreDelight;

namespace
{

const char *g_catmullClark = "catmull-clark";

void staticParameters( const IECoreScene::MeshPrimitive *mesh, ParameterList &parameters )
{
	parameters.add( "nvertices", mesh->verticesPerFace() );

	if( mesh->interpolation() == "catmullClark" )
	{
		parameters.add( {
			"subdivision.scheme",
			&g_catmullClark,
			NSITypeString,
			0,
			1,
			0
		} );
	}
}

bool convertStatic( const IECoreScene::MeshPrimitive *mesh, NSIContext_t context, const char *handle )
{
	NSICreate( context, handle, "mesh", 0, nullptr );

	ParameterList parameters;
	staticParameters( mesh, parameters );
	NodeAlgo::primitiveVariableParameterList( mesh, parameters, mesh->vertexIds() );

	NSISetAttribute( context, handle, parameters.size(), parameters.data() );

	return true;
}

bool convertAnimated( const vector<const IECoreScene::MeshPrimitive *> &meshes, const vector<float> &times, NSIContext_t context, const char *handle )
{
	NSICreate( context, handle, "mesh", 0, nullptr );

	ParameterList parameters;
	staticParameters( meshes.front(), parameters );

	vector<ParameterList> animatedParameters;
	NodeAlgo::primitiveVariableParameterLists(
		vector<const Primitive *>( meshes.begin(), meshes.end() ),
		parameters, animatedParameters,
		meshes.front()->vertexIds()
	);

	NSISetAttribute( context, handle, parameters.size(), parameters.data() );

	if( !animatedParameters.empty() )
	{
		for( size_t i = 0, e = animatedParameters.size(); i < e; ++i )
		{
			NSISetAttributeAtTime( context, handle, times[i], animatedParameters[i].size(), animatedParameters[i].data() );
		}
	}

	return true;
}

NodeAlgo::ConverterDescription<MeshPrimitive> g_description( convertStatic, convertAnimated );

} // namespace
