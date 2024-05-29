//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/BranchCreator.h"

#include "GafferScene/FilterResults.h"
#include "GafferScene/Private/ChildNamesMap.h"
#include "GafferScene/SceneAlgo.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "IECore/NullObject.h"

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

void mergeSetNames( const InternedStringVectorData *toAdd, vector<InternedString> &result )
{
	if( !toAdd )
	{
		return;
	}

	// This naive approach to merging set names preserves the order of the incoming names,
	// but at the expense of using linear search. We assume that the number of sets is small
	// enough and the InternedString comparison fast enough that this is OK.
	for( const auto &setName : toAdd->readable() )
	{
		if( std::find( result.begin(), result.end(), setName ) == result.end() )
		{
			result.push_back( setName );
		}
	}
}

// Returns the length prefix of the path which exists in the given scene
size_t existingPathLength( const ScenePlug *scene, const ScenePlug::ScenePath &path )
{
	ScenePlug::PathScope scope( Context::current() );
	scope.setPath( &path );
	if( scene->existsPlug()->getValue() )
	{
		return path.size();
	}

	ScenePlug::ScenePath prefix = path;
	prefix.pop_back();
	while( prefix.size() )
	{
		scope.setPath( &prefix );
		if( scene->existsPlug()->getValue() )
		{
			return prefix.size();
		}
		prefix.pop_back();
	}
	return 0;
}

// InternedString compares by pointer address by default, which will give differing
// results betweeen processes. Comparing by string value gives an alphabetical ordering
// we can rely on.
bool internedStringValueLess( const InternedString &a, const InternedString &b )
{
	return a.string() < b.string();
}

const InternedString g_ellipsis( "..." );

void validateDestination( const ScenePlug::ScenePath &destination )
{
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
					"Invalid destination `{}`. {}",
					ScenePlug::pathToString( destination ),
					e.what()
				)
			);
		}
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// BranchCreator::BranchesData
//////////////////////////////////////////////////////////////////////////

class BranchCreator::BranchesData : public IECore::Data
{

	public :

		struct Location
		{
			using Ptr = std::unique_ptr<Location>;
			using ChildMap = std::unordered_map<IECore::InternedString, Ptr>;
			using SourcePaths = vector<ScenePlug::ScenePath>;

			Location( size_t depth, bool exists ) : exists( exists ), depth( depth ) {}

			// True if this location exists in the input
			// scene.
			const bool exists;
			// Depth of this location in the scene.
			const size_t depth;
			// Child locations.
			ChildMap children;
			// The source paths for this destination.
			// Null if this is not a destination.
			std::unique_ptr<SourcePaths> sourcePaths;
			// Names of children which do not exist in
			// the input scene. Null if all children
			// exist in the input.
			InternedStringVectorDataPtr newChildNames;

		};

		BranchesData( const BranchCreator *branchCreator, const Context *context )
			:	m_root( new Location( 0, true ) )
		{
			auto f = [this, branchCreator]( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &path )
			{
				addBranch( branchCreator, path );
				return true;
			};
			SceneAlgo::filteredParallelTraverse( branchCreator->inPlug(), branchCreator->filterPlug(), f );

			if( !branchCreator->filterPlug()->getInput() )
			{
				const auto parent = branchCreator->parentPlugPath();
				if( parent )
				{
					ScenePlug::PathScope pathScope( context, &*parent );
					addBranch( branchCreator, *parent );
				}
			}

			// When multiple sources map to the same destination, we have no guarantees about
			// the order they will be visited above. Sort them alphabetically so that our output
			// is stable from run to run.
			visitLocationsWalk(
				[] ( const ScenePlug::ScenePath &path, Location *location ) {
					if( location->sourcePaths )
					{
						std::sort(
							location->sourcePaths->begin(), location->sourcePaths->end(),
							[] ( const ScenePlug::ScenePath &a, const ScenePlug::ScenePath &b ) {
								return lexicographical_compare(
									a.begin(), a.end(), b.begin(), b.end(),
									internedStringValueLess
								);
							}
						);
					}
					if( location->newChildNames )
					{
						std::sort(
							location->newChildNames->writable().begin(), location->newChildNames->writable().end(),
							internedStringValueLess
						);
					}
				},
				ScenePath(),
				m_root.get()
			);

		}

		static bool affectedBy( const BranchCreator *branchCreator, const Plug *input )
		{
			return
				input == branchCreator->filterPlug() ||
				input == branchCreator->inPlug()->childNamesPlug() ||
				input == branchCreator->parentPlug() ||
				input == branchCreator->inPlug()->existsPlug() ||
				input == branchCreator->destinationPlug()
			;
		}

		static void hash( const BranchCreator *branchCreator, const Context *context, IECore::MurmurHash &h )
		{
			// See `SceneAlgo::matchingPathsHash()` for documentation of this hashing strategy.
			std::atomic<uint64_t> h1( 0 ), h2( 0 );
			auto f = [branchCreator, &h1, &h2]( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &path )
			{
				IECore::MurmurHash h;
				hashBranch( branchCreator, path, h );
				h1 += h.h1();
				h2 += h.h2();
				return true;
			};
			SceneAlgo::filteredParallelTraverse( branchCreator->inPlug(), branchCreator->filterPlug(), f );
			h.append( MurmurHash( h1, h2 ) );

			if( !branchCreator->filterPlug()->getInput() )
			{
				const auto parent = branchCreator->parentPlugPath();
				if( parent )
				{
					ScenePlug::PathScope pathScope( context, &*parent );
					hashBranch( branchCreator, *parent, h );
				}
			}
		}

		bool empty() const
		{
			return m_root->children.empty() && !m_root->sourcePaths;
		}

		const Location *locationOrAncestor( const ScenePlug::ScenePath &path ) const
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
					break;
				}
			}
			return result;
		}

		const Location::SourcePaths &sourcePaths( const ScenePlug::ScenePath &destination ) const
		{
			const Location *location = locationOrAncestor( destination );
			assert( location->depth == destination.size() );
			if( !location->sourcePaths )
			{
				throw IECore::Exception( fmt::format( "No source paths found for destination \"{}\"", ScenePlug::pathToString( destination ) ) );
			}
			return *location->sourcePaths;
		}

		template<typename F>
		void visitDestinations( F &&f ) const
		{
			visitLocationsWalk(
				[ &f ] ( const ScenePlug::ScenePath &path, const Location *location ) {
					if( location->sourcePaths )
					{
						f( path, *location->sourcePaths );
					}
				},
				ScenePath(),
				m_root.get()
			);
		}

	private :

		template<typename F>
		void visitLocationsWalk( F &&f, const ScenePlug::ScenePath &path, Location *location ) const
		{
			f( path, location );

			ScenePlug::ScenePath childPath = path; childPath.push_back( InternedString() );
			for( const auto &child : location->children )
			{
				childPath.back() = child.first;
				visitLocationsWalk( f, childPath, child.second.get() );
			}
		}

		static void hashBranch( const BranchCreator *branchCreator, const ScenePlug::ScenePath &path, IECore::MurmurHash &h )
		{
			h.append( path.data(), path.size() );
			h.append( (uint64_t)path.size() );

			const ScenePlug::ScenePath destination = ScenePlug::stringToPath( branchCreator->destinationPlug()->getValue() );
			validateDestination( destination );

			h.append( destination.data(), destination.size() );
			h.append( (uint64_t)destination.size() );

			h.append( existingPathLength( branchCreator->inPlug(), destination ) );
		}

		void addBranch( const BranchCreator *branchCreator, const ScenePlug::ScenePath &path )
		{
			const ScenePlug::ScenePath destination = ScenePlug::stringToPath( branchCreator->destinationPlug()->getValue() );
			validateDestination( destination );
			const size_t existingPathLen = existingPathLength( branchCreator->inPlug(), destination );

			tbb::spin_mutex::scoped_lock lock( m_mutex );

			Location *location = m_root.get();
			for( const auto &name : destination )
			{
				if( !location->exists && location->sourcePaths )
				{
					// We don't yet support merging branch children with new locations
					// introduced by destinations that didn't previously exist.
					throw IECore::Exception( fmt::format(
						"Destination \"{}\" contains a nested destination",
						ScenePlug::pathToString( ScenePath( destination.begin(), destination.begin() + location->depth ) )
					) );
				}

				const auto inserted = location->children.insert( Location::ChildMap::value_type( name, Location::Ptr() ) );
				if( inserted.second )
				{
					const bool exists = location->depth < existingPathLen;
					inserted.first->second = std::make_unique<Location>( location->depth + 1, exists );
					if( !exists )
					{
						if( !location->newChildNames )
						{
							location->newChildNames = new InternedStringVectorData;
						}
						location->newChildNames->writable().push_back( name );
					}
				}
				location = inserted.first->second.get();
			}

			if( !location->sourcePaths )
			{
				if( !location->exists && location->children.size() )
				{
					throw IECore::Exception( fmt::format(
						"Destination \"{}\" contains a nested destination",
						ScenePlug::pathToString( destination )
					) );
				}
				location->sourcePaths.reset( new Location::SourcePaths );
			}
			location->sourcePaths->push_back( path );
		}

		tbb::spin_mutex m_mutex;
		Location::Ptr m_root;

};

//////////////////////////////////////////////////////////////////////////
// BranchCreator
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( BranchCreator );

size_t BranchCreator::g_firstPlugIndex = 0;

BranchCreator::BranchCreator( const std::string &name )
	:	FilteredSceneProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "parent" ) );
	addChild( new StringPlug( "destination", Gaffer::Plug::In, "${scene:path}" ) );

	addChild( new ObjectPlug( "__branches", Gaffer::Plug::Out, IECore::NullObject::defaultNullObject() ) );
	addChild( new ObjectPlug( "__mapping", Gaffer::Plug::Out, IECore::NullObject::defaultNullObject() ) );

	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
	outPlug()->childBoundsPlug()->setFlags( Plug::AcceptsDependencyCycles, true );
}

BranchCreator::~BranchCreator()
{
}

Gaffer::StringPlug *BranchCreator::parentPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *BranchCreator::parentPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *BranchCreator::destinationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *BranchCreator::destinationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::ObjectPlug *BranchCreator::branchesPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ObjectPlug *BranchCreator::branchesPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 2 );
}

Gaffer::ObjectPlug *BranchCreator::mappingPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::ObjectPlug *BranchCreator::mappingPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 3 );
}

void BranchCreator::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if( BranchesData::affectedBy( this, input ) )
	{
		outputs.push_back( branchesPlug() );
	}

	if(
		input == inPlug()->childNamesPlug() ||
		input == branchesPlug() ||
		affectsBranchChildNames( input )
	)
	{
		outputs.push_back( mappingPlug() );
	}

	if(
		input == branchesPlug() ||
		input == mappingPlug() ||
		input == inPlug()->boundPlug() ||
		input == outPlug()->childBoundsPlug() ||
		affectsBranchBound( input )
	)
	{
		outputs.push_back( outPlug()->boundPlug() );
	}

	if(
		input == branchesPlug() ||
		input == mappingPlug() ||
		input == inPlug()->transformPlug() ||
		affectsBranchTransform( input )
	)
	{
		outputs.push_back( outPlug()->transformPlug() );
	}

	if(
		input == branchesPlug() ||
		input == mappingPlug() ||
		input == inPlug()->attributesPlug() ||
		affectsBranchAttributes( input )
	)
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}

	if(
		input == branchesPlug() ||
		input == mappingPlug() ||
		input == inPlug()->objectPlug() ||
		affectsBranchObject( input )
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}

	if(
		input == branchesPlug() ||
		input == mappingPlug() ||
		input == inPlug()->childNamesPlug() ||
		affectsBranchChildNames( input )
	)
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}

	if(
		input == branchesPlug() ||
		input == inPlug()->setNamesPlug() ||
		affectsBranchSetNames( input )
	)
	{
		outputs.push_back( outPlug()->setNamesPlug() );
	}

	if(
		affectsBranchesForSet( input ) ||
		input == mappingPlug() ||
		input == inPlug()->setPlug() ||
		affectsBranchSet( input )
	)
	{
		outputs.push_back( outPlug()->setPlug() );
	}
}

std::optional<ScenePlug::ScenePath> BranchCreator::parentPlugPath() const
{
	const string parentAsString = parentPlug()->getValue();
	if( parentAsString.empty() )
	{
		return std::nullopt;
	}

	ScenePlug::ScenePath parent;
	ScenePlug::stringToPath( parentAsString, parent );
	if( inPlug()->exists( parent ) )
	{
		return parent;
	}

	return std::nullopt;
}

void BranchCreator::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hash( output, context, h );

	if( output == branchesPlug() )
	{
		BranchesData::hash( this, context, h );
	}
	else if( output == mappingPlug() )
	{
		hashMapping( context, h );
	}
}

void BranchCreator::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == branchesPlug() )
	{
		static_cast<Gaffer::ObjectPlug *>( output )->setValue( new BranchesData( this, context ) );
	}
	else if( output == mappingPlug() )
	{
		static_cast<Gaffer::ObjectPlug *>( output )->setValue( computeMapping( context ) );
	}
	else
	{
		FilteredSceneProcessor::compute( output, context );
	}
}

void BranchCreator::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ScenePath sourcePath, branchPath;
	const LocationType locationType = sourceAndBranchPaths( path, sourcePath, branchPath );

	switch( locationType )
	{
		case Branch :
			hashBranchBound( sourcePath, branchPath, context, h );
			break;
		case Destination :
		case Ancestor :
			FilteredSceneProcessor::hashBound( path, context, parent, h );
			inPlug()->boundPlug()->hash( h );
			outPlug()->childBoundsPlug()->hash( h );
			break;
		case NewDestination :
		case NewAncestor :
			h = outPlug()->childBoundsPlug()->hash();
			break;
		case PassThrough :
		default :
			h = inPlug()->boundPlug()->hash();
			break;
	}
}

Imath::Box3f BranchCreator::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath sourcePath, branchPath;
	const LocationType locationType = sourceAndBranchPaths( path, sourcePath, branchPath );

	switch( locationType )
	{
		case Branch :
			return computeBranchBound( sourcePath, branchPath, context );
		case Destination :
		case Ancestor : {
			Box3f result = inPlug()->boundPlug()->getValue();
			result.extendBy( outPlug()->childBoundsPlug()->getValue() );
			return result;
		}
		case NewDestination :
		case NewAncestor :
			return outPlug()->childBoundsPlug()->getValue();
		case PassThrough :
		default :
			return inPlug()->boundPlug()->getValue();
	}
}

void BranchCreator::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ScenePath sourcePath, branchPath;
	const LocationType locationType = sourceAndBranchPaths( path, sourcePath, branchPath );

	switch( locationType )
	{
		case Branch : {
			hashBranchTransform( sourcePath, branchPath, context, h );
			if( branchPath.size() == 1 )
			{
				ScenePath destinationPath = path; destinationPath.pop_back();
				if( sourcePath != destinationPath )
				{
					h.append( inPlug()->fullTransformHash( sourcePath ) );
					h.append( outPlug()->fullTransform( destinationPath ) );
				}
			}
			break;
		}
		case Destination :
		case Ancestor :
		case PassThrough :
			h = inPlug()->transformPlug()->hash();
			break;
		default :
			h = inPlug()->transformPlug()->defaultHash();
	}
}

Imath::M44f BranchCreator::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath sourcePath, branchPath;
	const LocationType locationType = sourceAndBranchPaths( path, sourcePath, branchPath );

	switch( locationType )
	{
		case Branch : {
			M44f result = computeBranchTransform( sourcePath, branchPath, context );
			if( branchPath.size() == 1 )
			{
				ScenePath destinationPath = path; destinationPath.pop_back();
				if( sourcePath != destinationPath )
				{
					// Account for the difference between source and destination transforms so that
					// branches are positioned as if they were parented below the source.
					M44f relativeTransform = inPlug()->fullTransform( sourcePath ) * outPlug()->fullTransform( destinationPath ).inverse();
					result *= relativeTransform;
				}
			}
			return result;
		}
		case Destination :
		case Ancestor :
		case PassThrough :
			return inPlug()->transformPlug()->getValue();
		default :
			return inPlug()->transformPlug()->defaultValue();
	}
}

void BranchCreator::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ScenePath sourcePath, branchPath;
	const LocationType locationType = sourceAndBranchPaths( path, sourcePath, branchPath );

	switch( locationType )
	{
		case Branch :
			hashBranchAttributes( sourcePath, branchPath, context, h );
			break;
		case Destination :
		case Ancestor :
		case PassThrough :
			h = inPlug()->attributesPlug()->hash();
			break;
		default :
			h = inPlug()->attributesPlug()->defaultHash();
			break;
	}
}

IECore::ConstCompoundObjectPtr BranchCreator::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath sourcePath, branchPath;
	const LocationType locationType = sourceAndBranchPaths( path, sourcePath, branchPath );

	switch( locationType )
	{
		case Branch :
			return computeBranchAttributes( sourcePath, branchPath, context );
		case Destination :
		case Ancestor :
		case PassThrough :
			return inPlug()->attributesPlug()->getValue();
		default :
			return inPlug()->attributesPlug()->defaultValue();
	}
}

bool BranchCreator::processesRootObject() const
{
	return false;
}

void BranchCreator::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ScenePath sourcePath, branchPath;
	const LocationType locationType = sourceAndBranchPaths( path, sourcePath, branchPath );

	switch( locationType )
	{
		case Branch :
			hashBranchObject( sourcePath, branchPath, context, h );
			break;
		case Destination :
			if( processesRootObject() )
			{
				// See notes in `hashObject()`.
				if( !destinationPlug()->isSetToDefault() )
				{
					throw IECore::Exception( "Can only process root object when `destination` is default." );
				}
				hashBranchObject( path, branchPath, context, h );
				break;
			}
			[[fallthrough]];
		case Ancestor :
		case PassThrough :
			h = inPlug()->objectPlug()->hash();
			break;
		default :
			h = inPlug()->objectPlug()->defaultHash();
	}
}

IECore::ConstObjectPtr BranchCreator::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath sourcePath, branchPath;
	const LocationType locationType = sourceAndBranchPaths( path, sourcePath, branchPath );

	switch( locationType )
	{
		case Branch :
			return computeBranchObject( sourcePath, branchPath, context );
		case Destination :
			if( processesRootObject() )
			{
				/// \todo The `processesRootObject()` mechanism was intended to allow derived
				/// classes to modify the object at `sourcePath`, but it is not compatible
				/// with the new `destination` plug. We could continue to support it by doing
				/// another filter evaluation, but the mechanism of processing the "root"
				/// object feels bogus now that source and destination are decoupled. Come up
				/// with something more logical.
				if( !destinationPlug()->isSetToDefault() )
				{
					throw IECore::Exception( "Can only process root object when `destination` is default." );
				}
				return computeBranchObject( path, branchPath, context );
			}
			[[fallthrough]];
		case Ancestor :
		case PassThrough :
			return inPlug()->objectPlug()->getValue();
		default :
			return inPlug()->objectPlug()->defaultValue();
	}
}

void BranchCreator::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ScenePath sourcePath, branchPath;
	ConstInternedStringVectorDataPtr newChildNames;
	const LocationType locationType = sourceAndBranchPaths( path, sourcePath, branchPath, &newChildNames );

	switch( locationType )
	{
		case Branch :
			hashBranchChildNames( sourcePath, branchPath, context, h );
			break;
		case Destination :
		case NewDestination : {
			Private::ConstChildNamesMapPtr mapping = boost::static_pointer_cast<const Private::ChildNamesMap>( mappingPlug()->getValue() );
			h = mapping->outputChildNames()->Object::hash();
			break;
		}
		case NewAncestor :
			h = newChildNames->Object::hash();
			break;
		case Ancestor :
			if( newChildNames )
			{
				FilteredSceneProcessor::hashChildNames( path, context, parent, h );
				inPlug()->childNamesPlug()->hash( h );
				newChildNames->hash( h );
				return;
			}
			[[fallthrough]];
		case PassThrough :
		default :
			h = inPlug()->childNamesPlug()->hash();
	}
}

IECore::ConstInternedStringVectorDataPtr BranchCreator::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath sourcePath, branchPath;
	ConstInternedStringVectorDataPtr newChildNames;
	const LocationType locationType = sourceAndBranchPaths( path, sourcePath, branchPath, &newChildNames );

	switch( locationType )
	{
		case Branch :
			return computeBranchChildNames( sourcePath, branchPath, context );
		case Destination :
		case NewDestination : {
			Private::ConstChildNamesMapPtr mapping = boost::static_pointer_cast<const Private::ChildNamesMap>( mappingPlug()->getValue() );
			return mapping->outputChildNames();
		}
		case NewAncestor :
			return newChildNames;
		case Ancestor :
			if( newChildNames )
			{
				InternedStringVectorDataPtr combinedNames = inPlug()->childNamesPlug()->getValue()->copy();
				combinedNames->writable().insert(
					combinedNames->writable().end(),
					newChildNames->readable().begin(),
					newChildNames->readable().end()
				);
				return combinedNames;
			}
			[[fallthrough]];
		case PassThrough :
		default :
			return inPlug()->childNamesPlug()->getValue();
	}
}

void BranchCreator::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstBranchesDataPtr branchesData = branches( context );
	if( branchesData->empty() )
	{
		h = inPlug()->setNamesPlug()->hash();
		return;
	}

	FilteredSceneProcessor::hashSetNames( context, parent, h );
	inPlug()->setNamesPlug()->hash( h );

	if( constantBranchSetNames() )
	{
		MurmurHash branchSetNamesHash;
		hashBranchSetNames( ScenePlug::ScenePath(), context, branchSetNamesHash );
		h.append( branchSetNamesHash );
	}
	else
	{
		branchesData->visitDestinations(
			[&context, &h, this] ( const ScenePath &destination, const BranchesData::Location::SourcePaths &sourcePaths ) {
				for( const auto &sourcePath : sourcePaths )
				{
					MurmurHash branchSetNamesHash;
					hashBranchSetNames( sourcePath, context, branchSetNamesHash );
					h.append( branchSetNamesHash );
				}
			}
		);
	}
}

IECore::ConstInternedStringVectorDataPtr BranchCreator::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstBranchesDataPtr branchesData = branches( context );

	ConstInternedStringVectorDataPtr inputSetNamesData = inPlug()->setNamesPlug()->getValue();
	if( branchesData->empty() )
	{
		return inputSetNamesData;
	}

	InternedStringVectorDataPtr resultData = new InternedStringVectorData( inputSetNamesData->readable() );
	vector<InternedString> &result = resultData->writable();

	if( constantBranchSetNames() )
	{
		ConstInternedStringVectorDataPtr branchSetNamesData = computeBranchSetNames( ScenePlug::ScenePath(), context );
		mergeSetNames( branchSetNamesData.get(), result );
	}
	else
	{
		branchesData->visitDestinations(
			[&context, &result, this] ( const ScenePath &destination, const BranchesData::Location::SourcePaths &sourcePaths ) {
				for( const auto &sourcePath : sourcePaths )
				{
					ConstInternedStringVectorDataPtr branchSetNamesData = computeBranchSetNames( sourcePath, context );
					mergeSetNames( branchSetNamesData.get(), result );
				}
			}
		);
	}

	return resultData;
}

void BranchCreator::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstBranchesDataPtr branches = branchesForSet( setName, context );
	if( !branches )
	{
		h = inPlug()->setPlug()->hash();
		return;
	}

	FilteredSceneProcessor::hashSet( setName, context, parent, h );
	inPlug()->setPlug()->hash( h );

	/// \todo Parallelise.
	branches->visitDestinations(
		[&setName, &context, &h, this] ( const ScenePath &destination, const BranchesData::Location::SourcePaths &sourcePaths ) {
			for( const auto &sourcePath : sourcePaths )
			{
				MurmurHash branchSetHash;
				hashBranchSet( sourcePath, setName, context, branchSetHash );
				h.append( branchSetHash );
			}
			ScenePlug::PathScope pathScope( context, &destination );
			mappingPlug()->hash( h );
			h.append( destination.data(), destination.size() );
		}
	);
}

IECore::ConstPathMatcherDataPtr BranchCreator::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstPathMatcherDataPtr inputSetData = inPlug()->setPlug()->getValue();

	ConstBranchesDataPtr branches = branchesForSet( setName, context );
	if( !branches )
	{
		return inputSetData;
	}

	PathMatcherDataPtr outputSetData = inputSetData->copy();
	PathMatcher &outputSet = outputSetData->writable();

	/// \todo Parallelise.
	branches->visitDestinations(
		[&setName, &context, &outputSet, this] ( const ScenePath &destination, const BranchesData::Location::SourcePaths &sourcePaths ) {
			vector<ConstPathMatcherDataPtr> branchSets = { nullptr };
			for( const auto &sourcePath : sourcePaths )
			{
				branchSets.push_back( computeBranchSet( sourcePath, setName, context ) );
			}
			ScenePlug::PathScope pathScope( context, &destination );
			Private::ConstChildNamesMapPtr mapping = boost::static_pointer_cast<const Private::ChildNamesMap>( mappingPlug()->getValue() );
			outputSet.addPaths( mapping->set( branchSets ), destination );
		}
	);

	return outputSetData;
}

Gaffer::ValuePlug::CachePolicy BranchCreator::hashCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == outPlug()->setPlug() )
	{
		// Technically we do not _need_ TaskIsolation because we have not yet
		// multithreaded `hashSet()`. But we still benefit from requesting it
		// because it means the hash is stored in the global cache, where it is
		// shared between all threads and is almost guaranteed not to be evicted.
		return ValuePlug::CachePolicy::TaskIsolation;
	}
	else if( output == branchesPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return FilteredSceneProcessor::hashCachePolicy( output );
}

Gaffer::ValuePlug::CachePolicy BranchCreator::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == branchesPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return FilteredSceneProcessor::computeCachePolicy( output );
}

BranchCreator::ConstBranchesDataPtr BranchCreator::branchesForSet( const IECore::InternedString &setName, const Gaffer::Context *context ) const
{
	if( constantBranchSetNames() )
	{
		// All branches provide the same sets. If that doesn't include the set in question
		// then we don't need to visit any of the parent paths at all, and can early out
		// in `hashSet()` and `computeSet()`.
		ConstInternedStringVectorDataPtr branchSetNamesData;
		{
			ScenePlug::GlobalScope globalScope( context );
			branchSetNamesData = computeBranchSetNames( ScenePlug::ScenePath(), context );
		}
		if( !branchSetNamesData )
		{
			return nullptr;
		}
		const auto &branchSetNames = branchSetNamesData->readable();
		if( find( branchSetNames.begin(), branchSetNames.end(), setName ) == branchSetNames.end() )
		{
			return nullptr;
		}
	}

	ConstBranchesDataPtr b = branches( context );
	return b->empty() ? nullptr : b;
}

bool BranchCreator::affectsBranchesForSet( const Gaffer::Plug *input ) const
{
	return
		( constantBranchSetNames() && affectsBranchSetNames( input ) ) ||
		input == branchesPlug()
	;
}

bool BranchCreator::affectsBranchBound( const Gaffer::Plug *input ) const
{
	return false;
}

bool BranchCreator::affectsBranchTransform( const Gaffer::Plug *input ) const
{
	return false;
}

bool BranchCreator::affectsBranchAttributes( const Gaffer::Plug *input ) const
{
	return false;
}

bool BranchCreator::affectsBranchObject( const Gaffer::Plug *input ) const
{
	return false;
}

bool BranchCreator::affectsBranchChildNames( const Gaffer::Plug *input ) const
{
	return false;
}

bool BranchCreator::affectsBranchSetNames( const Gaffer::Plug *input ) const
{
	return false;
}

bool BranchCreator::affectsBranchSet( const Gaffer::Plug *input ) const
{
	return false;
}

void BranchCreator::hashBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashBound( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), context, inPlug(), h );
}

void BranchCreator::hashBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashTransform( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), context, inPlug(), h );
}

void BranchCreator::hashBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashAttributes( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), context, inPlug(), h );
}

void BranchCreator::hashBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashObject( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), context, inPlug(), h );
}

void BranchCreator::hashBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashChildNames( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), context, inPlug(), h );
}

void BranchCreator::hashBranchSetNames( const ScenePath &sourcePath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

IECore::ConstInternedStringVectorDataPtr BranchCreator::computeBranchSetNames( const ScenePath &sourcePath, const Gaffer::Context *context ) const
{
	// It's OK to return nullptr, because the value returned from this method
	// isn't used as the result of a compute(), and won't be stored on a plug.
	// For the same reason, it's ok for hashBranchSetNames() to do nothing by default
	return nullptr;
}

bool BranchCreator::constantBranchSetNames() const
{
	return true;
}

void BranchCreator::hashBranchSet( const ScenePath &sourcePath, const IECore::InternedString &setName, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

IECore::ConstPathMatcherDataPtr BranchCreator::computeBranchSet( const ScenePath &sourcePath, const IECore::InternedString &setName, const Gaffer::Context *context ) const
{
	// See comments in computeBranchSetNames.
	return nullptr;
}

void BranchCreator::hashMapping( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( inPlug()->existsPlug()->getValue() )
	{
		inPlug()->childNamesPlug()->hash( h );
	}

	ConstBranchesDataPtr branchesData = branches( Context::current() );
	const ScenePlug::ScenePath &destinationPath = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	for( const auto &sourcePath : branchesData->sourcePaths( destinationPath ) )
	{
		MurmurHash branchChildNamesHash;
		hashBranchChildNames( sourcePath, ScenePath(), context, branchChildNamesHash );
		h.append( branchChildNamesHash );
	}
}

IECore::ConstDataPtr BranchCreator::computeMapping( const Gaffer::Context *context ) const
{
	vector<ConstInternedStringVectorDataPtr> childNames;
	if( inPlug()->existsPlug()->getValue() )
	{
		childNames.push_back( inPlug()->childNamesPlug()->getValue() );
	}
	else
	{
		childNames.push_back( new InternedStringVectorData );
	}

	ConstBranchesDataPtr branchesData = branches( Context::current() );
	const ScenePlug::ScenePath &destinationPath = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	for( const auto &sourcePath : branchesData->sourcePaths( destinationPath ) )
	{
		childNames.push_back( computeBranchChildNames( sourcePath, ScenePath(), context ) );
	}

	return new Private::ChildNamesMap( childNames );
}

BranchCreator::ConstBranchesDataPtr BranchCreator::branches( const Gaffer::Context *context ) const
{
	ScenePlug::GlobalScope globalScope( context );
	return static_pointer_cast<const BranchesData>( branchesPlug()->getValue() );
}

BranchCreator::LocationType BranchCreator::sourceAndBranchPaths( const ScenePath &path, ScenePath &sourcePath, ScenePath &branchPath, IECore::ConstInternedStringVectorDataPtr *newChildNames ) const
{
	ConstBranchesDataPtr branchesData = branches( Context::current() );
	const BranchesData::Location *location = branchesData->locationOrAncestor( path );

	if( newChildNames && location->depth == path.size() )
	{
		*newChildNames = location->newChildNames;
	}

	if( location->sourcePaths )
	{
		if( location->depth < path.size() )
		{
			Private::ConstChildNamesMapPtr mapping;
			{
				const ScenePath destinationPath( path.begin(), path.begin() + location->depth );
				ScenePlug::PathScope pathScope( Context::current(), &destinationPath );
				mapping = boost::static_pointer_cast<const Private::ChildNamesMap>( mappingPlug()->getValue() );
			}

			const Private::ChildNamesMap::Input input = mapping->input( path[location->depth] );
			if( input.index >= 1 )
			{
				branchPath.assign( path.begin() + location->depth, path.end() );
				branchPath[0] = input.name;
				sourcePath = (*location->sourcePaths)[input.index-1];
				return Branch;
			}
			else
			{
				return PassThrough;
			}
		}
		else
		{
			return location->exists ? Destination : NewDestination;
		}
	}

	if( path.size() == location->depth && !location->children.empty() )
	{
		return location->exists ? Ancestor : NewAncestor;
	}
	else
	{
		return PassThrough;
	}
}

IECore::PathMatcher::Result BranchCreator::parentAndBranchPaths( const ScenePath &path, ScenePath &parentPath, ScenePath &branchPath ) const
{
	const LocationType locationType = sourceAndBranchPaths( path, parentPath, branchPath );
	switch( locationType )
	{
		case Branch :
			return IECore::PathMatcher::AncestorMatch;
		case Destination :
		case NewDestination :
			return IECore::PathMatcher::ExactMatch;
		case Ancestor :
		case NewAncestor :
			return IECore::PathMatcher::DescendantMatch;
		case PassThrough :
			return IECore::PathMatcher::NoMatch;
	}

	assert( false ); // Should not get here
	return IECore::PathMatcher::NoMatch;
}
