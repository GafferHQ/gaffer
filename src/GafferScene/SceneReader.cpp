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

#include "GafferScene/SceneReader.h"
#include "GafferScene/PathMatcherData.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;

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
	addChild( new StringPlug( "sets" ) );
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

Gaffer::StringPlug *SceneReader::setsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *SceneReader::setsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

void SceneReader::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FileSource::affects( input, outputs );

	if( input == tagsPlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}
	else if( input == setsPlug() )
	{
		outputs.push_back( outPlug()->globalsPlug() );
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
		result->members()[ std::string( *it ) ] = boost::const_pointer_cast<Object>( s->readAttribute( *it, context->getFrame() / g_frameRate ) );
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

IECore::ConstObjectPtr SceneReader::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( path );
	if( !s || !s->hasObject() )
	{
		return parent->objectPlug()->defaultValue();
	}

	return s->readObject( context->getFrame() / g_frameRate );
}

void SceneReader::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	FileSource::hashChildNames( path, context, parent, h );
	tagsPlug()->hash( h );
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
	FileSource::hashGlobals( context, parent, h );
	setsPlug()->hash( h );
}

static void loadSetsWalk( const SceneInterface *s, const vector<InternedString> &tags, const vector<PathMatcher *> &sets, const vector<InternedString> &path )
{
	// For each tag we wish to load, we need to determine if it exists at the current
	// location. The natural way to do this would be to call s->hasTag( tag ), but that
	// actually has pretty poor performance when calling hasTag() for many tags. So
	// we load all the local tags with readTags(), and then for each of them test to see
	// if they exist in the list of tags we wish to load. We test the local tags against
	// the tags because we're in control of the tags and can sort them beforehand for faster
	// searching, whereas the localTags just come as-is. Using binary search over linear
	// search isn't actually that big a win for a typical number of tags, simply because
	// InternedString equality tests are so quick, but there's a very slight benefit, which
	// should be more apparent should anyone create a very large number of tags at some point.

	vector<InternedString> sceneTags;
	s->readTags( sceneTags, SceneInterface::LocalTag );

	for( vector<InternedString>::const_iterator it = sceneTags.begin(), eIt = sceneTags.end(); it != eIt; ++it )
	{
		vector<InternedString>::const_iterator t = lower_bound( tags.begin(), tags.end(), *it );
		if( t != tags.end() && *t == *it )
		{
			/// \todo addPath() is doing a search to find the right node to insert at.
			/// If nodes were exposed by the PathMatcher, we could provide the right
			/// node to insert at by tracking it as we recurse the hierarchy.
			sets[t - tags.begin()]->addPath( path );
		}
	}

	// Figure out if we need to recurse by querying descendant tags to see if they include
	// anything we're interested in.

	sceneTags.clear();
	s->readTags( sceneTags, SceneInterface::DescendantTag );

	bool recurse = false;
	for( vector<InternedString>::const_iterator it = sceneTags.begin(), eIt = sceneTags.end(); it != eIt; ++it )
	{
		vector<InternedString>::const_iterator t = lower_bound( tags.begin(), tags.end(), *it );
		if( t != tags.end() && *t == *it )
		{
			recurse = true;
			break;
		}
	}

	if( !recurse )
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
		childPath[path.size()] = *it;
		loadSetsWalk( child.get(), tags, sets, childPath );
	}
}

IECore::ConstCompoundObjectPtr SceneReader::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( ScenePath() );
	if( !s )
	{
		return parent->globalsPlug()->defaultValue();
	}

	CompoundObjectPtr result = new CompoundObject;

	// figure out which tags we want to convert into sets

	vector<InternedString> allTags;
	s->readTags( allTags, SceneInterface::LocalTag | SceneInterface::DescendantTag );

	const std::string setsString = setsPlug()->getValue();
	Tokenizer setsTokenizer( setsString, boost::char_separator<char>( " " ) );

	vector<InternedString> tagsToLoadAsSets;
	for( vector<InternedString>::const_iterator tIt = allTags.begin(), tEIt = allTags.end(); tIt != tEIt; ++tIt )
	{
		for( Tokenizer::const_iterator sIt = setsTokenizer.begin(), sEIt = setsTokenizer.end(); sIt != sEIt; ++sIt )
		{
			if( match( tIt->value(), *sIt ) )
			{
				tagsToLoadAsSets.push_back( *tIt );
			}
		}
	}

	// sort so that we can use lower_bound() in loadSetsWalk().
	sort( tagsToLoadAsSets.begin(), tagsToLoadAsSets.end() );

	// make sets for each of them, and then defer to loadSetsWalk()
	// to do the work.

	IECore::CompoundDataPtr sets = result->member<IECore::CompoundData>(
		"gaffer:sets",
		/* throwExceptions = */ false,
		/* createIfMissing = */ true
	);

	vector<PathMatcher *> pathMatchers;
	for( vector<InternedString>::const_iterator it = tagsToLoadAsSets.begin(), eIt = tagsToLoadAsSets.end(); it != eIt; ++it )
	{
		PathMatcherDataPtr d = sets->member<PathMatcherData>(
			*it,
			/* throwExceptions = */ false,
			/* createIfMissing = */ true
		);
		pathMatchers.push_back( &(d->writable()) );
	}

	loadSetsWalk( s.get(), tagsToLoadAsSets, pathMatchers, vector<InternedString>() );

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
