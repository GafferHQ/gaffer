//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
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

#ifndef GAFFERVDB_VDBOBJECT_H
#define GAFFERVDB_VDBOBJECT_H

#include <unordered_map>

#include "openvdb/openvdb.h"

#include "OpenEXR/ImathBox.h"

#include "IECore/Object.h"
#include "IECore/CompoundObject.h"
#include "IECoreScene/VisibleRenderable.h"
#include "IECore/VectorTypedData.h"

#include "GafferVDB/Export.h"
#include "GafferVDB/TypeIds.h"

namespace GafferVDB
{

class GAFFERVDB_API VDBObject : public IECoreScene::VisibleRenderable
{

	public :

		VDBObject();

		//! initialise VDBObject from a vdb file
		VDBObject( const std::string &filename );

		IE_CORE_DECLAREEXTENSIONOBJECT( GafferVDB::VDBObject, VDBObjectTypeId, IECoreScene::VisibleRenderable );

		void insertGrid( openvdb::GridBase::Ptr grid );
		void removeGrid( const std::string &name );

		openvdb::GridBase::ConstPtr findGrid( const std::string &name ) const;
		openvdb::GridBase::Ptr findGrid( const std::string &name );

		std::vector<std::string> gridNames() const;

		Imath::Box3f bound() const override;
		void render( IECoreScene::Renderer *renderer ) const override;

		IECore::CompoundObjectPtr metadata( const std::string &name );

		//! Are the grids in this VDBObject unmodified from the vdb file in filename?
		//! Useful for passing VDB objects to renders by filename instead of memory buffer
		bool unmodifiedFromFile() const;

		//! path to VDB file used to initialise this object
		//! empty for procedurally generated VDBs
		std::string fileName() const
		{
			return m_fileName;
		}

	protected :

		virtual ~VDBObject();

	private :

		static const unsigned int m_ioVersion;

		class GAFFERVDB_API HashedGrid
		{
			public:
				HashedGrid() : m_hashValid( false ), m_unmodifiedFromFile( false )
				{
				}

				HashedGrid( openvdb::GridBase::Ptr grid, bool initFromFile = false ) : m_grid( grid ), m_hashValid( false ), m_unmodifiedFromFile( initFromFile )
				{
				}

				IECore::MurmurHash hash() const;
				openvdb::GridBase::Ptr grid() const;
				bool unmodifiedFromFile() const;
				void markedAsEdited();

			private:
				openvdb::GridBase::Ptr m_grid;
				mutable bool m_hashValid;
				mutable IECore::MurmurHash m_hash;
				bool m_unmodifiedFromFile;
		};

		std::unordered_map<std::string, HashedGrid> m_grids;

		//! store the filename incase we need don't modify the vdb and we can pass it on to clients who can only deal with file VDBs
		std::string m_fileName;
};

IE_CORE_DECLAREPTR( VDBObject )

} // namespace GafferVDB

#endif // GAFFERVDB_VDBOBJECT_H
