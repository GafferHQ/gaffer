//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

// Cycles (for ustring)
#include "util/util_param.h"
#undef fmix // OpenImageIO's farmhash inteferes with IECore::MurmurHash

#include "GafferCycles/IECoreCyclesPreview/ObjectAlgo.h"

#include "IECore/MessageHandler.h"

#include "IECoreScene/PrimitiveVariable.h"

#include <unordered_map>

using namespace std;
using namespace IECore;
using namespace IECoreScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace std
{

/// \todo Move to IECore/TypeIds.h
template<>
struct hash<IECore::TypeId>
{
	size_t operator()( IECore::TypeId typeId ) const
	{
		return hash<size_t>()( typeId );
	}
};

} // namespace std

namespace
{

using namespace IECoreCycles;

struct Converters
{

	ObjectAlgo::Converter converter;
	ObjectAlgo::MotionConverter motionConverter;

};

typedef std::unordered_map<IECore::TypeId, Converters> Registry;

Registry &registry()
{
	static Registry r;
	return r;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace IECoreCycles
{

namespace ObjectAlgo
{

ccl::Object *convert( const IECore::Object *object, const std::string &nodeName, ccl::Scene *scene )
{
	const Registry &r = registry();
	Registry::const_iterator it = r.find( object->typeId() );
	if( it == r.end() )
	{
		return nullptr;
	}
	return it->second.converter( object, nodeName, scene );
}

ccl::Object *convert( const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const int frameIdx, const std::string &nodeName, ccl::Scene *scene )
{
	if( samples.empty() )
	{
		return nullptr;
	}

	const IECore::Object *firstSample = samples.front();
	const IECore::TypeId firstSampleTypeId = firstSample->typeId();
	for( std::vector<const IECore::Object *>::const_iterator it = samples.begin()+1, eIt = samples.end(); it != eIt; ++it )
	{
		if( (*it)->typeId() != firstSampleTypeId )
		{
			throw IECore::Exception( "Inconsistent object types." );
		}
	}

	const Registry &r = registry();
	Registry::const_iterator it = r.find( firstSampleTypeId );
	if( it == r.end() )
	{
		return nullptr;
	}
	if( it->second.motionConverter )
	{
		return it->second.motionConverter( samples, times, frameIdx, nodeName, scene );
	}
	else
	{
		return it->second.converter( samples.front(), nodeName, scene );
	}
}

void registerConverter( IECore::TypeId fromType, Converter converter, MotionConverter motionConverter )
{
	registry()[fromType] = { converter, motionConverter };
}

} // namespace ObjectAlgo

} // namespace IECoreCycles
