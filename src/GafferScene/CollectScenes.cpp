//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/CollectScenes.h"

#include "GafferScene/SceneAlgo.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "IECore/NullObject.h"

#include "boost/container/flat_map.hpp"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// RootTree
//////////////////////////////////////////////////////////////////////////

namespace
{

// Used to represent the tree of locations specified by `rootNamesPlug()`.
// This allows us to quickly find the matching root for any output location
// via `locationOrAncestor()`.
class RootTree : public IECore::Data
{

	public :

		struct Location;
		using LocationPtr = std::unique_ptr<Location>;
		using ChildMap = boost::container::flat_map<IECore::InternedString, LocationPtr>;

		struct Location
		{

			Location( size_t depth )
				:	depth( depth ), childNames( new InternedStringVectorData() )
			{
			}

			bool isRoot() const
			{
				return !rootVariableValue.empty();
			}

			// The path to this location, but exactly as the user spelled
			// it in `rootNamesPlug()` (may or may not have a leading or
			// trailing '/'). Empty if not a collection root.
			string rootVariableValue;
			size_t depth;
			ChildMap children;
			InternedStringVectorDataPtr childNames;

		};

		RootTree( const IECore::StringVectorData *roots )
			:	m_treeRoot( new Location( 0 ) )
		{
			ScenePlug::ScenePath path;
			for( const auto &root : roots->readable() )
			{
				ScenePlug::stringToPath( root, path );
				if( path.empty() )
				{
					continue;
				}

				Location *location = m_treeRoot.get();
				for( const auto &name : path )
				{
					const auto inserted = location->children.insert( ChildMap::value_type( name, LocationPtr() ) );
					if( inserted.second )
					{
						if( location->isRoot() )
						{
							throw IECore::Exception( boost::str( boost::format( "\"%1%\" contains nested roots" ) % location->rootVariableValue ) );
						}
						inserted.first->second.reset( new Location( location->depth + 1 ) );
						location->childNames->writable().push_back( name );
					}
					location = inserted.first->second.get();
				}

				if( location->isRoot() )
				{
					// Duplicate found - skip.
					continue;
				}

				if( !location->children.empty() )
				{
					throw IECore::Exception( boost::str( boost::format( "\"%1%\" contains nested roots" ) % root ) );
				}

				location->rootVariableValue = root;
				m_roots.push_back( root );
			}
		}

		const Location *locationOrAncestor( const ScenePlug::ScenePath &path ) const
		{
			const Location *result = m_treeRoot.get();
			for( const auto &name : path )
			{
				const auto it = result->children.find( name );
				if( it != result->children.end() )
				{
					result = it->second.get();
				}
				else
				{
					break;
				}
			}
			return result;
		}

		const vector<string> &roots() const
		{
			return m_roots;
		}

	private :

		LocationPtr m_treeRoot;
		vector<string> m_roots;

};

IE_CORE_DECLAREPTR( RootTree )

} // namespace

//////////////////////////////////////////////////////////////////////////
// SourceScope and SourcePathScope
//////////////////////////////////////////////////////////////////////////

class CollectScenes::SourceScope : public Context::EditableScope
{

	public :

		SourceScope( const Context *context, const InternedString &rootVariable )
			:	EditableScope( context ), m_rootVariable( rootVariable )
		{
		}

		void setRoot( const std::string &root )
		{
			set( m_rootVariable, root );
		}

	private :

		InternedString m_rootVariable;

};

class CollectScenes::SourcePathScope : public SourceScope
{

	public :

		SourcePathScope( const Context *context, const CollectScenes *collectScenes, const ScenePlug::ScenePath &downstreamPath )
			:	SourceScope( context, collectScenes->rootNameVariablePlug()->getValue() )
		{
			// Evaluate RootTree in global scope.
			remove( ScenePlug::scenePathContextName );
			m_rootTree = boost::static_pointer_cast<const RootTree>( collectScenes->rootTreePlug()->getValue() );
			m_rootTreeLocation = m_rootTree->locationOrAncestor( downstreamPath );
			if( m_rootTreeLocation->isRoot() )
			{
				setRoot( m_rootTreeLocation->rootVariableValue );
				ScenePlug::ScenePath upstreamPath;
				// We evaluate the sourceRootPlug _after_ setting the root name,
				// so that users can use the root name in expressions and
				// substitutions.
				ScenePlug::stringToPath( collectScenes->sourceRootPlug()->getValue(), upstreamPath );
				upstreamPath.insert( upstreamPath.end(), downstreamPath.begin() + m_rootTreeLocation->depth, downstreamPath.end() );
				set( ScenePlug::scenePathContextName, upstreamPath );
			}
			else
			{
				set( ScenePlug::scenePathContextName, downstreamPath );
			}
		}

		const RootTree::Location *rootTreeLocation() const
		{
			return m_rootTreeLocation;
		}

		static bool affectedBy( const CollectScenes *collectScenes, const Plug *input )
		{
			return
				input == collectScenes->rootNameVariablePlug() ||
				input == collectScenes->rootTreePlug() ||
				input == collectScenes->sourceRootPlug()
			;
		}

	private :

		ConstRootTreePtr m_rootTree;
		const RootTree::Location *m_rootTreeLocation;

};

//////////////////////////////////////////////////////////////////////////
// CollectScenes
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( CollectScenes );

size_t CollectScenes::g_firstPlugIndex = 0;

CollectScenes::CollectScenes( const std::string &name )
	:	SceneProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringVectorDataPlug( "rootNames", Plug::In, new StringVectorData() ) );
	addChild( new StringPlug( "rootNameVariable", Plug::In, "collect:rootName" ) );
	addChild( new StringPlug( "sourceRoot", Plug::In, "/" ) );
	addChild( new ObjectPlug( "__rootTree", Plug::Out, IECore::NullObject::defaultNullObject() ) );

	outPlug()->childBoundsPlug()->setFlags( Plug::AcceptsDependencyCycles, true );
}

CollectScenes::~CollectScenes()
{
}

Gaffer::StringVectorDataPlug *CollectScenes::rootNamesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::StringVectorDataPlug *CollectScenes::rootNamesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 0 );
}

Gaffer::StringPlug *CollectScenes::rootNameVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *CollectScenes::rootNameVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *CollectScenes::sourceRootPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *CollectScenes::sourceRootPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::ObjectPlug *CollectScenes::rootTreePlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::ObjectPlug *CollectScenes::rootTreePlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 3 );
}

void CollectScenes::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );

	if( input == rootNamesPlug() )
	{
		outputs.push_back( rootTreePlug() );
	}

	if(
		input == outPlug()->childBoundsPlug() ||
		SourcePathScope::affectedBy( this, input ) ||
		input == inPlug()->boundPlug()
	)
	{
		outputs.push_back( outPlug()->boundPlug() );
	}

	if( SourcePathScope::affectedBy( this, input ) || input == inPlug()->transformPlug() )
	{
		outputs.push_back( outPlug()->transformPlug() );
	}

	if( SourcePathScope::affectedBy( this, input ) || input == inPlug()->attributesPlug() )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}

	if( SourcePathScope::affectedBy( this, input ) || input == inPlug()->objectPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}

	if(
		SourcePathScope::affectedBy( this, input ) ||
		input == inPlug()->existsPlug() ||
		input == inPlug()->childNamesPlug()
	)
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}

	if(
		input == rootTreePlug() ||
		input == rootNameVariablePlug() ||
		input == inPlug()->globalsPlug()
	)
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}

	if(
		input == rootTreePlug() ||
		input == inPlug()->setNamesPlug() ||
		input == rootNameVariablePlug()
	)
	{
		outputs.push_back( outPlug()->setNamesPlug() );
	}

	if(
		input == rootTreePlug() ||
		input == inPlug()->setPlug() ||
		input == sourceRootPlug() ||
		input == rootNameVariablePlug()
	)
	{
		outputs.push_back( outPlug()->setPlug() );
	}
}

void CollectScenes::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneProcessor::hash( output, context, h );

	if( output == rootTreePlug() )
	{
		rootNamesPlug()->hash( h );
	}
}

void CollectScenes::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == rootTreePlug() )
	{
		ConstStringVectorDataPtr roots = rootNamesPlug()->getValue();
		static_cast<ObjectPlug *>( output )->setValue(
			new RootTree( roots.get() )
		);
		return;
	}

	SceneProcessor::compute( output, context );
}

void CollectScenes::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SourcePathScope sourcePathScope( context, this, path );
	if( !sourcePathScope.rootTreeLocation()->isRoot() )
	{
		h = outPlug()->childBoundsPlug()->hash();
	}
	else
	{
		h = inPlug()->boundPlug()->hash();
	}
}

Imath::Box3f CollectScenes::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	SourcePathScope sourcePathScope( context, this, path );
	if( !sourcePathScope.rootTreeLocation()->isRoot() )
	{
		return outPlug()->childBoundsPlug()->getValue();
	}
	else
	{
		return inPlug()->boundPlug()->getValue();
	}
}

void CollectScenes::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SourcePathScope sourcePathScope( context, this, path );
	if( !sourcePathScope.rootTreeLocation()->isRoot() )
	{
		SceneProcessor::hashTransform( path, context, parent, h );
	}
	else
	{
		h = inPlug()->transformPlug()->hash();
	}
}

Imath::M44f CollectScenes::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	SourcePathScope sourcePathScope( context, this, path );
	if( !sourcePathScope.rootTreeLocation()->isRoot() )
	{
		return M44f();
	}
	else
	{
		return inPlug()->transformPlug()->getValue();
	}
}

void CollectScenes::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SourcePathScope sourcePathScope( context, this, path );
	if( !sourcePathScope.rootTreeLocation()->isRoot() )
	{
		SceneProcessor::hashAttributes( path, context, parent, h );
	}
	else
	{
		h = inPlug()->attributesPlug()->hash();
	}
}

IECore::ConstCompoundObjectPtr CollectScenes::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	SourcePathScope sourcePathScope( context, this, path );
	if( !sourcePathScope.rootTreeLocation()->isRoot() )
	{
		return outPlug()->attributesPlug()->defaultValue();
	}
	else
	{
		return inPlug()->attributesPlug()->getValue();
	}
}

void CollectScenes::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SourcePathScope sourcePathScope( context, this, path );
	if( !sourcePathScope.rootTreeLocation()->isRoot() )
	{
		SceneProcessor::hashObject( path, context, parent, h );
	}
	else
	{
		h = inPlug()->objectPlug()->hash();
	}
}

IECore::ConstObjectPtr CollectScenes::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	SourcePathScope sourcePathScope( context, this, path );
	if( !sourcePathScope.rootTreeLocation()->isRoot() )
	{
		return outPlug()->objectPlug()->defaultValue();
	}
	else
	{
		return inPlug()->objectPlug()->getValue();
	}
}

void CollectScenes::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SourcePathScope sourcePathScope( context, this, path );
	if( !sourcePathScope.rootTreeLocation()->isRoot() )
	{
		h = sourcePathScope.rootTreeLocation()->childNames->Object::hash();
	}
	else
	{
		if( path.size() == sourcePathScope.rootTreeLocation()->depth )
		{
			if( !inPlug()->existsPlug()->getValue() )
			{
				h = inPlug()->childNamesPlug()->defaultValue()->Object::hash();
				return;
			}
		}
		h = inPlug()->childNamesPlug()->hash();
	}
}

IECore::ConstInternedStringVectorDataPtr CollectScenes::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	SourcePathScope sourcePathScope( context, this, path );
	if( !sourcePathScope.rootTreeLocation()->isRoot() )
	{
		return sourcePathScope.rootTreeLocation()->childNames;
	}
	else
	{
		if( path.size() == sourcePathScope.rootTreeLocation()->depth )
		{
			if( !inPlug()->existsPlug()->getValue() )
			{
				return inPlug()->childNamesPlug()->defaultValue();
			}
		}
		return inPlug()->childNamesPlug()->getValue();
	}
}

void CollectScenes::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstRootTreePtr rootTree = boost::static_pointer_cast<const RootTree>( rootTreePlug()->getValue() );
	if( rootTree->roots().size() )
	{
		SourceScope sourceScope( context, rootNameVariablePlug()->getValue() );
		sourceScope.setRoot( rootTree->roots()[0] );
		h = inPlug()->globalsPlug()->hash();
	}
	else
	{
		h = inPlug()->globalsPlug()->defaultValue()->Object::hash();
	}
}

IECore::ConstCompoundObjectPtr CollectScenes::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstRootTreePtr rootTree = boost::static_pointer_cast<const RootTree>( rootTreePlug()->getValue() );
	if( rootTree->roots().size() )
	{
		SourceScope sourceScope( context, rootNameVariablePlug()->getValue() );
		sourceScope.setRoot( rootTree->roots()[0] );
		return inPlug()->globalsPlug()->getValue();
	}
	else
	{
		return inPlug()->globalsPlug()->defaultValue();
	}
}

void CollectScenes::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashSetNames( context, parent, h );

	ConstRootTreePtr rootTree = boost::static_pointer_cast<const RootTree>( rootTreePlug()->getValue() );
	const ValuePlug *inSetNamesPlug = inPlug()->setNamesPlug();

	SourceScope sourceScope( context, rootNameVariablePlug()->getValue() );
	for( const auto &root : rootTree->roots() )
	{
		sourceScope.setRoot( root );
		inSetNamesPlug->hash( h );
	}
}

IECore::ConstInternedStringVectorDataPtr CollectScenes::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstRootTreePtr rootTree = boost::static_pointer_cast<const RootTree>( rootTreePlug()->getValue() );

	InternedStringVectorDataPtr setNamesData = new InternedStringVectorData;
	vector<InternedString> &setNames = setNamesData->writable();

	const InternedStringVectorDataPlug *inSetNamesPlug = inPlug()->setNamesPlug();

	SourceScope sourceScope( context, rootNameVariablePlug()->getValue() );
	for( const auto &root : rootTree->roots() )
	{
		sourceScope.setRoot( root );
		ConstInternedStringVectorDataPtr inSetNamesData = inSetNamesPlug->getValue();
		for( const auto &setName : inSetNamesData->readable() )
		{
			if( find( setNames.begin(), setNames.end(), setName ) == setNames.end() )
			{
				setNames.push_back( setName );
			}
		}
	}

	return setNamesData;
}

void CollectScenes::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashSet( setName, context, parent, h );

	ConstRootTreePtr rootTree;
	{
		ScenePlug::GlobalScope globalScope( context );
		rootTree = boost::static_pointer_cast<const RootTree>( rootTreePlug()->getValue() );
	}

	const PathMatcherDataPlug *inSetPlug = inPlug()->setPlug();
	const StringPlug *sourceRootPlug = this->sourceRootPlug();

	SourceScope sourceScope( context, rootNameVariablePlug()->getValue() );
	for( const auto &root : rootTree->roots() )
	{
		sourceScope.setRoot( root );
		inSetPlug->hash( h );
		sourceRootPlug->hash( h );
		h.append( root );
	}
}

IECore::ConstPathMatcherDataPtr CollectScenes::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstRootTreePtr rootTree;
	{
		ScenePlug::GlobalScope globalScope( context );
		rootTree = boost::static_pointer_cast<const RootTree>( rootTreePlug()->getValue() );
	}

	PathMatcherDataPtr setData = new PathMatcherData;
	PathMatcher &set = setData->writable();

	const PathMatcherDataPlug *inSetPlug = inPlug()->setPlug();
	const StringPlug *sourceRootPlug = this->sourceRootPlug();

	SourceScope sourceScope( context, rootNameVariablePlug()->getValue() );
	ScenePlug::ScenePath prefix;
	for( const auto &root : rootTree->roots() )
	{
		sourceScope.setRoot( root );
		ConstPathMatcherDataPtr inSetData = inSetPlug->getValue();
		const PathMatcher &inSet = inSetData->readable();
		if( !inSet.isEmpty() )
		{
			ScenePlug::stringToPath( root, prefix );
			const string root = sourceRootPlug->getValue();
			if( !root.empty() )
			{
				set.addPaths( inSet.subTree( root ), prefix );
			}
			else
			{
				set.addPaths( inSet, prefix );
			}
		}
	}

	return setData;
}

