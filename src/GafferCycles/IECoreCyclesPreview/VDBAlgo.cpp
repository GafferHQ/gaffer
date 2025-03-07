//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Alex Fuller. All rights reserved.
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

#include "GafferCycles/IECoreCyclesPreview/GeometryAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "openvdb/openvdb.h"
IECORE_POP_DEFAULT_VISIBILITY

// This also includes "openvdb.h", so it must come after our
// `#include "openvdb.h"` so that `IECORE_PUSH_DEFAULT_VISIBILITY`
// can do its thing.
#include "IECoreVDB/VDBObject.h"

// Cycles
IECORE_PUSH_DEFAULT_VISIBILITY
#include "scene/volume.h"
IECORE_POP_DEFAULT_VISIBILITY

using namespace std;
using namespace Imath;

using namespace IECore;
using namespace IECoreCycles;

namespace
{

ccl::Geometry *convert( const IECoreVDB::VDBObject *vdbObject, const std::string &nodeName, ccl::Scene *scene )
{
	ccl::Volume *volume = new ccl::Volume();
	volume->name = ccl::ustring( nodeName.c_str() );
	return volume;
}

ccl::Geometry *convert( const std::vector<const IECoreVDB::VDBObject *> &samples, const std::vector<float> &times, const int frameIdx, const std::string &nodeName, ccl::Scene *scene )
{
	return convert( samples.front(), nodeName, scene );
}

GeometryAlgo::ConverterDescription<IECoreVDB::VDBObject> g_description( convert, convert );

} // namespace
