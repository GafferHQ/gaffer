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

#include "GafferCycles/IECoreCyclesPreview/ParticleAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

//#include "IECoreScene/PointsAlgo.h"

#include "IECore/SimpleTypedData.h"

// Cycles
#include "render/particles.h"
#include "util/util_array.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace IECoreCycles

{

namespace ParticleAlgo

{

ccl::ParticleSystem *convert( const IECoreScene::PointsPrimitive *points )
{
	ccl::ParticleSystem *cparticleSys = new ccl::ParticleSystem();
	size_t size = points->getNumPoints();
	cparticleSys->particles = ccl::array<ccl::Particle>( size );

	// Convert primitive variables.
	PrimitiveVariableMap variablesToConvert = points->variables;
	for( PrimitiveVariableMap::iterator it = variablesToConvert.begin(), eIt = variablesToConvert.end(); it != eIt; ++it )
	{
		// Int
		if( ( it->first == "index" ) || ( it->first == "instanceIndex" ) )
		{
			if( const IntVectorData *data = runTimeCast<const IntVectorData>( it->second.data.get() ) )
			{
				const std::vector<int> &intData = data->readable();

				for( size_t i = 0; i < size; ++i )
					cparticleSys->particles[i].index = intData[i];
			}
		}
		// Floats
		else if( ( it->first == "age" ) || ( it->first == "lifetime" ) || ( it->first == "size" ) || ( it->first == "width" ) )
		{
			if( const FloatVectorData *data = runTimeCast<const FloatVectorData>( it->second.data.get() ) )
			{
				const std::vector<float> &floatData = data->readable();

				if( it->first == "age" )
				{
					for( size_t i = 0; i < size; ++i )
						cparticleSys->particles[i].age = floatData[i];
				}
				else if( it->first == "lifetime" )
				{
					for( size_t i = 0; i < size; ++i )
						cparticleSys->particles[i].lifetime = floatData[i];
				}
				else if( ( it->first == "size" ) || ( it->first == "width" ) )
				{
					for( size_t i = 0; i < size; ++i )
						cparticleSys->particles[i].size = floatData[i];
				}
			}
		}
		// Vec3
		else if( ( it->first == "P" ) || ( it->first == "velocity" ) || ( it->first == "angular_velocity" ) )
		{
			if( const V3fVectorData *data = runTimeCast<const V3fVectorData>( it->second.data.get() ) )
			{
				const std::vector<V3f> &v3fData = data->readable();

				if( it->first == "P" )
				{
					for( size_t i = 0; i < size; ++i )
						cparticleSys->particles[i].location = SocketAlgo::setVector( v3fData[i] );
				}
				else if( it->first == "velocity" )
				{
					for( size_t i = 0; i < size; ++i )
						cparticleSys->particles[i].velocity = SocketAlgo::setVector( v3fData[i] );
				}
				else if( it->first == "angular_velocity" )
				{
					for( size_t i = 0; i < size; ++i )
						cparticleSys->particles[i].angular_velocity = SocketAlgo::setVector( v3fData[i] );
				}
			}
		}
		// Quat
		else if( ( it->first == "rotation" ) || ( it->first == "orientation" ) )
		{
			if( const QuatfVectorData *data = runTimeCast<const QuatfVectorData>( it->second.data.get() ) )
			{
				const std::vector<Quatf> &quatfData = data->readable();

				for( size_t i = 0; i < size; ++i )
					cparticleSys->particles[i].rotation = SocketAlgo::setQuaternion( quatfData[i] );
			}
		}
		else
		{
			msg( Msg::Warning, "IECoreCyles::PointsAlgo::convert", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected V3fVectorData)." ) % it->first % it->second.data->typeName() );
		}
	}

	return cparticleSys;
}

} // namespace ParticleAlgo

} // namespace IECoreCycles
