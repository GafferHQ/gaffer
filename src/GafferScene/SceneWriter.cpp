//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2014, Image Engine Design inc. All rights reserved.
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

#include "GafferScene/SceneWriter.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/SceneReader.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "IECoreScene/SceneInterface.h"

#include <filesystem>
#include <unordered_map>

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

struct LocationData
{
	LocationData( const ScenePlug *scene, const ScenePlug::ScenePath &path, const CompoundData *setsForTags )
		:	m_path( path ),
			m_attributes( scene->attributesPlug()->getValue() ),
			m_object( scene->objectPlug()->getValue() ),
			m_bound( scene->boundPlug()->getValue() ),
			m_transform( scene->transformPlug()->getValue() ),
			m_childNames( scene->childNamesPlug()->getValue() )
	{
		if( setsForTags )
		{
			const CompoundDataMap &setsMap = setsForTags->readable();
			m_tags.reserve( setsMap.size() );

			for( const auto &[name, data] : setsMap )
			{
				auto pathMatcher = static_cast<const PathMatcherData *>( data.get() );
				if( pathMatcher->readable().match( path ) & IECore::PathMatcher::ExactMatch )
				{
					m_tags.push_back( name );
				}
			}
		}
	}

	void write( IECoreScene::SceneInterface *root, float time ) const
	{
		SceneInterfacePtr scene = root;
		for( auto &p : m_path )
		{
			scene = scene->child( p, SceneInterface::CreateIfMissing );
		}

		if( m_object->typeId() != IECore::NullObjectTypeId && m_path.size() > 0 )
		{
			scene->writeObject( m_object.get(), time );
		}

		scene->writeBound( Imath::Box3d( Imath::V3f( m_bound.min ), Imath::V3f( m_bound.max ) ), time );

		if( m_path.size() )
		{
			M44dDataPtr td = new IECore::M44dData( Imath::M44d (
				m_transform[0][0], m_transform[0][1], m_transform[0][2], m_transform[0][3],
				m_transform[1][0], m_transform[1][1], m_transform[1][2], m_transform[1][3],
				m_transform[2][0], m_transform[2][1], m_transform[2][2], m_transform[2][3],
				m_transform[3][0], m_transform[3][1], m_transform[3][2], m_transform[3][3]
			) );
			scene->writeTransform( td.get(), time );
		}

		for( const auto &[name, value] : m_attributes->members() )
		{
			scene->writeAttribute( name, value.get(), time );
		}

		if( !m_tags.empty() )
		{
			scene->writeTags( m_tags );
		}

		for( const auto &childName : m_childNames->readable() )
		{
			// `SceneAlgo::parallelGatherLocations()` may visit children in any
			// order. Pre-create SceneInterface children here so that they are
			// created in the correct order.
			scene->child( childName, SceneInterface::CreateIfMissing );
		}
	}

	private :

		ScenePlug::ScenePath m_path;
		ConstCompoundObjectPtr m_attributes;
		ConstObjectPtr m_object;
		Imath::Box3f m_bound;
		Imath::M44f m_transform;
		ConstInternedStringVectorDataPtr m_childNames;
		SceneInterface::NameList m_tags;

};

} // namespace

GAFFER_NODE_DEFINE_TYPE( SceneWriter );

size_t SceneWriter::g_firstPlugIndex = 0;

SceneWriter::SceneWriter( const std::string &name )
	: TaskNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in", Plug::In ) );
	addChild( new StringPlug( "fileName" ) );
	addChild( new ScenePlug( "out", Plug::Out, Plug::Default & ~Plug::Serialisable ) );
	outPlug()->setInput( inPlug() );
}

SceneWriter::~SceneWriter()
{
}

ScenePlug *SceneWriter::inPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *SceneWriter::inPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

StringPlug *SceneWriter::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *SceneWriter::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

ScenePlug *SceneWriter::outPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 2 );
}

const ScenePlug *SceneWriter::outPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 2 );
}

IECore::MurmurHash SceneWriter::hash( const Gaffer::Context *context ) const
{
	const ScenePlug *scenePlug = inPlug()->source<ScenePlug>();
	if ( ( fileNamePlug()->getValue() == "" ) || ( scenePlug == inPlug() ) )
	{
		return IECore::MurmurHash();
	}

	IECore::MurmurHash h = TaskNode::hash( context );
	h.append( fileNamePlug()->hash() );
	/// \todo hash the actual scene when we have a hierarchyHash
	h.append( (uint64_t)scenePlug );
	h.append( context->hash() );

	return h;
}

void SceneWriter::execute() const
{
	std::vector<float> frame( 1, Context::current()->getFrame() );
	executeSequence( frame );
}

void SceneWriter::executeSequence( const std::vector<float> &frames ) const
{
	const ScenePlug *scene = inPlug()->getInput<ScenePlug>();
	if( !scene )
	{
		throw IECore::Exception( "No input scene" );
	}

	SceneInterfacePtr output;
	Context::EditableScope scope( Context::current() );

	for( auto frame : frames )
	{
		scope.setFrame( frame );

		ConstCompoundDataPtr sets;
		bool useSetsAPI = true;
		const std::string fileName = fileNamePlug()->getValue();
		if( !output || output->fileName() != fileName )
		{
			createDirectories( fileName );
			output = SceneInterface::create( fileName, IndexedIO::Write );
			sets = SceneAlgo::sets( scene );
			useSetsAPI = SceneReader::useSetsAPI( output.get() );
		}

		SceneAlgo::parallelGatherLocations(

			scene,

			// Collect LocationData from each location in parallel.

			[&] ( const ScenePlug *scene, const ScenePlug::ScenePath &path ) {
				return LocationData( scene, path, useSetsAPI ? nullptr : sets.get() );
			},

			// Write to output serially, because SceneInterfaces are not
			// thread-safe for writing.

			[&] ( const LocationData &locationData ) {
				locationData.write( output.get(), scope.context()->getTime() );
			}

		);

		if( useSetsAPI && sets )
		{
			for( const auto &[name, data] : sets->readable() )
			{
				output->writeSet( name, static_cast<const PathMatcherData *>( data.get() )->readable() );
			}
		}

		ConstCompoundObjectPtr globals = scene->globals();
		if( !globals->members().empty() )
		{
			output->writeAttribute( "gaffer:globals", globals.get(), scope.context()->getTime() );
		}

	}
}

bool SceneWriter::requiresSequenceExecution() const
{
	return true;
}

void SceneWriter::createDirectories( const std::string &fileName ) const
{
	const std::filesystem::path filePath( fileName );
	const std::filesystem::path directory = filePath.parent_path();
	if( !directory.empty() )
	{
		std::filesystem::create_directories( directory );
	}
}
