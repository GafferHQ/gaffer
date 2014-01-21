//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "boost/bind.hpp"

#include "IECore/SharedSceneInterfaces.h"
#include "IECore/InternedString.h"
#include "IECore/SceneCache.h"

#include "Gaffer/Context.h"

#include "GafferScene/SceneReader.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( SceneReader );

//////////////////////////////////////////////////////////////////////////
// SceneReader implementation
//////////////////////////////////////////////////////////////////////////

/// \todo hard coded framerate should be replaced with a getTime() method on Gaffer::Context or something
const double SceneReader::g_frameRate( 24 );
size_t SceneReader::g_firstPlugIndex = 0;

static IECore::BoolDataPtr g_trueBoolData = new IECore::BoolData( true );

SceneReader::SceneReader( const std::string &name )
	:	FileSource( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "tags" ) );
	plugSetSignal().connect( boost::bind( &SceneReader::plugSet, this, ::_1 ) );
}

SceneReader::~SceneReader()
{
}

Gaffer::StringPlug *SceneReader::tagsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *SceneReader::tagsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

void SceneReader::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FileSource::affects( input, outputs );
	
	if( input == tagsPlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}
}

size_t SceneReader::supportedExtensions( std::vector<std::string> &extensions )
{
	extensions = SceneInterface::supportedExtensions();
	return extensions.size();
}

void SceneReader::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	FileSource::hashBound( path, context, parent, h );

	ConstSceneInterfacePtr s = scene( path );
	const SampledSceneInterface *ss = runTimeCast<const SampledSceneInterface>( s.get() );
	if( !ss || ss->numBoundSamples() > 1 )
	{
		h.append( context->getFrame() );
	}
}

void SceneReader::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	FileSource::hashTransform( path, context, parent, h );
	
	ConstSceneInterfacePtr s = scene( path );
	if( !s )
	{
		return;
	}
	
	const SampledSceneInterface *ss = runTimeCast<const SampledSceneInterface>( s.get() );
	if( !ss || ss->numTransformSamples() > 1 )
	{
		h.append( context->getFrame() );
	}
}

void SceneReader::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstSceneInterfacePtr s = scene( path );
	if( !s )
	{
		h = parent->attributesPlug()->defaultValue()->Object::hash();
		return;
	}
	
	SceneInterface::NameList attributeNames;
	s->attributeNames( attributeNames );
	SceneInterface::NameList tagNames;
	s->readTags( tagNames, IECore::SceneInterface::LocalTag );
	
	if( !attributeNames.size() && !tagNames.size() )
	{
		h = parent->attributesPlug()->defaultValue()->Object::hash();
		return;
	}

	FileSource::hashAttributes( path, context, parent, h );

	bool animated = false;
	const SampledSceneInterface *ss = runTimeCast<const SampledSceneInterface>( s.get() );
	if( !ss )
	{
		animated = true;
	}
	else
	{
		for( SceneInterface::NameList::iterator it = attributeNames.begin(); it != attributeNames.end(); ++it )
		{
			if( ss->numAttributeSamples( *it ) > 1 )
			{
				animated = true;
				break;
			}
		}
	}
				
	if( animated )
	{
		h.append( context->getFrame() );
	}
}

void SceneReader::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstSceneInterfacePtr s = scene( path );
	if( !s || !s->hasObject() )
	{
		// no object
		h = parent->objectPlug()->defaultValue()->hash();
		return;
	}

	FileSource::hashObject( path, context, parent, h );
	const SampledSceneInterface *ss = runTimeCast<const SampledSceneInterface>( s.get() );
	if( !ss || ss->numObjectSamples() > 1 )
	{
		h.append( context->getFrame() );
	}
}

void SceneReader::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	FileSource::hashChildNames( path, context, parent, h );
	tagsPlug()->hash( h );
}

Imath::Box3f SceneReader::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( path );
	if( !s )
	{
		return Box3f();
	}
	
	Box3d b = s->readBound( context->getFrame() / g_frameRate );
	
	if( b.isEmpty() )
	{
		return Box3f();
	}
	
	return Box3f( b.min, b.max );
}

Imath::M44f SceneReader::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( path );
	if( !s )
	{
		return M44f();
	}
		
	M44d t = s->readTransformAsMatrix( context->getFrame() / g_frameRate );
	
	return M44f(
		t[0][0], t[0][1], t[0][2], t[0][3],
		t[1][0], t[1][1], t[1][2], t[1][3],
		t[2][0], t[2][1], t[2][2], t[2][3],
		t[3][0], t[3][1], t[3][2], t[3][3]
	);
}

IECore::ConstCompoundObjectPtr SceneReader::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( path );
	if( !s )
	{
		return parent->attributesPlug()->defaultValue();
	}
	
	// read attributes
	
	SceneInterface::NameList nameList;
	s->attributeNames( nameList );
	
	CompoundObjectPtr result = new CompoundObject;
	
	for( SceneInterface::NameList::iterator it = nameList.begin(); it != nameList.end(); ++it )
	{
		// these internal attributes should be ignored:
		if( *it == SceneCache::animatedObjectTopologyAttribute )
		{
			continue;
		}
		if( *it == SceneCache::animatedObjectPrimVarsAttribute )
		{
			continue;
		}
		
		// the const cast is ok, because we're only using it to put the object into a CompoundObject that will
		// be treated as forever const after being returned from this function.
		result->members()[ std::string( *it ) ] = constPointerCast<Object>( s->readAttribute( *it, context->getFrame() / g_frameRate ) );
	}

	// read tags and turn them into attributes of the form "user:tag:tagName"
	
	nameList.clear();
	s->readTags( nameList, IECore::SceneInterface::LocalTag );
	for( SceneInterface::NameList::const_iterator it = nameList.begin(); it != nameList.end(); ++it )
	{
		if( it->string().compare( 0, 11, "ObjectType:" ) == 0 )
		{
			continue;
		}
		result->members()["user:tag:"+it->string()] = g_trueBoolData;
	}

	return result;
}

IECore::ConstObjectPtr SceneReader::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( path );
	if( !s || !s->hasObject() )
	{
		return parent->objectPlug()->defaultValue();
	}
	
	return s->readObject( context->getFrame() / g_frameRate );
}

IECore::ConstInternedStringVectorDataPtr SceneReader::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( path );
	if( !s )
	{
		return parent->childNamesPlug()->defaultValue();
	}

	// get the child names
	
	InternedStringVectorDataPtr resultData = new InternedStringVectorData;
	vector<InternedString> &result = resultData->writable();
	s->childNames( result );
	
	// filter out any which don't have the right tags
	
	std::string tagsString = tagsPlug()->getValue();
	if( !tagsString.empty() )
	{
		typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
		Tokenizer tagsTokenizer( tagsString, boost::char_separator<char>( " " ) );
		
		vector<InternedString> tags;
		std::copy( tagsTokenizer.begin(), tagsTokenizer.end(), back_inserter( tags ) );
		
		vector<InternedString>::iterator newResultEnd = result.begin();
		SceneInterface::NameList childTags;
		for( vector<InternedString>::const_iterator cIt = result.begin(), cEIt = result.end(); cIt != cEIt; ++cIt )
		{
			ConstSceneInterfacePtr child = s->child( *cIt );
			childTags.clear();
			child->readTags( childTags, IECore::SceneInterface::EveryTag );
			
			bool childMatches = false;
			for( SceneInterface::NameList::const_iterator tIt = childTags.begin(), tEIt = childTags.end(); tIt != tEIt; ++tIt )
			{
				if( find( tags.begin(), tags.end(), *tIt ) != tags.end() )
				{
					childMatches = true;
					break;
				}
			}
		
			if( childMatches )
			{
				*newResultEnd++ = *cIt;
			}
		}
		
		result.erase( newResultEnd, result.end() );
	}
	
	return resultData;
}

IECore::ConstCompoundObjectPtr SceneReader::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return parent->globalsPlug()->defaultValue();
}

void SceneReader::plugSet( Gaffer::Plug *plug )
{
	// this clears the cache every time the refresh count is updated, so you don't get entries
	// from old files hanging around and screwing up the hierarchy.
	/// \todo The fact that this clears the cache for all nodes, ever is a problem - find a better
	// way of doing this!
	if( plug == refreshCountPlug() )
	{
		SharedSceneInterfaces::clear();
		m_lastScene.clear();
	}
}

ConstSceneInterfacePtr SceneReader::scene( const ScenePath &path ) const
{
	std::string fileName = fileNamePlug()->getValue();
	if( !fileName.size() )
	{
		return NULL;
	}
	
	LastScene &lastScene = m_lastScene.local();
	if( lastScene.fileName == fileName )
	{
		if( lastScene.path == path )
		{
			return lastScene.pathScene;
		}
		else
		{
			lastScene.path = path;
			lastScene.pathScene = lastScene.fileNameScene->scene( path );
			return lastScene.pathScene;
		}
	}

	lastScene.fileName = fileName;
	lastScene.fileNameScene = SharedSceneInterfaces::get( fileName );
	lastScene.path = path;
	lastScene.pathScene = lastScene.fileNameScene->scene( path );
	return lastScene.pathScene;
}
