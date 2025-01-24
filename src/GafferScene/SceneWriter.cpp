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

#include "tbb/mutex.h"

#include <filesystem>
#include <unordered_map>

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

struct LocationWriter
{

	LocationWriter( SceneInterface *rootOutput, const CompoundData *sets, float time, tbb::mutex &mutex )
		: m_parent( nullptr ), m_rootOutput( rootOutput ), m_sets( sets ), m_time( time ), m_mutex( mutex )
	{
	}

	// Called by `parallelProcessLocations()` to create child functors for each location.
	LocationWriter( const LocationWriter &parent )
		: m_parent( &parent ), m_rootOutput( parent.m_rootOutput ), m_sets( parent.m_sets ), m_time( parent.m_time ), m_mutex( parent.m_mutex )
	{
	}

	~LocationWriter()
	{
		// Some implementations of SceneInterface may perform writing when we release
		// the SceneInterfaces, so we need to hold the lock while freeing them.
		tbb::mutex::scoped_lock scopedLock( m_mutex );
		m_childOutputs.clear();
	}

	bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &scenePath )
	{
		// First read all the scene data for this location. We don't need the lock
		// for this so we can read multiple locations in parallel.

		ConstCompoundObjectPtr attributes = scene->attributesPlug()->getValue();

		ConstCompoundObjectPtr globals;

		ConstObjectPtr object = scene->objectPlug()->getValue();
		Imath::Box3f bound = scene->boundPlug()->getValue();

		IECore::M44dDataPtr transformData;

		if( scenePath.empty() )
		{
			globals = scene->globals();
		}
		else
		{
			Imath::M44f t = scene->transformPlug()->getValue();
			transformData = new IECore::M44dData( Imath::M44d (
				t[0][0], t[0][1], t[0][2], t[0][3],
				t[1][0], t[1][1], t[1][2], t[1][3],
				t[2][0], t[2][1], t[2][2], t[2][3],
				t[3][0], t[3][1], t[3][2], t[3][3]
			) );
		}

		SceneInterface::NameList locationSets;
		if( m_sets )
		{
			const CompoundDataMap &setsMap = m_sets->readable();
			locationSets.reserve( setsMap.size() );

			for( const auto &[name, data] : setsMap )
			{
				auto pathMatcher = static_cast<const PathMatcherData *>( data.get() );
				if( pathMatcher->readable().match( scenePath ) & IECore::PathMatcher::ExactMatch )
				{
					locationSets.push_back( name );
				}
			}
		}

		ConstInternedStringVectorDataPtr childNames = scene->childNamesPlug()->getValue();

		// Now write the scene data to the output SceneInterface. We require
		// a lock for this as SceneInterface writing is not thread-safe.

		tbb::mutex::scoped_lock scopedLock( m_mutex );

		SceneInterface *output = m_parent ? m_parent->m_childOutputs.at( scenePath.back() ).get() : m_rootOutput;

		if( object->typeId() != IECore::NullObjectTypeId && scenePath.size() > 0 )
		{
			output->writeObject( object.get(), m_time );
		}

		output->writeBound( Imath::Box3d( Imath::V3f( bound.min ), Imath::V3f( bound.max ) ), m_time );

		if( transformData )
		{
			output->writeTransform( transformData.get(), m_time );
		}

		for( CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; it++ )
		{
			output->writeAttribute( it->first, it->second.get(), m_time );
		}

		if( globals && !globals->members().empty() )
		{
			output->writeAttribute( "gaffer:globals", globals.get(), m_time );
		}

		if( !locationSets.empty() )
		{
			output->writeTags( locationSets );
		}

		for( const auto &childName : childNames->readable() )
		{
			// `SceneAlgo::parallelProcessLocations()` may visit children in any
			// order. Pre-create SceneInterface children here so that they are
			// created in the correct order.
			m_childOutputs[childName] = output->child( childName, SceneInterface::CreateIfMissing );
		}

		return true;
	}

	private :

		const LocationWriter *m_parent;
		SceneInterface *m_rootOutput;
		unordered_map<IECore::InternedString, SceneInterfacePtr> m_childOutputs;
		const CompoundData *m_sets;
		float m_time;
		tbb::mutex &m_mutex;

};

}

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
	tbb::mutex mutex;
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

		LocationWriter locationWriter( output.get(), !useSetsAPI ? sets.get() : nullptr, scope.context()->getTime(), mutex );
		SceneAlgo::parallelProcessLocations( scene, locationWriter );

		if( useSetsAPI && sets )
		{
			for( const auto &[name, data] : sets->readable() )
			{
				output->writeSet( name, static_cast<const PathMatcherData *>( data.get() )->readable() );
			}
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
