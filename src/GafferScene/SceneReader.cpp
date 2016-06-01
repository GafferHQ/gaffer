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
#include "Gaffer/StringAlgo.h"
#include "Gaffer/StringPlug.h"

#include "GafferScene/SceneReader.h"
#include "GafferScene/PathMatcherData.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// Removes context variables which are unnecessary when computing
// global aspects of the scene, but which are frequently changed
// to compute per-location aspects of the scene. This makes us
// friendlier to the hash caching mechanism in ValuePlug,
// since it'll see fewer unnecessarily different contexts, and will
// therefore get more cache hits. We use this in our utility
// methods for computing set names, sets and globals.
void removeNonGlobalContextVariables( Context *context )
{
	context->remove( Filter::inputSceneContextName );
	context->remove( ScenePlug::scenePathContextName );
}

} // namespace

typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;

IE_CORE_DEFINERUNTIMETYPED( SceneReader );

//////////////////////////////////////////////////////////////////////////
// SceneReader implementation
//////////////////////////////////////////////////////////////////////////

size_t SceneReader::g_firstPlugIndex = 0;

static IECore::BoolDataPtr g_trueBoolData = new IECore::BoolData( true );

SceneReader::SceneReader( const std::string &name )
	:	SceneNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "fileName" ) );
	addChild( new IntPlug( "refreshCount" ) );
	addChild( new StringPlug( "tags" ) );
	plugSetSignal().connect( boost::bind( &SceneReader::plugSet, this, ::_1 ) );
}

SceneReader::~SceneReader()
{
}

Gaffer::StringPlug *SceneReader::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *SceneReader::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *SceneReader::refreshCountPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *SceneReader::refreshCountPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *SceneReader::tagsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *SceneReader::tagsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

void SceneReader::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneNode::affects( input, outputs );

	if( input == fileNamePlug() || input == refreshCountPlug() )
	{
		outputs.push_back( outPlug()->boundPlug() );
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( outPlug()->attributesPlug() );
		outputs.push_back( outPlug()->objectPlug() );
		outputs.push_back( outPlug()->childNamesPlug() );
		// deliberately not adding globalsPlug(), since we don't
		// load those from file.
		outputs.push_back( outPlug()->setNamesPlug() );
		outputs.push_back( outPlug()->setPlug() );
	}
	else if( input == tagsPlug() )
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
	SceneNode::hashBound( path, context, parent, h );

	hashFileName( context, h );
	refreshCountPlug()->hash( h );

	ConstSceneInterfacePtr s = scene( path, context );
	if( !s )
	{
		return;
	}

	s->hash( SceneInterface::BoundHash, context->getTime(), h );

}

Imath::Box3f SceneReader::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( path, context );
	if( !s )
	{
		return Box3f();
	}

	Box3d b = s->readBound( context->getTime() );

	if( b.isEmpty() )
	{
		return Box3f();
	}

	return Box3f( b.min, b.max );
}

void SceneReader::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashTransform( path, context, parent, h );

	hashFileName( context, h );
	refreshCountPlug()->hash( h );

	ConstSceneInterfacePtr s = scene( path, context );
	if( !s )
	{
		return;
	}

	s->hash( SceneInterface::TransformHash, context->getTime(), h );
}

Imath::M44f SceneReader::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( path, context );
	if( !s )
	{
		return M44f();
	}

	M44d t = s->readTransformAsMatrix( context->getTime() );

	return M44f(
		t[0][0], t[0][1], t[0][2], t[0][3],
		t[1][0], t[1][1], t[1][2], t[1][3],
		t[2][0], t[2][1], t[2][2], t[2][3],
		t[3][0], t[3][1], t[3][2], t[3][3]
	);
}

void SceneReader::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstSceneInterfacePtr s = scene( path, context );
	if( !s )
	{
		h = parent->attributesPlug()->defaultValue()->Object::hash();
		return;
	}

	SceneNode::hashAttributes( path, context, parent, h );

	hashFileName( context, h );
	refreshCountPlug()->hash( h );

	s->hash( SceneInterface::AttributesHash, context->getTime(), h );
}

IECore::ConstCompoundObjectPtr SceneReader::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( path, context );
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
		result->members()[ std::string( *it ) ] = boost::const_pointer_cast<Object>( s->readAttribute( *it, context->getTime() ) );
	}

	return result;
}

void SceneReader::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{

	ConstSceneInterfacePtr s = scene( path, context );
	if( !s || !s->hasObject() )
	{
		// no object
		h = parent->objectPlug()->defaultValue()->hash();
		return;
	}

	SceneNode::hashObject( path, context, parent, h );

	hashFileName( context, h );
	refreshCountPlug()->hash( h );

	s->hash( SceneInterface::ObjectHash, context->getTime(), h );
}

IECore::ConstObjectPtr SceneReader::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( path, context );
	if( !s || !s->hasObject() )
	{
		return parent->objectPlug()->defaultValue();
	}

	return s->readObject( context->getTime() );
}

void SceneReader::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstSceneInterfacePtr s = scene( path, context );
	if( !s )
	{
		h = parent->childNamesPlug()->defaultValue()->Object::hash();
		return;
	}

	SceneNode::hashChildNames( path, context, parent, h );

	hashFileName( context, h );
	refreshCountPlug()->hash( h );

	// append a hash of the tags plug, as restricting the tags can affect the hierarchy
	tagsPlug()->hash( h );

	s->hash( SceneInterface::ChildNamesHash, context->getTime(), h );
}

IECore::ConstInternedStringVectorDataPtr SceneReader::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( path, context );
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

void SceneReader::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = outPlug()->globalsPlug()->defaultValue()->Object::hash();
}

IECore::ConstCompoundObjectPtr SceneReader::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return outPlug()->globalsPlug()->defaultValue();
}

void SceneReader::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashSetNames( context, parent, h );

	hashFileName( context, h );
	refreshCountPlug()->hash( h );
}

IECore::ConstInternedStringVectorDataPtr SceneReader::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( ScenePath(), context );
	if( !s )
	{
		return parent->setNamesPlug()->defaultValue();
	}

	InternedStringVectorDataPtr result = new InternedStringVectorData();
	s->readTags( result->writable(), SceneInterface::LocalTag | SceneInterface::DescendantTag );

	return result;
}

void SceneReader::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashSet( setName, context, parent, h );

	hashFileName( context, h );
	refreshCountPlug()->hash( h );
	h.append( setName );
}

static void loadSetWalk( const SceneInterface *s, const InternedString &setName, PathMatcher &set, const vector<InternedString> &path )
{
	if( s->hasTag( setName, SceneInterface::LocalTag ) )
	{
		set.addPath( path );
	}

	// Figure out if we need to recurse by querying descendant tags to see if they include
	// anything we're interested in.

	if( !s->hasTag( setName, SceneInterface::DescendantTag ) )
	{
		return;
	}

	// Recurse to the children.

	SceneInterface::NameList childNames;
	s->childNames( childNames );
	vector<InternedString> childPath( path );
	childPath.push_back( InternedString() ); // room for the child name
	for( SceneInterface::NameList::const_iterator it = childNames.begin(), eIt = childNames.end(); it != eIt; ++it )
	{
		ConstSceneInterfacePtr child = s->child( *it );
		childPath.back() = *it;
		loadSetWalk( child.get(), setName, set, childPath );
	}
}

GafferScene::ConstPathMatcherDataPtr SceneReader::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	PathMatcherDataPtr result = new PathMatcherData;
	ConstSceneInterfacePtr rootScene = scene( ScenePath(), context );
	if( rootScene )
	{
		loadSetWalk( rootScene.get(), setName, result->writable(), ScenePath() );
	}
	return result;
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

ConstSceneInterfacePtr SceneReader::scene( const ScenePath &path, const Gaffer::Context *context ) const
{
	std::string fileName = fileNameValue( context );

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
			lastScene.pathScene = lastScene.fileNameScene->scene( path );
			lastScene.path = path;
			return lastScene.pathScene;
		}
	}

	lastScene.fileNameScene = SharedSceneInterfaces::get( fileName );
	lastScene.fileName = fileName;

	lastScene.pathScene = lastScene.fileNameScene->scene( path );
	lastScene.path = path;

	return lastScene.pathScene;
}

std::string SceneReader::fileNameValue( const Gaffer::Context *context ) const
{

	ContextPtr tmpContext = new Context( *context, Context::Borrowed );
	removeNonGlobalContextVariables( tmpContext.get() );
	{
		Context::Scope scopedContext( tmpContext.get() );
		return fileNamePlug()->getValue();
	}

}

void SceneReader::hashFileName( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{

	ContextPtr tmpContext = new Context( *context, Context::Borrowed );
	removeNonGlobalContextVariables( tmpContext.get() );
	{
		Context::Scope scopedContext( tmpContext.get() );
		fileNamePlug()->hash( h );
	}

}
