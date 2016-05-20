//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "IECore/SimpleTypedData.h"
#include "IECore/Renderer.h"

#include "IECoreArnold/NodeAlgo.h"
#include "IECoreArnold/ParameterAlgo.h"
#include "GafferArnold/Private/IECoreArnoldPreview/ProceduralAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreArnold;
using namespace IECoreArnoldPreview;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

NodeAlgo::ConverterDescription<ExternalProcedural> g_description( ProceduralAlgo::convert );

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace IECoreArnoldPreview
{

namespace ProceduralAlgo
{

AtNode *convert( const IECore::ExternalProcedural *procedural )
{
	std::string nodeType = "procedural";
	// Allow a parameter "ai:nodeType" == "volume" to create a volume shape rather
	// than a procedural shape. Volume shapes provide "dso", "min" and "max" parameters
	// just as procedural shapes do, so the mapping is a fairly natural one.
	const CompoundDataMap &parameters = procedural->parameters()->readable();
	CompoundDataMap::const_iterator nodeTypeIt = parameters.find( "ai:nodeType" );
	if( nodeTypeIt != parameters.end() && nodeTypeIt->second->isInstanceOf( StringData::staticTypeId() ) )
	{
		nodeType = static_cast<const StringData *>( nodeTypeIt->second.get() )->readable();
	}
	AtNode *node = AiNode( nodeType.c_str() );

	AiNodeSetStr( node, "dso", procedural->getFileName().c_str() );
	ParameterAlgo::setParameters( node, parameters );

	const Box3f bound = procedural->bound();
	if( bound != Renderer::Procedural::noBound )
	{
		AiNodeSetPnt( node, "min", bound.min.x, bound.min.y, bound.min.z );
		AiNodeSetPnt( node, "max", bound.max.x, bound.max.y, bound.max.z );
	}
	else
	{
		// No bound available - expand procedural immediately.
		AiNodeSetBool( node, "load_at_init", true );
	}

	return node;
}

} // namespace ProceduralAlgo

} // namespace IECoreArnoldPreview

