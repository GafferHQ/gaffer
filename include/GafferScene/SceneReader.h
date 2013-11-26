//////////////////////////////////////////////////////////////////////////
//  
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

#ifndef GAFFERSCENE_SCENEREADER_H
#define GAFFERSCENE_SCENEREADER_H

#include "tbb/enumerable_thread_specific.h"

#include "GafferScene/FileSource.h"

namespace GafferScene
{

class SceneReader : public FileSource
{

	public :

		SceneReader( const std::string &name=defaultName<SceneReader>() );
		virtual ~SceneReader();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::SceneReader, SceneReaderTypeId, FileSource )
				
	protected :
	
		virtual void hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		virtual void hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;

		virtual Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstInternedStringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstCompoundObjectPtr computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const;
	
	private :
	
		void plugSet( Gaffer::Plug *plug );
		
		// The typical access patterns for the SceneReader include accessing
		// the same file repeatedly, and also the same path within the file
		// repeatedly (to hash a value then compute it for instance, or to get
		// the bound and then the object). We take advantage of that by storing
		// the last accessed scene in thread local storage - we can then avoid
		// the relatively expensive lookups necessary to find the appropriate
		// SceneInterfacePtr for a query.
		struct LastScene
		{
			std::string fileName;
			IECore::ConstSceneInterfacePtr fileNameScene;
			ScenePlug::ScenePath path;
			IECore::ConstSceneInterfacePtr pathScene;
		};
		mutable tbb::enumerable_thread_specific<LastScene> m_lastScene;
		// Returns the SceneInterface for the current filename (in the current Context)
		// and specified path, using m_lastScene to accelerate the lookups.
		IECore::ConstSceneInterfacePtr scene( const ScenePath &path ) const;
		
		static const double g_frameRate;
};

IE_CORE_DECLAREPTR( SceneReader )

} // namespace GafferScene

#endif // GAFFERSCENE_SCENEREADER_H
