//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "IECoreScene/CurvesPrimitive.h"

#include "IECore/MessageHandler.h"

#include <nsi.h>

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreDelight;

namespace
{

const char *g_catmullRom = "catmull-rom";
const char *g_bSpline = "b-spline";

void staticParameters( const IECoreScene::CurvesPrimitive *object, ParameterList &parameters )
{
	parameters.add( "nvertices", object->verticesPerCurve() );

	const char **basis = nullptr;
	if( object->basis() == CubicBasisf::catmullRom() )
	{
		basis = &g_catmullRom;
	}
	else if( object->basis() == CubicBasisf::bSpline() )
	{
		basis = &g_bSpline;
	}
	else
	{
		IECore::msg( IECore::Msg::Warning, "IECoreDelight", "Unsupported curves basis" );
	}

	if( basis )
	{
		parameters.add( {
			"basis",
			basis,
			NSITypeString,
			0,
			1,
			0
		} );
	}

	if( object->periodic() )
	{
		IECore::msg( IECore::Msg::Warning, "IECoreDelight", "Periodic curves are not supported" );
	}
}

bool convertStatic( const IECoreScene::CurvesPrimitive *object, NSIContext_t context, const char *handle )
{
	NSICreate( context, handle, "cubiccurves", 0, nullptr );

	ParameterList parameters;
	staticParameters( object, parameters );

	NodeAlgo::primitiveVariableParameterList( object, parameters );

	NSISetAttribute( context, handle, parameters.size(), parameters.data() );

	return true;
}

bool convertAnimated( const vector<const IECoreScene::CurvesPrimitive *> &objects, const vector<float> &times, NSIContext_t context, const char *handle )
{
	NSICreate( context, handle, "cubiccurves", 0, nullptr );

	ParameterList parameters;
	staticParameters( objects.front(), parameters );

	vector<ParameterList> animatedParameters;
	NodeAlgo::primitiveVariableParameterLists(
		vector<const Primitive *>( objects.begin(), objects.end() ),
		parameters, animatedParameters
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

NodeAlgo::ConverterDescription<CurvesPrimitive> g_description( convertStatic, convertAnimated );

} // namespace
