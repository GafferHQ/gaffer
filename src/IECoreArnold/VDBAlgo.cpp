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

#include "IECoreVDB/VDBObject.h"

#include "IECoreArnold/NodeAlgo.h"
#include "IECoreArnold/ParameterAlgo.h"

#include "IECoreScene/Renderer.h"

#include "IECore/CompoundData.h"
#include "IECore/Exception.h"
#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/Version.h"

#include "openvdb/io/Stream.h"
#include "openvdb/openvdb.h"

#include "boost/iostreams/categories.hpp"
#include "boost/iostreams/stream.hpp"

using namespace std;
using namespace Imath;

using namespace IECore;
using namespace IECoreArnold;

namespace
{

IECore::InternedString g_filedataParam("filedata");
IECore::InternedString g_filenameParam("filename");

IECore::InternedString g_gridParam("grids");
AtString g_volume("volume");

///! utility to allow us to stream directly into a UCharVectorData
struct UCharVectorDataSink
{
	using char_type = char;
	using category = boost::iostreams::sink_tag;

	UCharVectorDataSink( IECore::UCharVectorData *storage ) : m_storage( storage->writable() )
	{
	}

	std::streamsize write( const char *s, std::streamsize n )
	{
		m_storage.insert( m_storage.end(), s, s + n );
		return n;
	}

	std::vector<unsigned char> &m_storage;
};

UCharVectorDataPtr createMemoryBuffer(const IECoreVDB::VDBObject* vdbObject)
{
	IECore::UCharVectorDataPtr buffer = new IECore::UCharVectorData();
	UCharVectorDataSink sink( buffer.get() );
	boost::iostreams::stream<UCharVectorDataSink> memoryStream( sink );

	openvdb::io::Stream vdbStream( memoryStream );

	openvdb::GridCPtrVec gridsToWrite;
	std::vector<std::string> gridNames = vdbObject->gridNames();
	for( const std::string& gridName : gridNames )
	{
		gridsToWrite.push_back( vdbObject->findGrid( gridName ) );
	}
	vdbStream.write( gridsToWrite );

	return buffer;
}

CompoundDataPtr createParameters(const IECoreVDB::VDBObject* vdbObject)
{
	CompoundDataPtr parameters = new CompoundData();
	CompoundDataMap& compoundData = parameters->writable();

	compoundData[g_gridParam] = new StringVectorData( vdbObject->gridNames() );

	if ( vdbObject->unmodifiedFromFile() )
	{
		compoundData[g_filenameParam] = new StringData( vdbObject->fileName() );
	}
	else
	{
		compoundData[g_filedataParam] = createMemoryBuffer( vdbObject );
	}

	return parameters;
}

AtNode *convert( const IECoreVDB::VDBObject *vdbObject, AtUniverse *universe, const std::string &name, const AtNode* parent, const std::string &messageContext )
{
	AtNode *node = AiNode( universe, g_volume, AtString( name.c_str() ), parent );

	CompoundDataPtr parameters = createParameters( vdbObject );
	ParameterAlgo::setParameters( node, parameters->readable(), messageContext );

	return node;
}

NodeAlgo::ConverterDescription<IECoreVDB::VDBObject> g_description( ::convert );

} // namespace
