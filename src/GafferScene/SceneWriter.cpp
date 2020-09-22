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

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "IECoreScene/SceneInterface.h"

#include "boost/filesystem.hpp"

#include "tbb/concurrent_unordered_map.h"
#include "tbb/mutex.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

struct LocationWriter
{
	LocationWriter(SceneInterfacePtr output, ConstCompoundDataPtr sets, float time, tbb::mutex& mutex) : m_output( output ), m_sets(sets), m_time( time ), m_mutex( mutex )
	{
	}

	/// first half of this function can be lock free reading data from ScenePlug
	/// once all the data has been read then we take a global lock and write
	/// into the SceneInterface
	bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &scenePath )
	{
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
		const CompoundDataMap &setsMap = m_sets->readable();
		locationSets.reserve( setsMap.size() );

		for( CompoundDataMap::const_iterator it = setsMap.begin(); it != setsMap.end(); ++it)
		{
			ConstPathMatcherDataPtr pathMatcher = IECore::runTimeCast<PathMatcherData>( it->second );

			if( pathMatcher->readable().match( scenePath ) & IECore::PathMatcher::ExactMatch )
			{
				locationSets.push_back( it->first );
			}
		}

		tbb::mutex::scoped_lock scopedLock( m_mutex );

		if( !scenePath.empty() )
		{
			m_output = m_output->child( scenePath.back(), SceneInterface::CreateIfMissing );
		}

		for( CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; it++ )
		{
			m_output->writeAttribute( it->first, it->second.get(), m_time );
		}

		if( globals && !globals->members().empty() )
		{
			m_output->writeAttribute( "gaffer:globals", globals.get(), m_time );
		}

		if( object->typeId() != IECore::NullObjectTypeId && scenePath.size() > 0 )
		{
			m_output->writeObject( object.get(), m_time );
		}

		m_output->writeBound( Imath::Box3d( Imath::V3f( bound.min ), Imath::V3f( bound.max ) ), m_time );

		if( transformData )
		{
			m_output->writeTransform( transformData.get(), m_time );
		}

		if( !locationSets.empty() )
		{
			m_output->writeTags( locationSets );
		}

		return true;
	}

	SceneInterfacePtr m_output;
	ConstCompoundDataPtr m_sets;
	float m_time;
	tbb::mutex &m_mutex;
};

}

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( SceneWriter );

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

	const std::string fileName = fileNamePlug()->getValue();
	createDirectories( fileName );
	SceneInterfacePtr output = SceneInterface::create( fileName, IndexedIO::Write );
	tbb::mutex mutex;
	ContextPtr context = new Context( *Context::current() );
	Context::Scope scopedContext( context.get() );

	for( std::vector<float>::const_iterator it = frames.begin(); it != frames.end(); ++it )
	{
		context->setFrame( *it );

		ConstCompoundDataPtr sets = SceneAlgo::sets( scene );
		LocationWriter locationWriter( output, sets, context->getTime(), mutex );

		SceneAlgo::parallelProcessLocations( scene, locationWriter );
	}
}

bool SceneWriter::requiresSequenceExecution() const
{
	return true;
}


void SceneWriter::createDirectories( const std::string &fileName ) const
{
	boost::filesystem::path filePath( fileName );
	boost::filesystem::path directory = filePath.parent_path();
	if( !directory.empty() )
	{
		boost::filesystem::create_directories( directory );
	}
}
