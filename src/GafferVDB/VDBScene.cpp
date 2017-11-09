//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, John Haddon. All rights reserved.
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


#include "openvdb/openvdb.h"

#include "IECore/SceneInterface.h"
#include "IECore/SimpleTypedData.h"
#include "GafferVDB/TypeIds.h"
#include "GafferVDB/VDBObject.h"

#include "GafferScene/ScenePlug.h"

using namespace Imath;
using namespace IECore;
using namespace GafferVDB;

using namespace openvdb;
namespace
{

const SceneInterface::Name g_objectName("vdb");

class VDBScene : public SceneInterface
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( VDBScene, VDBSceneTypeId, IECore::SceneInterface );

		VDBScene( const std::string &fileName, IndexedIO::OpenMode openMode )
		: SceneInterface(),
			m_rootData( new RootData(fileName) )

		{
		}

		~VDBScene() override
		{
		}

		std::string fileName() const override
		{
			return rootData().m_fileName;
		}

		Name name() const override
		{
			if ( m_parent )
			{
				return g_objectName;
			}
			else
			{
				return Name();
			}

		}

		void path( Path &p ) const override
		{

			if ( m_parent )
			{
				p = { g_objectName };
			}
			else
			{
				p = {};
			}
		}

		////////////////////////////////////////////////////
		// Bounds
		////////////////////////////////////////////////////

		Imath::Box3d readBound( double time ) const override
		{
			const Imath::Box3f bound = rootData().m_vdbObject->bound();
			return Imath::Box3d(bound.min, bound.max);
		}

		 void writeBound( const Imath::Box3d &bound, double time ) override
		 {
			 throw IECore::NotImplementedException("");
		 }

		////////////////////////////////////////////////////
		// Transforms
		////////////////////////////////////////////////////

		ConstDataPtr readTransform( double time ) const override
		{
			return new M44dData;
		}

		Imath::M44d readTransformAsMatrix( double time ) const override
		{
			return M44d();
		}

		void writeTransform( const Data *transform, double time ) override
		{
			throw IECore::NotImplementedException("");
		}

		////////////////////////////////////////////////////
		// Attributes
		////////////////////////////////////////////////////

		bool hasAttribute( const Name &name ) const override
		{
			return false;
		}

		/// Fills attrs with the names of all attributes available in the current directory
		void attributeNames( NameList &attrs ) const override
		{
			attrs = {};
		}

		ConstObjectPtr readAttribute( const Name &name, double time ) const override
		{
			return nullptr;
		}

		void writeAttribute( const Name &name, const Object *attribute, double time ) override
		{
			throw IECore::NotImplementedException("");
		}

		////////////////////////////////////////////////////
		// Tags
		////////////////////////////////////////////////////

		bool hasTag( const Name &name, int filter = LocalTag ) const override
		{
			return false;
		}

		void readTags( NameList &tags, int filter = LocalTag ) const override
		{
			tags = {};
		}

		void writeTags( const NameList &tags ) override
		{
			throw IECore::NotImplementedException("");
		}

		////////////////////////////////////////////////////
		// Objects
		////////////////////////////////////////////////////

		bool hasObject() const override
		{
			return true;
		}

		ConstObjectPtr readObject( double time ) const override
		{
			if ( m_parent )
			{
				return rootData().m_vdbObject;
			}
			else
			{
				return nullptr;
			}

		}

		PrimitiveVariableMap readObjectPrimitiveVariables( const std::vector<InternedString> &primVarNames, double time ) const override
		{
			return PrimitiveVariableMap();
		}

		void writeObject( const Object *object, double time ) override
		{
			throw IECore::NotImplementedException("");
		}

		////////////////////////////////////////////////////
		// Hierarchy
		////////////////////////////////////////////////////

		/// Convenience method to determine if a child exists
		bool hasChild( const Name &name ) const override
		{
			if ( !m_parent && name == g_objectName)
			{
				return true;
			}

			return false;
		}
		/// Queries the names of any existing children of path() within
		/// the scene.
		void childNames( NameList &childNames ) const override
		{
			if ( m_parent )
			{
				childNames = NameList();
			}
			else
			{
				childNames = { g_objectName };
			}

		}
		/// Returns an object for the specified child location in the scene.
		/// If the child does not exist then it will behave according to the
		/// missingBehavior parameter. May throw and exception, may return a NULL pointer,
		/// or may create the child (if that is possible).
		/// Bounding boxes will be automatically propagated up from the children
		/// to the parent as it is written.
		SceneInterfacePtr child( const Name &name, MissingBehaviour missingBehaviour = ThrowIfMissing ) override
		{
			if ( m_parent )
			{
				if (missingBehaviour == ThrowIfMissing)
				{
					throw IECore::InvalidArgumentException("VDBSCene::child(): no child called \" + name.string()");
				}
				else if (missingBehaviour == CreateIfMissing)
				{
					throw IECore::InvalidArgumentException("VDBScene::child(): CreateIfMissing not supported");
				}
				return nullptr;
			}
			else
			{
				if (name == g_objectName)
				{
					return new VDBScene(this);
				}
				else if (missingBehaviour == ThrowIfMissing)
				{
					throw IECore::InvalidArgumentException("VDBSCene::child(): no child called \" + name.string()");
				}
				else if (missingBehaviour == CreateIfMissing)
				{
					throw IECore::InvalidArgumentException("VDBScene::child(): CreateIfMissing not supported");
				}
			}


			return SceneInterfacePtr();
		}

		/// Returns a read-only interface for a child location in the scene.
		ConstSceneInterfacePtr child( const Name &name, MissingBehaviour missingBehaviour = ThrowIfMissing ) const override
		{
			return const_cast< VDBScene* >( this )->child( name, missingBehaviour );
		}

		/// Returns a writable interface to a new child. Throws an exception if it already exists.
		/// Bounding boxes will be automatically propagated up from the children
		/// to the parent as it is written.
		SceneInterfacePtr createChild( const Name &name ) override
		{
			throw IECore::NotImplementedException("");
		}

		/// Returns a interface for querying the scene at the given path (full path).
		SceneInterfacePtr scene( const Path &path, MissingBehaviour missingBehaviour = ThrowIfMissing ) override
		{
			if ( path.empty() )
			{
				if ( m_parent )
				{
					return m_parent;
				}
				else
				{
					return this;
				}
			}
			else if ( path.size() == 1 && path[0] == g_objectName )
			{
				if ( m_parent )
				{
					return this;
				}
				else
				{
					return new VDBScene( this );
				}
			}
			else
			{
				if (missingBehaviour == ThrowIfMissing)
				{
					std::string pathStr;
					GafferScene::ScenePlug::pathToString(path, pathStr);
					bool isRoot = (m_parent != nullptr);
					if ( isRoot )
					{
						throw IECore::InvalidArgumentException("VDBSCene::scene(): no path called '" + pathStr + "' is root!" );
					}
					else
					{
						throw IECore::InvalidArgumentException("VDBSCene::scene(): no path called '" + pathStr + "'");
					}

				}
				else if (missingBehaviour == CreateIfMissing)
				{
					throw IECore::NotImplementedException("VDBScene::scene(): CreateIfMissing not supported");
				}
				return nullptr;
			}
		}

		/// Returns a const interface for querying the scene at the given path (full path).
		ConstSceneInterfacePtr scene( const Path &path, MissingBehaviour missingBehaviour = ThrowIfMissing ) const override
		{
			return const_cast< VDBScene* >( this )->scene( path, missingBehaviour );
		}

		////////////////////////////////////////////////////
		// Hash
		////////////////////////////////////////////////////

		void hash( HashType hashType, double time, MurmurHash &h ) const override
		{
			SceneInterface::hash (hashType, time, h);
			h.append( hashType );

			if ( hashType == ChildNamesHash )
			{
				h.append( m_parent == nullptr );
			}
			else if ( hashType == ObjectHash || hashType == BoundHash)
			{
				h.append( rootData().m_fileName );
				h.append( m_parent == nullptr );
			}
			else if ( hashType == HierarchyHash )
			{
				h.append( m_parent == nullptr );
			}
		}

	private :

		VDBScene( VDBScene* parent )
		: m_parent( parent )
		{
		}

		static FileFormatDescription<VDBScene> g_description;

		struct RootData
		{
			RootData(const std::string& filename)
			: m_fileName(filename),
			  m_vdbObject(new VDBObject(m_fileName) )
			{
			}


			std::string m_fileName;
			VDBObject::Ptr m_vdbObject;
		};

		RootData &rootData() const
		{
			if ( m_parent )
				return m_parent->rootData();
			else
				return *m_rootData;
		}

		std::shared_ptr<RootData> m_rootData;
		Ptr m_parent;

};

IE_CORE_DEFINERUNTIMETYPED( VDBScene )

SceneInterface::FileFormatDescription<VDBScene> VDBScene::g_description(".vdb", IndexedIO::Read );

} // namespace
