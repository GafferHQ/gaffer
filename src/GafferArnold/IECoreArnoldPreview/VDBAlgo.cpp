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
#include "IECore/CompoundData.h"

#include "IECoreArnold/ParameterAlgo.h"

#include "IECoreArnold/NodeAlgo.h"

#include "GafferVDB/VDBObject.h"

using namespace std;
using namespace Imath;

using namespace IECore;
using namespace IECoreArnold;

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace
{
	IECore::InternedString g_filedataParam("filedata");
	IECore::InternedString g_gridParam("grids");
	AtString g_volume("volume");

	CompoundDataPtr  createParameters(const GafferVDB::VDBObject* vdbObject)
	{
		CompoundDataPtr parameters = new CompoundData();
		CompoundDataMap& compoundData = parameters->writable();

		compoundData[g_gridParam] = new StringVectorData( vdbObject->gridNames() );
		compoundData[g_filedataParam] = vdbObject->memoryBuffer();

		return parameters;
	}
}

namespace IECoreArnoldPreview
{

namespace VDBAlgo
{

AtNode *convert( const GafferVDB::VDBObject *vdbObject, const std::string & /*name*/, const AtNode* /* parent */ )
{
	AtNode *node = AiNode( g_volume );

	CompoundDataPtr parameters = createParameters( vdbObject );
	ParameterAlgo::setParameters( node, parameters->readable() );

	return node;
}

} // namespace ProceduralAlgo

} // namespace IECoreArnoldPreview

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

NodeAlgo::ConverterDescription<GafferVDB::VDBObject> g_description( IECoreArnoldPreview::VDBAlgo::convert );

} // namespace