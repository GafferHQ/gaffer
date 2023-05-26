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

#include "GafferScene/SceneReader.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TransformPlug.h"

#include "IECoreScene/SceneCache.h"
#include "IECoreScene/SharedSceneInterfaces.h"

#include "IECore/InternedString.h"
#include "IECore/StringAlgo.h"

#include "boost/bind/bind.hpp"

#include "fmt/format.h"

using namespace std;
using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

using Tokenizer = boost::tokenizer<boost::char_separator<char> >;

GAFFER_NODE_DEFINE_TYPE( SceneReader );

//////////////////////////////////////////////////////////////////////////
// SceneReader implementation
//////////////////////////////////////////////////////////////////////////

size_t SceneReader::g_firstPlugIndex = 0;

namespace
{

IECore::ConstBoolDataPtr g_trueBoolData = new IECore::BoolData( true );
const InternedString g_lights( "__lights" );
const InternedString g_defaultLights( "defaultLights" );

bool shouldEmulateDefaultLightsSet( const IECoreScene::SceneInterface *scene, const vector<InternedString> &setNames )
{
	// When loading a USD file that wasn't authored by Gaffer, there will be no `defaultLights`
	// set, because USD uses a different mechanism for light linking. In this case, we want to
	// put all the lights in the `defaultLights` set because having everything linked is typically
	// better than having nothing linked. We do that by loading the `__lights` set in its place.
	//
	// When a `defaultLights` set has been authored explicitly, presumably because the file was
	// written from Gaffer, we prefer that to any automatic behaviour. This allows us to round-trip
	// light linking within Gaffer itself.
	return
		!strcmp( scene->typeName(), "USDScene" ) &&
		std::find( setNames.begin(), setNames.end(), g_defaultLights ) == setNames.end() &&
		std::find( setNames.begin(), setNames.end(), g_lights ) != setNames.end()
	;
}

double timeAsDouble( const Context *context )
{
	// The SceneInterface expects time as a `double` in seconds, but Gaffer's
	// primary representation is a `float` frame number. We need to take care
	// with this conversion, particularly with respect to USDScene and USD's own
	// representation for time.
	//
	// USD uses `double` UsdTimeCode values to store time, with an arbitrary
	// mapping between timecode, frames and seconds being specified by the
	// `framesPerSecond` and `timeCodesPerSecond` stage metadata (also
	// `double`). One common setup is to set `timeCodesPerSecond ==
	// framesPerSecond` so that timecodes are equivalent to frame numbers. In
	// this case we should be able to do an exact mapping from Gaffer's frame
	// number to USD's timecode, by converting to seconds here and then multiplying
	// by `timeCodesPerSecond` inside the USDScene implementation. But this is
	// only lossless if we perform the division here at double precision, rather
	// than use `Context::getTime()` which operates only with float precision.
	//
	/// \todo Reconsider Gaffer's time representation. Perhaps we should simply
	/// move to `double` for storing `frame` and `framesPerSecond`?
	return static_cast<double>( context->getFrame() ) / static_cast<double>( context->getFramesPerSecond() );
}

ValuePlug::CachePolicy cachePolicyFromEnv( const char *name )
{
	if( const char *cp = getenv( name ) )
	{
		IECore::msg(
			IECore::Msg::Info, "SceneReader", fmt::format( "{} is set to {}.", name, cp )
		);

		if( !strcmp( cp, "Standard" ) )
		{
			return ValuePlug::CachePolicy::Standard;
		}
		else if( !strcmp( cp, "TaskCollaboration" ) )
		{
			return ValuePlug::CachePolicy::TaskCollaboration;
		}
		else if( !strcmp( cp, "TaskIsolation" ) )
		{
			return ValuePlug::CachePolicy::TaskIsolation;
		}
		else if( !strcmp( cp, "Legacy" ) )
		{
			return ValuePlug::CachePolicy::Legacy;
		}
		else
		{
			IECore::msg(
				IECore::Msg::Warning, "SceneReader",
				fmt::format( "Invalid value \"{}\" for {}. Must be Standard, TaskCollaboration, TaskIsolation or Legacy.", cp, name )
			);
		}
	}

	return ValuePlug::CachePolicy::Legacy;
}

const ValuePlug::CachePolicy g_objectCachePolicy = cachePolicyFromEnv( "GAFFERSCENE_SCENEREADER_OBJECT_CACHEPOLICY" );
const ValuePlug::CachePolicy g_setNamesCachePolicy = cachePolicyFromEnv( "GAFFERSCENE_SCENEREADER_SETNAMES_CACHEPOLICY" );
const ValuePlug::CachePolicy g_setCachePolicy = cachePolicyFromEnv( "GAFFERSCENE_SCENEREADER_SET_CACHEPOLICY" );

} // namespace

SceneReader::SceneReader( const std::string &name )
	:	SceneNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "fileName" ) );
	addChild( new IntPlug( "refreshCount" ) );
	addChild( new StringPlug( "tags" ) );
	addChild( new TransformPlug( "transform" ) );

	outPlug()->childBoundsPlug()->setFlags( Plug::AcceptsDependencyCycles, true );
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

Gaffer::TransformPlug *SceneReader::transformPlug()
{
	return getChild<TransformPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::TransformPlug *SceneReader::transformPlug() const
{
	return getChild<TransformPlug>( g_firstPlugIndex + 3 );
}

void SceneReader::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneNode::affects( input, outputs );

	const bool affectsScene = input == fileNamePlug() || input == refreshCountPlug();

	if(
		affectsScene ||
		input == outPlug()->childBoundsPlug() ||
		transformPlug()->isAncestorOf( input )
	)
	{
		outputs.push_back( outPlug()->boundPlug() );
	}

	if( affectsScene || transformPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->transformPlug() );
	}

	if( affectsScene || input == tagsPlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}

	if( affectsScene || input == outPlug()->setNamesPlug() )
	{
		outputs.push_back( outPlug()->setPlug() );
	}

	if( affectsScene )
	{
		outputs.push_back( outPlug()->attributesPlug() );
		outputs.push_back( outPlug()->objectPlug() );
		outputs.push_back( outPlug()->setNamesPlug() );
	}
}

size_t SceneReader::supportedExtensions( std::vector<std::string> &extensions )
{
	extensions = SceneInterface::supportedExtensions();
	return extensions.size();
}

Gaffer::ValuePlug::CachePolicy SceneReader::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	/// \todo Determine ideal cache policies and change default for when policy isn't
	/// specified by the environment. Consider doing this for other children of `outPlug()` too, but
	/// bear in mind that `CachePolicy::Standard` is not a good idea for `boundPlug()`. Because
	/// `computeBound()` forwards to `parent->childBoundsPlug()->getValue()` and that uses
	/// TaskCollaboration, we want to allow as many threads through as possible.
	if( output == outPlug()->objectPlug() )
	{
		return g_objectCachePolicy;
	}
	else if( output == outPlug()->setPlug() )
	{
		return g_setCachePolicy;
	}
	else if( output == outPlug()->setNamesPlug() )
	{
		return g_setNamesCachePolicy;
	}

	return SceneNode::computeCachePolicy( output );
}

void SceneReader::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashBound( path, context, parent, h );

	int refreshCount = 0;
	ConstSceneInterfacePtr s = scene( path, context, &refreshCount );
	if( !s )
	{
		return;
	}

	h.append( refreshCount );

	if( s->hasBound() )
	{
		s->hash( SceneInterface::BoundHash, timeAsDouble( context ), h );
	}
	else
	{
		// Deliberately not using `childBoundsPlug()->hash()`
		// here because `HierarchyHash` also uniquely identifies the
		// result, and is quicker to compute (at least in all current
		// SceneInterface implementations). In current implementations,
		// `HierarchyHash` is equivalent to hashing `fileName` and `path`
		// but with one big improvement : USDScene and LinkedScene can
		// account for scenegraph instancing and save us from repeating
		// the bounding box computation for _every_ instance. This is
		// a _big_ performance win for complex scenes.
		s->hash( SceneInterface::HierarchyHash, context->getTime(), h );
	}

	if( path.size() == 0 )
	{
		transformPlug()->hash( h );
	}
}

Imath::Box3f SceneReader::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( path, context );
	if( !s )
	{
		return Box3f();
	}

	Box3f result;
	if( s->hasBound() )
	{
		const Box3d b = s->readBound( timeAsDouble( context ) );
		if( b.isEmpty() )
		{
			return Box3f();
		}
		result = Box3f( b.min, b.max );
	}
	else
	{
		result = parent->childBoundsPlug()->getValue();
	}

	if( path.size() == 0 && !result.isEmpty() )
	{
		result = Imath::transform( result, transformPlug()->matrix() );
	}

	return result;
}

void SceneReader::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashTransform( path, context, parent, h );

	int refreshCount = 0;
	ConstSceneInterfacePtr s = scene( path, context, &refreshCount );
	if( !s )
	{
		return;
	}

	h.append( refreshCount );
	s->hash( SceneInterface::TransformHash, timeAsDouble( context ), h );

	if( path.size() == 1 )
	{
		transformPlug()->hash( h );
	}
}

Imath::M44f SceneReader::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( path, context );
	if( !s )
	{
		return M44f();
	}

	const M44d t = s->readTransformAsMatrix( timeAsDouble( context ) );
	M44f result = M44f(
		t[0][0], t[0][1], t[0][2], t[0][3],
		t[1][0], t[1][1], t[1][2], t[1][3],
		t[2][0], t[2][1], t[2][2], t[2][3],
		t[3][0], t[3][1], t[3][2], t[3][3]
	);

	if( path.size() == 1 )
	{
		result = result * transformPlug()->matrix();
	}
	return result;
}

void SceneReader::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	int refreshCount = 0;
	ConstSceneInterfacePtr s = scene( path, context, &refreshCount );
	if( !s )
	{
		h = parent->attributesPlug()->defaultValue()->Object::hash();
		return;
	}

	SceneNode::hashAttributes( path, context, parent, h );

	h.append( refreshCount );
	s->hash( SceneInterface::AttributesHash, timeAsDouble( context ), h );
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

		ConstObjectPtr attribute = s->readAttribute( *it, timeAsDouble( context ) );
		if( attribute )
		{
			// The const cast is ok, because we're only using it to put the object into a CompoundObject that will
			// be treated as forever const after being returned from this function.
			result->members()[ std::string( *it ) ] = boost::const_pointer_cast<Object>( attribute );
		}
		else
		{
			IECore::msg(
				IECore::Msg::Warning, "SceneReader::computeAttributes",
				fmt::format(
					"Failed to load attribute \"{}\" at location \"{}\"",
					it->string(), ScenePlug::pathToString( path )
				)
			);
		}
	}

	return result;
}

void SceneReader::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	int refreshCount = 0;
	ConstSceneInterfacePtr s = scene( path, context, &refreshCount );
	if( !s || !s->hasObject() )
	{
		// no object
		h = parent->objectPlug()->defaultValue()->hash();
		return;
	}

	SceneNode::hashObject( path, context, parent, h );

	h.append( refreshCount );
	s->hash( SceneInterface::ObjectHash, timeAsDouble( context ), h );
}

IECore::ConstObjectPtr SceneReader::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstSceneInterfacePtr s = scene( path, context );
	if( !s || !s->hasObject() )
	{
		return parent->objectPlug()->defaultValue();
	}

	return s->readObject( timeAsDouble( context ), context->canceller() );
}

void SceneReader::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	int refreshCount = 0; string tags;
	ConstSceneInterfacePtr s = scene( path, context, &refreshCount, &tags );
	if( !s )
	{
		h = parent->childNamesPlug()->defaultValue()->Object::hash();
		return;
	}

	SceneNode::hashChildNames( path, context, parent, h );

	h.append( refreshCount );
	h.append( tags );

	s->hash( SceneInterface::ChildNamesHash, timeAsDouble( context ), h );
}

IECore::ConstInternedStringVectorDataPtr SceneReader::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	string tagsString;
	ConstSceneInterfacePtr s = scene( path, context, nullptr, &tagsString );
	if( !s )
	{
		return parent->childNamesPlug()->defaultValue();
	}

	// get the child names

	InternedStringVectorDataPtr resultData = new InternedStringVectorData;
	vector<InternedString> &result = resultData->writable();
	s->childNames( result );

	// filter out any which don't have the right tags

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
			child->readTags( childTags, IECoreScene::SceneInterface::EveryTag );

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
	fileNamePlug()->hash( h );
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
	if( useSetsAPI( s.get() ) )
	{
		result->writable() = s->setNames();
	}
	else
	{
		s->readTags( result->writable(), SceneInterface::LocalTag | SceneInterface::DescendantTag );
	}

	if( shouldEmulateDefaultLightsSet( s.get(), result->readable() ) )
	{
		result->writable().push_back( g_defaultLights );
	}

	return result;
}

void SceneReader::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashSet( setName, context, parent, h );

	ScenePlug::GlobalScope globalScope( context );
	fileNamePlug()->hash( h );
	refreshCountPlug()->hash( h );
	// Technically speaking, we should also call `outPlug()->setNamesPlug()->hash( h )` here,
	// but it doesn't append anything we haven't already appended.
	h.append( setName );
}

static void loadSetWalk( const SceneInterface *s, const InternedString &setName, const Gaffer::Context *context, PathMatcher &set, const vector<InternedString> &path )
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
		Canceller::check( context->canceller() );

		ConstSceneInterfacePtr child = s->child( *it );
		childPath.back() = *it;
		loadSetWalk( child.get(), setName, context, set, childPath );
	}
}

IECore::ConstPathMatcherDataPtr SceneReader::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstInternedStringVectorDataPtr setNamesData = parent->setNames();
	if( find( setNamesData->readable().begin(), setNamesData->readable().end(), setName ) == setNamesData->readable().end() )
	{
		// As documented on `SceneNode::computeSet()`, we may be called with set names
		// that are not present in `out.setNames`, and it is our responsibility to
		// return an empty set in this case. Reading an empty set from a USDScene can
		// be arbitrarily expensive though, because it will traverse the entire stage
		// looking for matching collections. We perform our own check here first, to
		// avoid that expense.
		/// \todo Elsewhere in Gaffer it is the client's responsibility to only use
		/// valid contexts with names that have been advertised (e.g. `scene:path`,
		/// `image:channelName`). Perhaps that would be a better approach here?
		return outPlug()->setPlug()->defaultValue();
	}

	ConstSceneInterfacePtr rootScene = scene( ScenePath(), context );
	if( !rootScene )
	{
		return outPlug()->setPlug()->defaultValue();
	}

	InternedString setNameToRead = setName;
	if( setName == g_defaultLights )
	{
		vector<InternedString> setNames;
		if( useSetsAPI( rootScene.get() ) )
		{
			setNames = rootScene->setNames();
		}
		else
		{
			rootScene->readTags( setNames, SceneInterface::LocalTag | SceneInterface::DescendantTag );
		}
		if( shouldEmulateDefaultLightsSet( rootScene.get(), setNames ) )
		{
			setNameToRead = g_lights;
		}
	}

	if( useSetsAPI( rootScene.get() ) )
	{
		return new PathMatcherData( rootScene->readSet( setNameToRead, /* readDescendantSets = */ true, context->canceller() ) );
	}
	else
	{
		PathMatcherDataPtr result = new PathMatcherData;
		loadSetWalk( rootScene.get(), setNameToRead, context, result->writable(), ScenePath() );
		return result;
	}
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

ConstSceneInterfacePtr SceneReader::scene( const ScenePath &path, const Gaffer::Context *context, int *refreshCount, std::string *tags ) const
{
	ScenePlug::GlobalScope globalScope( context );

	std::string fileName = fileNamePlug()->getValue();
	if( !fileName.size() )
	{
		return nullptr;
	}

	if( refreshCount )
	{
		*refreshCount = refreshCountPlug()->getValue();
	}
	if( tags )
	{
		*tags = tagsPlug()->getValue();
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

bool SceneReader::useSetsAPI( const SceneInterface *scene )
{
	const char *typeName = scene->typeName();
	// We use the tags API for the legacy interfaces listed below, and the sets API
	// for everything else.
	return
		strcmp( typeName, "SceneCache" ) && strcmp( typeName, "MeshCacheSceneInterface" ) &&
		strcmp( typeName, "LinkedScene" ) && strcmp( typeName, "LiveScene" )
	;
}
