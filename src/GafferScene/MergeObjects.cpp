//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/MergeObjects.h"

#include "GafferScene/Private/ChildNamesMap.h"
#include "GafferScene/SceneAlgo.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "IECore/NullObject.h"

#include "tbb/blocked_range.h"
#include "tbb/parallel_reduce.h"
#include "tbb/spin_mutex.h"

#include "fmt/format.h"

#include <unordered_map>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// InternedString compares by pointer address by default, which will give differing
// results betweeen processes. Comparing by string value gives an alphabetical ordering
// we can rely on.
bool internedStringValueLess( const InternedString &a, const InternedString &b )
{
	return a.string() < b.string();
}

void validateDestination( const ScenePlug::ScenePath &destination, const ScenePlug::ScenePath &source )
{
	if( !destination.size() )
	{
		// If we were to allow this, what would it mean? Would a destination of / just discard the mesh?
		// Exception seems a lot clearer.
		throw IECore::Exception(
			fmt::format(
				"Empty destination not allowed for source location '{}'.",
				ScenePlug::pathToString( source )
			)
		);
	}

	for( auto &n : destination )
	{
		try
		{
			SceneAlgo::validateName( n );
		}
		catch( const std::exception &e )
		{
			throw IECore::Exception(
				fmt::format(
					"Invalid destination `{}` for source location '{}'. {}",
					ScenePlug::pathToString( destination ),
					ScenePlug::pathToString( source ),
					e.what()
				)
			);
		}
	}
}

using SourcePaths = std::vector<ScenePlug::ScenePath>;

//////////////////////////////////////////////////////////////////////////
// TreeData
//////////////////////////////////////////////////////////////////////////

// In order to collect all the locations that are specified as destinations,
// we need to visit all input locations, and construct a tree that holds all
// the destinations.

class TreeData : public IECore::Data
{

	public :

		struct Location
		{
			using Ptr = std::unique_ptr<Location>;

			// A location stores two things:

			// A map of child locations.
			std::unordered_map< IECore::InternedString, Ptr > children;

			// A map of child destinations.
			// We store these separately because name resolution is handled separately for these two:
			// an intermediate location may share a name with an original location that hasn't been
			// filtered, but a destination requires a new name in this case.
			std::unordered_map< InternedString, SourcePaths > destinations;
		};

		TreeData( const ScenePlug *inPlug, const FilterPlug *filterPlug, const StringPlug *destinationPlug )
			:	m_root( new Location() )
		{
			auto f = [this, destinationPlug]( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &sourcePath )
			{
				if( sourcePath.size() )
				{
					addDestination( destinationPlug, sourcePath );
				}
				return true;
			};
			SceneAlgo::filteredParallelTraverse( inPlug, filterPlug, f );
		}

		static bool affectedBy( const ScenePlug *inPlug, const FilterPlug *filterPlug, const StringPlug *destinationPlug, const Plug *input )
		{
			return
				input == filterPlug ||
				input == inPlug->childNamesPlug() ||
				input == destinationPlug
			;
		}

		static void hash(
			const ScenePlug *inPlug, const FilterPlug *filterPlug, const StringPlug *destinationPlug,
			IECore::MurmurHash &h
		)
		{
			// See `SceneAlgo::matchingPathsHash()` for documentation of this hashing strategy.
			std::atomic<uint64_t> h1( 0 ), h2( 0 );
			auto f = [destinationPlug, &h1, &h2]( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &sourcePath )
			{
				IECore::MurmurHash h;
				hashDestination( destinationPlug, sourcePath, h );
				h1 += h.h1();
				h2 += h.h2();
				return true;
			};
			SceneAlgo::filteredParallelTraverse( inPlug, filterPlug, f );
			h.append( MurmurHash( h1, h2 ) );
		}

		const Location *location( const ScenePlug::ScenePath &path ) const
		{
			const Location *result = m_root.get();
			for( const auto &name : path )
			{
				const auto it = result->children.find( name );
				if( it != result->children.end() )
				{
					result = it->second.get();
				}
				else
				{
					return nullptr;
				}
			}
			return result;
		}

	private :

		static void hashDestination( const StringPlug *destinationPlug, const ScenePlug::ScenePath &sourcePath, IECore::MurmurHash &h )
		{
			h.append( sourcePath.data(), sourcePath.size() );
			h.append( (uint64_t)sourcePath.size() );

			destinationPlug->hash( h );
		}

		void addDestination( const StringPlug *destinationPlug, const ScenePlug::ScenePath &sourcePath )
		{
			const ScenePlug::ScenePath destination = ScenePlug::stringToPath( destinationPlug->getValue() );
			validateDestination( destination, sourcePath );

			tbb::spin_mutex::scoped_lock lock( m_mutex );

			Location *location = m_root.get();
			for( unsigned int i = 0; i < destination.size() - 1; i++ )
			{
				const auto &name = destination[i];
				const auto inserted = location->children.try_emplace( name );
				if( inserted.second )
				{
					inserted.first->second = std::make_unique<Location>();
				}

				location = inserted.first->second.get();
			}

			auto insertResult = location->destinations.try_emplace( destination.back() );
			insertResult.first->second.push_back( sourcePath );
		}

		tbb::spin_mutex m_mutex;
		Location::Ptr m_root;

};

IE_CORE_DECLAREPTR( TreeData )

class MergeLocationData : public IECore::Data
{

	public :
		MergeLocationData( const TreeData::Location *location, const ScenePlug::ScenePath &path, const MergeObjects *mergeObjects, const Context *context, const int rootFilterValue )
		{
			std::unordered_set< IECore::InternedString > availableDestinations;

			bool hasDestinations = location && location->destinations.size();
			m_hasDescendantDestinations = ( location && location->children.size() ) || hasDestinations;

			InternedStringVectorDataPtr childNamesData;

			if( mergeObjects->inPlug()->existsPlug()->getValue() )
			{
				// If there is a source location for this path, conceptually, we want to take the source
				// child names, remove any that have been filtered out, and then move to the next branch
				// where they may be added back while adding paths used by destinations. If we actually
				// removed names that were subsequently added back, however, we change the order of the
				// names in a way that might not match a user's expectations ( especially if the
				// destination is ${scene:path}, so no change in the hierarchy is expected.
				//
				// To get around this, we check if a child name is used by any destination, and if it is,
				// we don't remove it, and instead insert it in availableDestinations so we no we can use
				// this name despite it not having actually been removed.
				ConstInternedStringVectorDataPtr inChildNamesData = mergeObjects->inPlug()->childNamesPlug()->getValue();
				const std::vector< InternedString > &inChildNames = inChildNamesData->readable();

				std::vector<int> prune;
				if( rootFilterValue & IECore::PathMatcher::EveryMatch )
				{

					FilterPlug::SceneScope sceneScope( context, mergeObjects->inPlug() );
					ScenePlug::ScenePath childPath = path;
					childPath.push_back( InternedString() ); // for the child name
					for( unsigned int i = 0; i < inChildNames.size(); i++ )
					{
						childPath[path.size()] = inChildNames[i];
						sceneScope.set( ScenePlug::scenePathContextName, &childPath );

						// NOTE : We include ancestor matches here so that if a parent location is filtered,
						// and this location is not filtered, it will always be discarded.
						// The corner case this covers is if you filter to a group, removing all of that
						// groups children, but then use that group as the destination - it is fairly
						// ambiguous what should happen to the group's children in this case ( do they
						// come back because the parent group is no longer Pruned because it is used as a
						// destination? ). I've made the call that it's more consistent if the principle is
						// "Children of filtered locations that aren't themselves filtered are always
						// discarded ( whether or not their parent are used as part of a destination )".
						// This also matches a natural way of handling sets.
						if( mergeObjects->filterPlug()->getValue() &
							( IECore::PathMatcher::ExactMatch | IECore::PathMatcher::AncestorMatch )
						)
						{
							// Check if this name is used by any destination
							if( !( location && (
								location->children.find( inChildNames[i] ) != location->children.end() ||
								location->destinations.find( inChildNames[i] ) != location->destinations.end()
							) ) )
							{
								// Not used, we can prune it
								if( !prune.size() )
								{
									prune.resize( inChildNames.size() );
								}
								prune[i] = true;
							}
							else
							{
								// Is used, so we don't actually remove it, but we do record that it is available
								if( hasDestinations )
								{
									availableDestinations.insert( inChildNames[i] );
								}
							}
						}
					}
				}


				if( prune.size() )
				{
					childNamesData = new InternedStringVectorData();
					std::vector< IECore::InternedString > &childNames = childNamesData->writable();
					for( unsigned int i = 0; i < inChildNames.size(); i++ )
					{
						if( !prune[i] )
						{
							childNames.push_back( inChildNames[i] );
						}
					}
				}
				else
				{
					// This should be a copy-on-write, and we shouldn't call writable on this unless their
					// is actually a new child name, so this often shouldn't actually allocate.
					childNamesData = inChildNamesData->copy();
				}
			}
			else
			{
				childNamesData = new InternedStringVectorData();
			}

			std::unordered_set< IECore::InternedString > usedNames;
			for( const IECore::InternedString &i : childNamesData->readable() )
			{
				usedNames.insert( i );
			}

			// Intermediate locations can be shared with the existing child names - all that happens
			// here is that new parent locations are added if necessary to support the destination locations.
			if( location && location->children.size() )
			{
				InternedStringVectorDataPtr newChildNamesData = new InternedStringVectorData();
				std::vector< IECore::InternedString > &newChildNames = newChildNamesData->writable();
				newChildNames.reserve( location->children.size() );
				for( const auto &i : location->children )
				{
					if( usedNames.find( i.first ) == usedNames.end() )
					{
						newChildNames.push_back( i.first );
						usedNames.insert( i.first );
						if( hasDestinations )
						{
							availableDestinations.insert( i.first );
						}
					}
				}

				if( newChildNames.size() )
				{
					std::sort( newChildNames.begin(), newChildNames.end(), internedStringValueLess );

					std::vector< IECore::InternedString > &childNames = childNamesData->writable();
					if( childNames.size() == 0 )
					{
						childNames.swap( newChildNames );
					}
					else
					{
						for( const InternedString &i : newChildNames )
						{
							childNames.push_back( i );
						}
					}
				}
			}

			// Destinatios aren't allowed to share names with the existing child names, unless they are
			// "available". "available" means either that they would have been removed, but were kept
			// because we noticed ahead of time that they are destinations, or that they were created
			// to support an intermediate location.
			if( hasDestinations )
			{
				std::vector< IECore::InternedString > &childNames = childNamesData->writable();

				std::vector< IECore::InternedString > destinationNames;
				destinationNames.reserve( location->destinations.size() );

				for( const auto &i : location->destinations )
				{
					if( availableDestinations.count( i.first ) )
					{
						// I don't like copying all this memory from the Location when we could
						// theoretically share it with the Location, but we need to sort it, so
						// if we were going to share it, we would need a mutex to control the sort,
						// and the cost of copying it is worst case <1% of a trivial MergeObjects
						// implementation, so just copying is the simple solution.
						m_destinations[ i.first ] = i.second;
					}
					else
					{
						// We have a new name - we can't set up an entry in destination map yet,
						// we need to sort and uniquify the names first.
						destinationNames.push_back( i.first );
					}
				}

				// It's important to sort the new destination names before we uniquify them, because
				// they were collected in parallel, and the order could be non-deterministic.
				std::sort( destinationNames.begin(), destinationNames.end(), internedStringValueLess );

				// Add the new names to the destinations map, uniquifying as necessary
				for( const InternedString &i : destinationNames )
				{
					const InternedString unique = GafferScene::Private::ChildNamesMap::uniqueName( i, usedNames );
					usedNames.insert( unique );
					childNames.push_back( unique );

					m_destinations[unique] = location->destinations.at(i);
				}

				// Sort the sources for each destination
				for( auto &i : m_destinations )
				{
					std::sort(
						i.second.begin(), i.second.end(),
						[] ( const ScenePlug::ScenePath &a, const ScenePlug::ScenePath &b ) {
							return lexicographical_compare(
								a.begin(), a.end(), b.begin(), b.end(),
								internedStringValueLess
							);
						}
					);
				}
			}

			m_childNamesData = childNamesData;
		}

		static void hash( const IECore::MurmurHash &treeHash, const ScenePlug::ScenePath &path, const MergeObjects *mergeObjects, const Context *context, const int rootFilterValue, IECore::MurmurHash &h )
		{
			if( mergeObjects->inPlug()->existsPlug()->getValue() )
			{
				mergeObjects->inPlug()->childNamesPlug()->hash( h );

				if( rootFilterValue )
				{
					ConstInternedStringVectorDataPtr inChildNamesData =
						mergeObjects->inPlug()->childNamesPlug()->getValue();
					const std::vector< InternedString > &inChildNames = inChildNamesData->readable();

					FilterPlug::SceneScope sceneScope( context, mergeObjects->inPlug() );

					ScenePlug::ScenePath childPath = path;
					childPath.push_back( InternedString() ); // for the child name
					for( unsigned int i = 0; i < inChildNames.size(); i++ )
					{
						childPath[path.size()] = inChildNames[i];
						sceneScope.set( ScenePlug::scenePathContextName, &childPath );
						mergeObjects->filterPlug()->hash( h );
					}
				}
			}

			h.append( treeHash );
			h.append( path );
		}

		ConstInternedStringVectorDataPtr m_childNamesData;
		std::unordered_map< InternedString, SourcePaths > m_destinations;

		// It feels slightly weird to store this here - it's not really related to this class's main
		// purpose of storing the child names and destinations present at this location. But we need
		// to compute this as part the initialization, and we need to access this per-location during
		// bounds computation, so it makes sense to store it here, rather than adding a separate plug
		// and recomputing it.
		bool m_hasDescendantDestinations;

};

IE_CORE_DECLAREPTR( MergeLocationData )

/// Calls `treePlug()->getValue()` in a clean context and
/// returns the result. This must be used for all access to
/// `treePlug()`.
ConstTreeDataPtr tree( const ObjectPlug *treePlug, const Gaffer::Context *context )
{
	ScenePlug::GlobalScope globalScope( context );
	return static_pointer_cast<const TreeData>( treePlug->getValue() );
}

void treeHash( const ObjectPlug *treePlug, const Gaffer::Context *context, IECore::MurmurHash &h )
{
	ScenePlug::GlobalScope globalScope( context );
	treePlug->hash( h );
}

// Returns a pointer to a vector of source paths if path is a destination, otherwise nullptr.
// parentHolder is used to ensure the memory isn't freed - the return value will be valid
// as long as it is held.
const std::vector<ScenePlug::ScenePath> *findSources(
	const ObjectPlug* mergeLocationPlug,
	const ScenePlug::ScenePath &path, const Gaffer::Context *context, ConstObjectPtr &parentHolder
)
{
	if( !path.size() )
	{
		return nullptr;
	}
	const ScenePlug::ScenePath parentPath( path.begin(), path.begin() + path.size() - 1 );
	ScenePlug::PathScope pathScope( context, &parentPath );
	parentHolder = mergeLocationPlug->getValue();
	const MergeLocationData* mergeLocation = IECore::runTimeCast<const MergeLocationData>( parentHolder.get() );
	if( !mergeLocation )
	{
		return nullptr;
	}

	auto it = mergeLocation->m_destinations.find( path.back() );
	if( it != mergeLocation->m_destinations.end() )
	{
		return &it->second;
	}

	return nullptr;
}

bool isConnected( const Gaffer::Plug *plug )
{
	// \todo - what is the appropriate criteria for "is something connected", when there is a difference
	// in behaviour that is visible to users?
	return plug->source()->direction() == Plug::Out;
}

// Given a source and destination path, within source and destination scenes, find a
// matrix mapping from source to destination. matchingPrefix and toDest are cache values -
// if we are still operating on the same destination, and matchingPrefix matches the length
// of the prefix of the two paths that currently matches, then we can reuse the toDest matrix.
M44f relativeTransform(
	const ScenePlug::ScenePath &sourcePath, const ScenePlug::ScenePath &destPath,
	const ScenePlug *sourceScene, const ScenePlug *destScene,
	ScenePlug::PathScope &pathScope, ScenePlug::ScenePath &matchingPrefix, M44f &toDest
)
{
	unsigned int matchingLength = std::min( sourcePath.size(), destPath.size() );
	if( sourceScene != destScene )
	{
		// In theory, we could do something more accurate even when the scenes are different, but
		// we couldn't skip evaluating the transforms in the prefix just because the names match.
		// We would need a separate code path where we evaluate the transforms at each level, but
		// don't multiply them onto the matrices if they are identical ( to avoid accumulating error ).
		// For now, do the simple thing, because preserving existing transforms is most important when
		// working in place.
		matchingLength = 0;
	}
	else
	{
		for( unsigned int i = 0; i < matchingLength; i++ )
		{
			if( sourcePath[ i ] != destPath[ i ] )
			{
				matchingLength = i;
				break;
			}
		}
	}

	if( matchingPrefix.size() != matchingLength || toDest == M44f( 0.0f ) )
	{
		ScenePlug::ScenePath &curPath = matchingPrefix;

		if( curPath.size() > matchingLength )
		{
			curPath.resize( matchingLength );
		}

		curPath.reserve( destPath.size() );
		while( curPath.size() < destPath.size() )
		{
			curPath.push_back( destPath[ curPath.size() ] );
		}

		toDest = M44f();
		while( curPath.size() > matchingLength )
		{
			pathScope.setPath( &curPath );
			if( destScene->existsPlug()->getValue() )
			{
				toDest = toDest * destScene->transformPlug()->getValue();
			}
			curPath.pop_back();
		}

		toDest.invert();
	}

	ScenePlug::ScenePath &curPath = matchingPrefix;

	curPath.reserve( sourcePath.size() );
	while( curPath.size() < sourcePath.size() )
	{
		curPath.push_back( sourcePath[ curPath.size() ] );
	}

	M44f fromSource;
	while( curPath.size() > matchingLength )
	{
		pathScope.setPath( &curPath );
		fromSource = fromSource * sourceScene->transformPlug()->getValue();
		curPath.pop_back();
	}

	return fromSource * toDest;
}

// The filter value used for pruning the existing scene - if the sourcePlug is connected, then no pruning occurs.
IECore::PathMatcher::Result pruneFilterValue( const GafferScene::ScenePlug *inPlug, const GafferScene::FilterPlug *filterPlug, const GafferScene::ScenePlug *sourcePlug, const Gaffer::Context *context )
{
	if( isConnected( sourcePlug ) )
	{
		return IECore::PathMatcher::NoMatch;
	}

	FilterPlug::SceneScope sceneScope( context, inPlug );
	return (IECore::PathMatcher::Result)filterPlug->getValue();
}

} // namespace


//////////////////////////////////////////////////////////////////////////
// MergeObjects
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( MergeObjects );

size_t MergeObjects::g_firstPlugIndex = 0;

MergeObjects::MergeObjects( const std::string &name, const std::string &defaultDestination  )
	:	FilteredSceneProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "source" ) );

	addChild( new StringPlug( "destination", Gaffer::Plug::In, defaultDestination ) );

	addChild( new ObjectPlug( "__tree", Gaffer::Plug::Out, IECore::NullObject::defaultNullObject() ) );
	addChild( new ObjectPlug( "__mergeLocation", Gaffer::Plug::Out, IECore::NullObject::defaultNullObject() ) );
	addChild( new ObjectPlug( "__processedObject", Plug::Out, NullObject::defaultNullObject() ) );

	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
	outPlug()->childBoundsPlug()->setFlags( Plug::AcceptsDependencyCycles, true );
}

MergeObjects::~MergeObjects()
{
}

GafferScene::ScenePlug *MergeObjects::sourcePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 0 );
}

const GafferScene::ScenePlug *MergeObjects::sourcePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 0 );
}

Gaffer::StringPlug *MergeObjects::destinationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *MergeObjects::destinationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::ObjectPlug *MergeObjects::treePlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ObjectPlug *MergeObjects::treePlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 2 );
}

Gaffer::ObjectPlug *MergeObjects::mergeLocationPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::ObjectPlug *MergeObjects::mergeLocationPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 3 );
}

Gaffer::ObjectPlug *MergeObjects::processedObjectPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::ObjectPlug *MergeObjects::processedObjectPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

const GafferScene::ScenePlug *MergeObjects::effectiveSourcePlug() const
{
	return isConnected( sourcePlug() ) ? sourcePlug() : inPlug();
}

void MergeObjects::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if(
		TreeData::affectedBy( inPlug(), filterPlug(), destinationPlug(), input ) ||
		TreeData::affectedBy( sourcePlug(), filterPlug(), destinationPlug(), input )
	)
	{
		outputs.push_back( treePlug() );
	}

	if(
		input == inPlug()->childNamesPlug() ||
		input == sourcePlug()->childNamesPlug() ||
		input == treePlug()
	)
	{
		outputs.push_back( mergeLocationPlug() );
	}

	if(
		input == mergeLocationPlug() ||
		input == inPlug()->boundPlug() ||
		input == sourcePlug()->boundPlug()
	)
	{
		outputs.push_back( outPlug()->boundPlug() );
	}

	if(
		input == mergeLocationPlug() ||
		input == inPlug()->transformPlug()
	)
	{
		outputs.push_back( outPlug()->transformPlug() );
	}

	if(
		input == mergeLocationPlug() ||
		input == inPlug()->attributesPlug()
	)
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}

	if(
		input == mergeLocationPlug() ||
		input == inPlug()->objectPlug() ||
		input == inPlug()->transformPlug() ||
		input == sourcePlug()->objectPlug() ||
		input == sourcePlug()->transformPlug()
	)
	{
		outputs.push_back( processedObjectPlug() );
	}

	if(
		input == mergeLocationPlug() ||
		input == inPlug()->objectPlug() ||
		input == processedObjectPlug()
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}

	if(
		input == mergeLocationPlug() ||
		input == inPlug()->childNamesPlug()
	)
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}

	if(
		input == treePlug() ||
		input == inPlug()->setPlug() ||
		input == filterPlug()
	)
	{
		outputs.push_back( outPlug()->setPlug() );
	}
}

void MergeObjects::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hash( output, context, h );

	if( output == treePlug() )
	{
		TreeData::hash( effectiveSourcePlug(), filterPlug(), destinationPlug(), h );
	}
	else if( output == mergeLocationPlug() )
	{
		// Do a full evalution of the tree data.
		// This is pretty expensive to trigger when someone could just be hashing childNames, and doesn't
		// require a full evaluation, but doing this now allows us to do an early out and avoid putting
		// entries in the value cache for locations that aren't being modified, and that's a noticeable
		// win for the common case where we are going to evaluate everything anyway.
		ConstTreeDataPtr treeData = tree( treePlug(), context );
		const ScenePlug::ScenePath &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
		const TreeData::Location* loc = treeData->location( path );

		int filterValue = pruneFilterValue( inPlug(), filterPlug(), sourcePlug(), context );

		ObjectPtr result;
		// We only need to compute merge data for this location if the filter matches, or the destination
		// tree overlaps it.
		if( !( loc || ( filterValue & IECore::PathMatcher::EveryMatch ) ) )
		{
			h.append( 0 );
			return;
		}

		// It's a bit sloppy to recompute the hash here when it was already computed in the call to tree()
		// above, but it should be hitting the hash cache.
		IECore::MurmurHash treeH;
		treeHash( treePlug(), context, treeH );

		MergeLocationData::hash( treeH, path, this, context, filterValue, h );
	}
	else if( output == processedObjectPlug() )
	{
		const ScenePlug::ScenePath &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
		ConstObjectPtr parentHolder;
		const SourcePaths *sourcePaths = findSources( mergeLocationPlug(), path, context, parentHolder );

		if( !sourcePaths )
		{
			throw IECore::Exception( "__processedObject should only be hashed from hashObject, which checks for a matching tree location first" );
		}

		h.append( outPlug()->fullTransformHash( path ) );

		const ScenePlug *effectiveSource = effectiveSourcePlug();

		const ThreadState &threadState = ThreadState::current();
		tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

		const IECore::MurmurHash reduction = tbb::parallel_deterministic_reduce(
			tbb::blocked_range<size_t>( 0, sourcePaths->size() ),
			IECore::MurmurHash(),
			[&] ( const tbb::blocked_range<size_t> &range, const MurmurHash &hash ) {

				ScenePlug::PathScope pathScope( threadState );
				IECore::MurmurHash result = hash;
				for( size_t i = range.begin(); i != range.end(); ++i )
				{
					pathScope.setPath( &((*sourcePaths)[i]) );
					result.append( effectiveSource->fullTransformHash( (*sourcePaths)[i] ) );
					effectiveSource->objectPlug()->hash( result );
				}
				return result;

			},
			[] ( const MurmurHash &x, const MurmurHash &y ) {

				MurmurHash result = x;
				result.append( y );
				return result;
			},
			tbb::simple_partitioner(),
			taskGroupContext
		);

		h.append( reduction );
	}
}

void MergeObjects::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == treePlug() )
	{
		static_cast<Gaffer::ObjectPlug *>( output )->setValue( new TreeData(
			effectiveSourcePlug(), filterPlug(), destinationPlug()
		) );
	}
	else if( output == mergeLocationPlug() )
	{
		ConstTreeDataPtr treeData = tree( treePlug(), context );
		const ScenePlug::ScenePath &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
		const TreeData::Location* loc = treeData->location( path );

		int filterValue = pruneFilterValue( inPlug(), filterPlug(), sourcePlug(), context );

		ObjectPtr result;
		// We only need to compute merge data for this location if the filter matches, or the destination
		// tree overlaps it.
		if( loc || ( filterValue & IECore::PathMatcher::EveryMatch ) )
		{
			result = new MergeLocationData( loc, path, this, context, filterValue );
		}
		else
		{
			result = IECore::NullObject::defaultNullObject();
		}
		static_cast<Gaffer::ObjectPlug *>( output )->setValue( result );
	}
	else if( output == processedObjectPlug() )
	{
		const ScenePlug::ScenePath &path = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
		ConstObjectPtr parentHolder;
		const SourcePaths *sourcePaths = findSources( mergeLocationPlug(), path, context, parentHolder );

		if( !sourcePaths )
		{
			throw IECore::Exception( "__processedObject should only be evaluated from computeObject, which checks for a matching tree location first" );
		}

		// Prepare a vector of pairs of objects and transforms, to be merged.
		std::vector< std::pair< IECore::ConstObjectPtr, Imath::M44f > > sources( sourcePaths->size() );

		const ScenePlug *effectiveSource = effectiveSourcePlug();

		const ThreadState &threadState = ThreadState::current();
		tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

		tbb::parallel_for(
			tbb::blocked_range<size_t>( 0, sourcePaths->size() ),
			[&] ( const tbb::blocked_range<size_t> &range ) {

				ScenePlug::ScenePath matchingPrefix;
				M44f toDest( 0.0f );

				ScenePlug::PathScope pathScope( threadState );
				for( size_t i = range.begin(); i != range.end(); ++i )
				{
					pathScope.setPath( &((*sourcePaths)[i]) );
					sources[i].first = effectiveSource->objectPlug()->getValue();
					sources[i].second = relativeTransform(
						(*sourcePaths)[i], path, effectiveSource, inPlug(), pathScope,
						matchingPrefix, toDest
					);
				}

			},
			tbb::auto_partitioner(),
			taskGroupContext
		);

		static_cast<Gaffer::ObjectPlug *>( output )->setValue( mergeObjects( sources, context ) );
	}
	else
	{
		FilteredSceneProcessor::compute( output, context );
	}
}

void MergeObjects::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstObjectPtr parentHolder;
	const SourcePaths *sourcePaths = findSources( mergeLocationPlug(), path, context, parentHolder );

	ConstMergeLocationDataPtr mergeLocationData = IECore::runTimeCast< const MergeLocationData >( mergeLocationPlug()->getValue() );
	bool hasDescendantDestinations = mergeLocationData && mergeLocationData->m_hasDescendantDestinations;
	bool inputExists = inPlug()->existsPlug()->getValue();
	bool hasDescendantPruned = false;
	if( inputExists &&
		( pruneFilterValue( inPlug(), filterPlug(), sourcePlug(), context ) & IECore::PathMatcher::DescendantMatch )
	)
	{
		if( inPlug()->childNamesPlug()->getValue()->readable().size() )
		{
			hasDescendantPruned = true;
		}
	}

	bool needsOriginalBoundMerge = false;
	IECore::MurmurHash childBoundHash;
	if( sourcePaths && !( mergeLocationData && mergeLocationData->m_childNamesData->readable().size() ) )
	{
	}
	else if( hasDescendantPruned )
	{
		childBoundHash = outPlug()->childBoundsPlug()->hash();
	}
	else if( hasDescendantDestinations )
	{
		childBoundHash = outPlug()->childBoundsPlug()->hash();

		if( inputExists && !sourcePaths )
		{
			needsOriginalBoundMerge = true;
		}
	}
	else
	{
		// If this location is neither a destination itself, or the parent of a destination, then
		// it must exists in the input.
		assert( inputExists );

		// Since we're not adding or removing anything, we can just pass through the input.
		childBoundHash = inPlug()->boundPlug()->hash();
	}

	if( !( sourcePaths || needsOriginalBoundMerge ) )
	{
		h = childBoundHash;
		return;
	}

	FilteredSceneProcessor::hashBound( path, context, parent, h );

	h.append( childBoundHash );
	if( needsOriginalBoundMerge )
	{
		inPlug()->boundPlug()->hash( h );
	}

	if( !sourcePaths )
	{
		return;
	}

	h.append( outPlug()->fullTransformHash( path ) );

	const ThreadState &threadState = ThreadState::current();
	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

	const ScenePlug *effectiveSource = effectiveSourcePlug();

	const IECore::MurmurHash reduction = tbb::parallel_deterministic_reduce(
		tbb::blocked_range<size_t>( 0, sourcePaths->size() ),
		IECore::MurmurHash(),
		[&] ( const tbb::blocked_range<size_t> &range, const MurmurHash &hash ) {

			ScenePlug::PathScope pathScope( threadState );
			IECore::MurmurHash result = hash;
			for( size_t i = range.begin(); i != range.end(); ++i )
			{
				pathScope.setPath( &((*sourcePaths)[i]) );
				effectiveSource->boundPlug()->hash( result );
				result.append( effectiveSource->fullTransformHash( (*sourcePaths)[i] ) );
			}
			return result;

		},
		[] ( const MurmurHash &x, const MurmurHash &y ) {

			MurmurHash result = x;
			result.append( y );
			return result;
		},
		tbb::simple_partitioner(),
		taskGroupContext
	);

	h.append( reduction );
}

Imath::Box3f MergeObjects::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstObjectPtr parentHolder;
	const SourcePaths *sourcePaths = findSources( mergeLocationPlug(), path, context, parentHolder );

	// Find the bound from children of this location, either in the existing scene, or added
	// by merges targetting child locations as destinations.

	// To know if we need to check the child bounds, we need to know if there are any destinations below this
	// location. We can efficiently query this from the mergeLocationData.
	ConstMergeLocationDataPtr mergeLocationData = IECore::runTimeCast< const MergeLocationData >( mergeLocationPlug()->getValue() );

	bool hasDescendantDestinations = mergeLocationData && mergeLocationData->m_hasDescendantDestinations;

	bool inputExists = inPlug()->existsPlug()->getValue();
	bool hasDescendantPruned = false;
	// If some of the locations in the original scene are getting pruned below this location, then we should
	// adjust the bounds.
	if( inputExists &&
		( pruneFilterValue( inPlug(), filterPlug(), sourcePlug(), context ) & IECore::PathMatcher::DescendantMatch )
	)
	{
		if( inPlug()->childNamesPlug()->getValue()->readable().size() )
		{
			hasDescendantPruned = true;
		}
	}

	bool needsOriginalBoundMerge = false;
	Box3f childBound;
	if( sourcePaths && !( mergeLocationData && mergeLocationData->m_childNamesData->readable().size() ) )
	{
		// There are no children, and we're generating a new object here - we can ignore any bound
		// except the new one we're going to compute.
	}
	else if( hasDescendantPruned )
	{
		// NOTE: This is potentially incorrect if there is an object at this location, but there is
		// currently no good way to fix this, and Prune has the same failure when adjustBounds is
		// used, so this is at least consistent.
		childBound = outPlug()->childBoundsPlug()->getValue();
	}
	else if( hasDescendantDestinations )
	{
		childBound = outPlug()->childBoundsPlug()->getValue();

		if( inputExists && !sourcePaths )
		{
			// This will likely do nothing - the children are not pruned, so the child bound should be
			// a superset of the input bound. The corner case handled here is if this location is a
			// parent that also has an object at it, in which case the childBounds fail to capture the
			// bound of the object at this location. We could reason that it's OK to fail in this case,
			// the same as we do in the hasDescendantPruned case above, but currently it's only pruning
			// operations that fail in this way, so for consistencay, we should probably get this right.
			needsOriginalBoundMerge = true;
		}
	}
	else
	{
		// If this location is neither a destination itself, or the parent of a destination, then
		// it must exists in the input.
		assert( inputExists );

		// Since we're not adding or removing anything, we can just pass through the input.
		childBound = inPlug()->boundPlug()->getValue();
	}

	if( needsOriginalBoundMerge )
	{
		childBound.extendBy( inPlug()->boundPlug()->getValue() );
	}

	if( !sourcePaths )
	{
		return childBound;
	}

	const ThreadState &threadState = ThreadState::current();
	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

	const ScenePlug *effectiveSource = effectiveSourcePlug();

	// This location is an actual destination, so accumulate bounds from everything being merged here.

	return tbb::parallel_reduce(
		tbb::blocked_range<size_t>( 0, sourcePaths->size() ),
		childBound,
		[&] ( const tbb::blocked_range<size_t> &range, const Box3f &bound ) {

			ScenePlug::PathScope pathScope( threadState );
			Box3f result = bound;

			ScenePlug::ScenePath matchingPrefix;
			M44f toDest( 0.0f );

			for( size_t i = range.begin(); i != range.end(); ++i )
			{
				pathScope.setPath( &((*sourcePaths)[i]) );
				Box3f childBound = effectiveSource->boundPlug()->getValue();

				// We're evaluating relativeTransform here, which is also needed in computeObject(). It doesn't seem
				// expensive enough to be worth another caching plug.
				childBound = Imath::transform( childBound, relativeTransform(
					(*sourcePaths)[i], path, effectiveSource, inPlug(), pathScope,
					matchingPrefix, toDest
				) );
				result.extendBy( childBound );
			}
			return result;

		},
		[] ( const Box3f &x, const Box3f &y ) {

			Box3f result = x;
			result.extendBy( y );
			return result;

		},
		tbb::auto_partitioner(),
		taskGroupContext
	);
}

void MergeObjects::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstObjectPtr parentHolder;
	const SourcePaths *sourcePaths = findSources( mergeLocationPlug(), path, context, parentHolder );
	if( !sourcePaths )
	{
		if( !inPlug()->existsPlug()->getValue() )
		{
			h = inPlug()->objectPlug()->defaultHash();
			return;
		}

		int filterValue = pruneFilterValue( inPlug(), filterPlug(), sourcePlug(), context );

		if( filterValue & IECore::PathMatcher::ExactMatch )
		{
			h = inPlug()->objectPlug()->defaultHash();
		}
		else
		{
			h = inPlug()->objectPlug()->hash();
		}
		return;
	}

	FilteredSceneProcessor::hashObject( path, context, parent, h );
	processedObjectPlug()->hash( h );
}

IECore::ConstObjectPtr MergeObjects::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstObjectPtr parentHolder;
	const SourcePaths *sourcePaths = findSources( mergeLocationPlug(), path, context, parentHolder );
	if( !sourcePaths )
	{
		// This location isn't a destination, so either pass through the input mesh, or just pass
		// a null object if this is a new location, or the previous mesh was a source for the merge.
		if( !inPlug()->existsPlug()->getValue() )
		{
			return inPlug()->objectPlug()->defaultValue();
		}

		int filterValue = pruneFilterValue( inPlug(), filterPlug(), sourcePlug(), context );

		if( filterValue & IECore::PathMatcher::ExactMatch )
		{
			return inPlug()->objectPlug()->defaultValue();
		}
		else
		{
			return inPlug()->objectPlug()->getValue();
		}
	}

	return processedObjectPlug()->getValue();
}

void MergeObjects::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( inPlug()->existsPlug()->getValue() )
	{
		h = inPlug()->transformPlug()->hash();
	}
	else
	{
		h = inPlug()->transformPlug()->defaultHash();
	}
}

Imath::M44f MergeObjects::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( inPlug()->existsPlug()->getValue() )
	{
		return inPlug()->transformPlug()->getValue();
	}
	else
	{
		return inPlug()->transformPlug()->defaultValue();
	}
}

void MergeObjects::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( inPlug()->existsPlug()->getValue() )
	{
		h = inPlug()->attributesPlug()->hash();
	}
	else
	{
		h = inPlug()->attributesPlug()->defaultHash();
	}
}

IECore::ConstCompoundObjectPtr MergeObjects::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( inPlug()->existsPlug()->getValue() )
	{
		return inPlug()->attributesPlug()->getValue();
	}
	else
	{
		return inPlug()->attributesPlug()->defaultValue();
	}
}


void MergeObjects::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashChildNames( path, context, parent, h );
	mergeLocationPlug()->hash( h );

	if( inPlug()->existsPlug()->getValue() )
	{
		inPlug()->childNamesPlug()->hash( h );
	}
}

IECore::ConstInternedStringVectorDataPtr MergeObjects::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstObjectPtr mergeLocationUntyped = mergeLocationPlug()->getValue();
	const MergeLocationData *mergeLocation = IECore::runTimeCast<const MergeLocationData>( mergeLocationUntyped.get() );
	if( !mergeLocation )
	{
		if( inPlug()->existsPlug()->getValue() )
		{
			return inPlug()->childNamesPlug()->getValue();
		}
		else
		{
			return inPlug()->childNamesPlug()->defaultValue();
		}
	}

	if( mergeLocation->m_childNamesData )
	{
		return mergeLocation->m_childNamesData;
	}
	else
	{
		return inPlug()->childNamesPlug()->defaultValue();
	}
}

void MergeObjects::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( isConnected( sourcePlug() ) )
	{
		h = inPlug()->setPlug()->hash();
		return;
	}

	FilteredSceneProcessor::hashSet( setName, context, parent, h );
	inPlug()->setPlug()->hash( h );
	treeHash( treePlug(), context, h );

	FilterPlug::SceneScope sceneScope( context, inPlug() );

	// The filter does not depend on which set we're evaluating, remove it
	// so we don't make separate cache entries.
	sceneScope.remove( ScenePlug::setNameContextName );

	// We need to get a hash representing the affects of the filter over
	// the whole scene, which we currently get by hashing the filterPlug
	// with no path in the context. It actually shouldn't be necessary to
	// remove it here, because the path should never be in the context when
	// evalauting a set - but we remove it to ensure that we're getting
	// the correct hash. Since this could probably only happen if someone
	// implements a custom C++ node incorrectly, in the future, it might be
	// reasonable to just throw an exception if the path is in the context
	// ( perhaps this could be caught in SceneNode::hash ).
	sceneScope.remove( ScenePlug::scenePathContextName );

	filterPlug()->hash( h );
}

IECore::ConstPathMatcherDataPtr MergeObjects::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( isConnected( sourcePlug() ) )
	{
		// If we're not operating in-place, then nothing is going to be removed from the set
		return inPlug()->setPlug()->getValue();
	}

	ConstPathMatcherDataPtr inputSetData = inPlug()->setPlug()->getValue();
	const PathMatcher &inputSet = inputSetData->readable();
	if( inputSet.isEmpty() )
	{
		return inputSetData;
	}

	PathMatcherDataPtr outputSetData = inputSetData->copy();
	PathMatcher &outputSet = outputSetData->writable();

	ConstTreeDataPtr treeData = tree( treePlug(), context );

	// We maintain a stack of locations matching our current position while traversing the set.
	// Set traversal is guaranteed to never add more than one level of nesting at a time, so we can keep
	// things in sync.
	std::vector< const TreeData::Location* > locationStack;

	FilterPlug::SceneScope sceneScope( context, inPlug() );
	sceneScope.remove( ScenePlug::setNameContextName );

	for( PathMatcher::RawIterator pIt = inputSet.begin(), peIt = inputSet.end(); pIt != peIt; )
	{
		sceneScope.set( ScenePlug::scenePathContextName, &(*pIt) );
		const int m = filterPlug()->getValue();

		locationStack.resize( pIt->size() );
		if( !locationStack.size() )
		{
			// Add the root location.
			locationStack.push_back( treeData->location( ScenePlug::ScenePath() ) );
		}
		else if( !locationStack.back() )
		{
			// We're already outside the hierarchy covered by the tree, keep adding null placeholders to
			// keep the stack the right size.
			locationStack.push_back( nullptr );
		}
		else
		{
			const auto childIter = locationStack.back()->children.find( pIt->back() );
			if( childIter != locationStack.back()->children.end() )
			{
				locationStack.push_back( childIter->second.get() );
			}
			else
			{
				locationStack.push_back( nullptr );
			}
		}

		if(
			// Check if there's a location for the current path
			locationStack.back() ||
			// Otherwise, maybe the parent location has this path as a destination?
			( locationStack.size() >= 2 && locationStack[ locationStack.size() - 2 ] && locationStack[ locationStack.size() - 2 ]->destinations.count( pIt->back() ) )
		)
		{
			// If this path is in the treeData, we don't prune it

			// If there is no filter match, we can stop examining this whole branch
			if( !( m & ( IECore::PathMatcher::ExactMatch | IECore::PathMatcher::AncestorMatch | IECore::PathMatcher::DescendantMatch ) ) )
			{
				pIt.prune();
			}

			++pIt;
		}
		else if( m & ( IECore::PathMatcher::ExactMatch | IECore::PathMatcher::AncestorMatch ) )
		{
			// This path and all below it are pruned, so we can
			// ignore it and prune the traversal to the descendant
			// paths.
			outputSet.prune( *pIt );
			pIt.prune();
			++pIt;
		}
		else if( m & IECore::PathMatcher::DescendantMatch )
		{
			// This path isn't pruned, so we continue our traversal
			// as normal to find out which descendants _are_ pruned.
			++pIt;
		}
		else
		{
			// This path isn't pruned, and neither is anything
			// below it. We can avoid retesting the filter for
			// all descendant paths, since we know they're not
			// pruned.
			assert( m == IECore::PathMatcher::NoMatch );
			pIt.prune();
			++pIt;
		}
	}

	return outputSetData;
}

Gaffer::ValuePlug::CachePolicy MergeObjects::hashCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == outPlug()->setPlug() )
	{
		// Technically we do not _need_ TaskIsolation because we have not yet
		// multithreaded `hashSet()`. But we still benefit from requesting it
		// because it means the hash is stored in the global cache, where it is
		// shared between all threads and is almost guaranteed not to be evicted.
		return ValuePlug::CachePolicy::TaskIsolation;
	}
	else if( output == treePlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	else if( output == processedObjectPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return FilteredSceneProcessor::hashCachePolicy( output );
}

Gaffer::ValuePlug::CachePolicy MergeObjects::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == treePlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	else if( output == processedObjectPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	else if( output == outPlug()->boundPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return FilteredSceneProcessor::computeCachePolicy( output );
}
