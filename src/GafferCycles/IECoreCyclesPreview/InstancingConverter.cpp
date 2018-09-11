//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#include "GafferCycles/IECoreCyclesPreview/InstancingConverter.h"

#include "GafferCycles/IECoreCyclesPreview/ObjectAlgo.h"

#include "tbb/concurrent_hash_map.h"

// Cycles
#include "render/mesh.h"
#include "util/util_param.h"

using namespace IECoreCycles;

struct InstancingConverter::MemberData
{
	typedef tbb::concurrent_hash_map<IECore::MurmurHash, ccl::Object *> Cache;
	Cache cache;
};

InstancingConverter::InstancingConverter()
{
	m_data = new MemberData();
}

InstancingConverter::~InstancingConverter()
{
	delete m_data;
}

ccl::Object *InstancingConverter::convert( const IECoreScene::Primitive *primitive, const std::string &nodeName )
{
	return convert( primitive, IECore::MurmurHash(), nodeName );
}

ccl::Object *InstancingConverter::convert( const IECoreScene::Primitive *primitive, const IECore::MurmurHash &additionalHash, const std::string &nodeName )
{
	IECore::MurmurHash h = primitive->::IECore::Object::hash();
	h.append( additionalHash );

	MemberData::Cache::accessor a;
	if( m_data->cache.insert( a, h ) )
	{
		a->second = ObjectAlgo::convert( primitive, nodeName );
		return a->second;
	}
	else
	{
		if( a->second )
		{
			ccl::Object *cobject = new ccl::Object();
			cobject->mesh = &(a->second->mesh);
			cobject->name = ustring(nodeName.c_str());
			return cobject;
		}
	}

	return nullptr;
}

ccl::Object *InstancingConverter::convert( const std::vector<const IECoreScene::Primitive *> &samples, const std::string &nodeName )
{
	return convert( samples, IECore::MurmurHash(), nodeName );
}

ccl::Object *InstancingConverter::convert( const std::vector<const IECoreScene::Primitive *> &samples, const IECore::MurmurHash &additionalHash, const std::string &nodeName )
{
	IECore::MurmurHash h;
	for( std::vector<const IECoreScene::Primitive *>::const_iterator it = samples.begin(), eIt = samples.end(); it != eIt; ++it )
	{
		(*it)->hash( h );
	}
	h.append( additionalHash );

	MemberData::Cache::accessor a;
	if( m_data->cache.insert( a, h ) )
	{
		std::vector<const IECore::Object *> objectSamples( samples.begin(), samples.end() );
		a->second = ObjectAlgo::convert( objectSamples, nodeName );
		return a->second;
	}
	else
	{
		if( a->second )
		{
			ccl::Object *cobject = new ccl::Object();
			cobject->mesh = &(a->second->mesh);
			cobject->name = ustring(nodeName.c_str());
			return cobject;
		}
	}

	return nullptr;
}
