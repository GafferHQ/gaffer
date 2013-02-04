//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
#include "IECore/ModelCache.h"

#include "GafferScene/ModelCacheSource.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( ModelCacheSource );

//////////////////////////////////////////////////////////////////////////
// ModelCacheSource::Cache Implementation
//////////////////////////////////////////////////////////////////////////

class ModelCacheSource::Cache
{
	
	private :
	
		IE_CORE_FORWARDDECLARE( FileAndMutex )

	public :
				
		Cache()
			:	m_fileCache( fileCacheGetter, 200 )
		{
		};
		
		/// This class provides access to a particular location within
		/// the ModelCache, and ensures that access is threadsafe by holding
		/// a mutex on the file.
		class Entry : public IECore::RefCounted
		{
		
			public :
			
				const ModelCache *modelCache()
				{
					return m_entry;
				}
		
			private :
			
				Entry( FileAndMutexPtr fileAndMutex )
					:	m_fileAndMutex( fileAndMutex ), m_lock( m_fileAndMutex->mutex )
				{
				}
			
				FileAndMutexPtr m_fileAndMutex;
				tbb::mutex::scoped_lock m_lock;
				ConstModelCachePtr m_entry;
				
				friend class Cache;
				
		};

		IE_CORE_DECLAREPTR( Entry )
		
		EntryPtr entry( const std::string &fileName, const ScenePath &scenePath )
		{
			FileAndMutexPtr f = m_fileCache.get( fileName );
			EntryPtr result = new Entry( f ); // this locks the mutex for us
			result->m_entry = result->m_fileAndMutex->file;
			
			for( ScenePath::const_iterator it = scenePath.begin(), eIt = scenePath.end(); it != eIt; it++ )
			{
				result->m_entry = result->m_entry->readableChild( *it );
			}
			
			return result;
		}
		
	private :
	
		class FileAndMutex : public IECore::RefCounted
		{
			public :
				
				typedef tbb::mutex Mutex;
				Mutex mutex;
				ModelCachePtr file;
				
		};
				
		static FileAndMutexPtr fileCacheGetter( const std::string &fileName, size_t &cost )
		{
			FileAndMutexPtr result = new FileAndMutex;
			result->file = new ModelCache( fileName, IndexedIO::Read );
			cost = 1;
			return result;
		}
		
		typedef LRUCache<std::string, FileAndMutexPtr> FileCache;
		FileCache m_fileCache;

};

//////////////////////////////////////////////////////////////////////////
// ModelCacheSource implementation
//////////////////////////////////////////////////////////////////////////

ModelCacheSource::ModelCacheSource( const std::string &name )
	:	FileSource( name )
{
}

ModelCacheSource::~ModelCacheSource()
{
}

Imath::Box3f ModelCacheSource::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	Cache::EntryPtr entry = cache().entry( fileNamePlug()->getValue(), path );
	Box3d b = entry->modelCache()->readBound();
	return Box3f( b.min, b.max );
}

Imath::M44f ModelCacheSource::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	Cache::EntryPtr entry = cache().entry( fileNamePlug()->getValue(), path );
	M44d t = entry->modelCache()->readTransform();
	return M44f(
		t[0][0], t[0][1], t[0][2], t[0][3],
		t[1][0], t[1][1], t[1][2], t[1][3],
		t[2][0], t[2][1], t[2][2], t[2][3],
		t[3][0], t[3][1], t[3][2], t[3][3]
	);
}

IECore::ConstCompoundObjectPtr ModelCacheSource::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	/// \todo Implement support for attributes in the file format and then support it here.
	return parent->attributesPlug()->defaultValue();
}

IECore::ConstObjectPtr ModelCacheSource::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	Cache::EntryPtr entry = cache().entry( fileNamePlug()->getValue(), path );
	ObjectPtr o = entry->modelCache()->readObject();
	return o ? o : parent->objectPlug()->defaultValue();
}

IECore::ConstInternedStringVectorDataPtr ModelCacheSource::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	Cache::EntryPtr entry = cache().entry( fileNamePlug()->getValue(), path );

	InternedStringVectorDataPtr result = new InternedStringVectorData;
	entry->modelCache()->childNames( result->writable() );
	
	return result;
}

IECore::ConstObjectVectorPtr ModelCacheSource::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return parent->globalsPlug()->defaultValue();
}

ModelCacheSource::Cache &ModelCacheSource::cache()
{
	static Cache c;
	return c;
}
