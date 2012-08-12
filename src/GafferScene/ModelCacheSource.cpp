//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "tbb/mutex.h"

#include "boost/tokenizer.hpp"

#include "IECore/FileIndexedIO.h"
#include "IECore/LRUCache.h"

#include "GafferScene/ModelCacheSource.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( ModelCacheSource );

//////////////////////////////////////////////////////////////////////////
// Implementation of an LRUCache of FileIndexedIOs.
//////////////////////////////////////////////////////////////////////////

namespace GafferScene
{

namespace Detail
{

class FileAndMutex : public IECore::RefCounted
{
	public :
		
		typedef tbb::mutex Mutex;
		Mutex mutex;
		/// \todo Add an actual ModelCache class to IECore rather than improvising with direct FileIndexedIO access.
		FileIndexedIOPtr file;
		
};

IE_CORE_DECLAREPTR( FileAndMutex )

FileAndMutexPtr fileCacheGetter( const std::string &fileName, size_t &cost )
{
	FileAndMutexPtr result = new FileAndMutex;
	result->file = new FileIndexedIO( fileName, "/", IndexedIO::Read );
	cost = 1;
	return result;
}

typedef LRUCache<std::string, FileAndMutexPtr> FileCache;

static FileCache g_fileCache( fileCacheGetter, 200 );

} // namespace Detail

} // namespace GafferScene

//////////////////////////////////////////////////////////////////////////
// ModelCacheSource implementation
//////////////////////////////////////////////////////////////////////////

using namespace GafferScene::Detail;

ModelCacheSource::ModelCacheSource( const std::string &name )
	:	FileSource( name )
{
}

ModelCacheSource::~ModelCacheSource()
{
}

Imath::Box3f ModelCacheSource::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string entry = entryForPath( path ) + "/bound";
	Box3f result;
	float *resultAddress = result.min.getValue();
	
	FileAndMutexPtr f = g_fileCache.get( fileNamePlug()->getValue() );
	FileAndMutex::Mutex::scoped_lock lock( f->mutex );
	f->file->read( entry, resultAddress, 6 );

	return result;
}

Imath::M44f ModelCacheSource::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string entry = entryForPath( path ) + "/transform";
	M44f result;
	float *resultAddress = result.getValue();
	
	FileAndMutexPtr f = g_fileCache.get( fileNamePlug()->getValue() );
	FileAndMutex::Mutex::scoped_lock lock( f->mutex );
	try
	{
		f->file->read( entry, resultAddress, 16 );
	}
	catch( ... )
	{
		// it's ok for an entry to not specify a transform
	}
	
	return result;
}

IECore::ConstCompoundObjectPtr ModelCacheSource::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	/// \todo Implement support for attributes in the file format and then support it here.
	return 0;
}

IECore::ConstObjectPtr ModelCacheSource::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	/// \todo The entry in the file should be called "object"
	std::string entry = entryForPath( path ) + "/geometry";
	
	FileAndMutexPtr f = g_fileCache.get( fileNamePlug()->getValue() );
	FileAndMutex::Mutex::scoped_lock lock( f->mutex );
	ObjectPtr result = 0;
	try
	{
		result = Object::load( f->file, entry );
	}
	catch( ... )
	{
		// it's ok for an entry to not specify geometry	
	}
	return runTimeCast<Primitive>( result );
}

IECore::ConstStringVectorDataPtr ModelCacheSource::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string entry = entryForPath( path ) + "/children";

	FileAndMutexPtr f = g_fileCache.get( fileNamePlug()->getValue() );
	FileAndMutex::Mutex::scoped_lock lock( f->mutex );

	IndexedIO::EntryList entries;

	try
	{
		f->file->chdir( entry );
	 	entries = f->file->ls();
		f->file->chdir( "/" );
	}
	catch( ... )
	{
		// it's ok for an entry to not specify children
	}
	
	StringVectorDataPtr resultData = new StringVectorData;
	std::vector<std::string> &result = resultData->writable();
	for( IndexedIO::EntryList::const_iterator it = entries.begin(); it!=entries.end(); it++ )
	{
		result.push_back( it->id() );
	}

	return resultData;
}

IECore::ConstObjectVectorPtr ModelCacheSource::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return 0;
}

std::string ModelCacheSource::entryForPath( const ScenePath &path ) const
{
	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
	Tokenizer tokens( path, boost::char_separator<char>( "/" ) );
	
	std::string result = "/root";
	for( Tokenizer::iterator tIt=tokens.begin(); tIt!=tokens.end(); tIt++ )
	{	
		result += "/children/";
		result += *tIt;
	}
	
	return result;
}
