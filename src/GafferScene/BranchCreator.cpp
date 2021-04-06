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

} // namespace

//////////////////////////////////////////////////////////////////////////
// BranchCreator::BranchesData
//////////////////////////////////////////////////////////////////////////

class BranchCreator::BranchesData : public IECore::Data
{

	public :

		BranchesData( const BranchCreator *branchCreator, const Context *context )
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
					addBranch( branchCreator, *parent );
				}
			}
		}

		static bool affectedBy( const BranchCreator *branchCreator, const Plug *input )
		{
			return
				input == branchCreator->filterPlug() ||
				input == branchCreator->inPlug()->childNamesPlug() ||
				input == branchCreator->parentPlug() ||
				input == branchCreator->inPlug()->existsPlug()
			;
		}

		static void hash( const BranchCreator *branchCreator, const Context *context, IECore::MurmurHash &h )
		{
			// See `SceneAlgo::matchingPathsHash()` for documentation of this hashing strategy.
			std::atomic<uint64_t> h1, h2;
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
					hashBranch( branchCreator, *parent, h );
				}
			}
		}

		const IECore::PathMatcher &parentPaths() const
		{
			return m_parentPaths;
		}

	private :

		static void hashBranch( const BranchCreator *branchCreator, const ScenePlug::ScenePath &path, IECore::MurmurHash &h )
		{
			if( path.size() )
			{
				h.append( path.data(), path.size() );
			}
			else
			{
				h.append( 0 );
			}
		}

		void addBranch( const BranchCreator *branchCreator, const ScenePlug::ScenePath &path )
		{
			tbb::spin_mutex::scoped_lock lock( m_mutex );
			m_parentPaths.addPath( path );
		}

		tbb::spin_mutex m_mutex;
		IECore::PathMatcher m_parentPaths;

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

Gaffer::ObjectPlug *BranchCreator::branchesPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::ObjectPlug *BranchCreator::branchesPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 1 );
}

Gaffer::ObjectPlug *BranchCreator::mappingPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 2
}

const Gaffer::ObjectPlug *BranchCreator::mappingPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 2 );
}

void BranchCreator::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if( BranchesData::affectedBy( this, input ) )
	{
		outputs.push_back( branchesPlug() );
	}

	if( input == inPlug()->childNamesPlug() || affectsBranchChildNames( input ) )
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
		affectsParentPathsForSet( input ) ||
		input == mappingPlug() ||
		input == inPlug()->setPlug() ||
		affectsBranchSet( input )
	)
	{
		outputs.push_back( outPlug()->setPlug() );
	}
}

boost::optional<ScenePlug::ScenePath> BranchCreator::parentPlugPath() const
{
	const string parentAsString = parentPlug()->getValue();
	if( parentAsString.empty() )
	{
		return boost::none;
	}

	ScenePlug::ScenePath parent;
	ScenePlug::stringToPath( parentAsString, parent );
	if( inPlug()->exists( parent ) )
	{
		return parent;
	}

	return boost::none;
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
	ScenePath parentPath, branchPath;
	const IECore::PathMatcher::Result parentMatch = parentAndBranchPaths( path, parentPath, branchPath );

	if( parentMatch == IECore::PathMatcher::AncestorMatch )
	{
		hashBranchBound( parentPath, branchPath, context, h );
	}
	else if( parentMatch == IECore::PathMatcher::ExactMatch || parentMatch == IECore::PathMatcher::DescendantMatch )
	{
		FilteredSceneProcessor::hashBound( path, context, parent, h );
		inPlug()->boundPlug()->hash( h );
		outPlug()->childBoundsPlug()->hash( h );
	}
	else
	{
		h = inPlug()->boundPlug()->hash();
	}
}

Imath::Box3f BranchCreator::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath parentPath, branchPath;
	const IECore::PathMatcher::Result parentMatch = parentAndBranchPaths( path, parentPath, branchPath );

	if( parentMatch == IECore::PathMatcher::AncestorMatch )
	{
		return computeBranchBound( parentPath, branchPath, context );
	}
	else if( parentMatch == IECore::PathMatcher::ExactMatch || parentMatch == IECore::PathMatcher::DescendantMatch )
	{
		Box3f result = inPlug()->boundPlug()->getValue();
		result.extendBy( outPlug()->childBoundsPlug()->getValue() );
		return result;
	}
	else
	{
		return inPlug()->boundPlug()->getValue();
	}
}

void BranchCreator::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ScenePath parentPath, branchPath;
	const IECore::PathMatcher::Result parentMatch = parentAndBranchPaths( path, parentPath, branchPath );

	if( parentMatch == IECore::PathMatcher::AncestorMatch )
	{
		hashBranchTransform( parentPath, branchPath, context, h );
	}
	else
	{
		h = inPlug()->transformPlug()->hash();
	}
}

Imath::M44f BranchCreator::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath parentPath, branchPath;
	const IECore::PathMatcher::Result parentMatch = parentAndBranchPaths( path, parentPath, branchPath );

	if( parentMatch == IECore::PathMatcher::AncestorMatch )
	{
		return computeBranchTransform( parentPath, branchPath, context );
	}
	else
	{
		return inPlug()->transformPlug()->getValue();
	}
}

void BranchCreator::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ScenePath parentPath, branchPath;
	const IECore::PathMatcher::Result parentMatch = parentAndBranchPaths( path, parentPath, branchPath );

	if( parentMatch == IECore::PathMatcher::AncestorMatch )
	{
		hashBranchAttributes( parentPath, branchPath, context, h );
	}
	else
	{
		h = inPlug()->attributesPlug()->hash();
	}
}

IECore::ConstCompoundObjectPtr BranchCreator::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath parentPath, branchPath;
	const IECore::PathMatcher::Result parentMatch = parentAndBranchPaths( path, parentPath, branchPath );

	if( parentMatch == IECore::PathMatcher::AncestorMatch )
	{
		return computeBranchAttributes( parentPath, branchPath, context );
	}
	else
	{
		return inPlug()->attributesPlug()->getValue();
	}
}

bool BranchCreator::processesRootObject() const
{
	return false;
}

void BranchCreator::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ScenePath parentPath, branchPath;
	const IECore::PathMatcher::Result parentMatch = parentAndBranchPaths( path, parentPath, branchPath );

	if( parentMatch == IECore::PathMatcher::AncestorMatch )
	{
		hashBranchObject( parentPath, branchPath, context, h );
	}
	else if( parentMatch == IECore::PathMatcher::ExactMatch && processesRootObject() )
	{
		// note branchPath is empty here
		hashBranchObject( parentPath, branchPath, context, h );
	}
	else
	{
		h = inPlug()->objectPlug()->hash();
	}
}

IECore::ConstObjectPtr BranchCreator::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath parentPath, branchPath;
	const IECore::PathMatcher::Result parentMatch = parentAndBranchPaths( path, parentPath, branchPath );

	if( parentMatch == IECore::PathMatcher::AncestorMatch )
	{
		return computeBranchObject( parentPath, branchPath, context );
	}
	else if( parentMatch == IECore::PathMatcher::ExactMatch && processesRootObject() )
	{
		// note branchPath is empty here
		return computeBranchObject( parentPath, branchPath, context );
	}
	else
	{
		return inPlug()->objectPlug()->getValue();
	}
}

void BranchCreator::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ScenePath parentPath, branchPath;
	const IECore::PathMatcher::Result parentMatch = parentAndBranchPaths( path, parentPath, branchPath );

	if( parentMatch == IECore::PathMatcher::AncestorMatch )
	{
		hashBranchChildNames( parentPath, branchPath, context, h );
	}
	else if( parentMatch == IECore::PathMatcher::ExactMatch )
	{
		Private::ConstChildNamesMapPtr mapping = boost::static_pointer_cast<const Private::ChildNamesMap>( mappingPlug()->getValue() );
		h = mapping->outputChildNames()->Object::hash();
	}
	else
	{
		h = inPlug()->childNamesPlug()->hash();
	}
}

IECore::ConstInternedStringVectorDataPtr BranchCreator::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ScenePath parentPath, branchPath;
	const IECore::PathMatcher::Result parentMatch = parentAndBranchPaths( path, parentPath, branchPath );

	if( parentMatch == IECore::PathMatcher::AncestorMatch )
	{
		return computeBranchChildNames( parentPath, branchPath, context );
	}
	else if( parentMatch == IECore::PathMatcher::ExactMatch )
	{
		Private::ConstChildNamesMapPtr mapping = boost::static_pointer_cast<const Private::ChildNamesMap>( mappingPlug()->getValue() );
		return mapping->outputChildNames();
	}
	else
	{
		return inPlug()->childNamesPlug()->getValue();
	}
}

void BranchCreator::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstBranchesDataPtr branchesData = branches( context );
	const PathMatcher &parentPaths = branchesData->parentPaths();

	if( parentPaths.isEmpty() )
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
		for( PathMatcher::Iterator it = parentPaths.begin(), eIt = parentPaths.end(); it != eIt; ++it )
		{
			MurmurHash branchSetNamesHash;
			hashBranchSetNames( *it, context, branchSetNamesHash );
			h.append( branchSetNamesHash );
		}
	}
}

IECore::ConstInternedStringVectorDataPtr BranchCreator::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstBranchesDataPtr branchesData = branches( context );
	const PathMatcher &parentPaths = branchesData->parentPaths();

	ConstInternedStringVectorDataPtr inputSetNamesData = inPlug()->setNamesPlug()->getValue();

	if( parentPaths.isEmpty() )
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
		for( PathMatcher::Iterator it = parentPaths.begin(), eIt = parentPaths.end(); it != eIt; ++it )
		{
			ConstInternedStringVectorDataPtr branchSetNamesData = computeBranchSetNames( *it, context );
			mergeSetNames( branchSetNamesData.get(), result );
		}
	}

	return resultData;
}

void BranchCreator::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	const PathMatcher parentPaths = parentPathsForSet( setName, context );
	if( parentPaths.isEmpty() )
	{
		h = inPlug()->setPlug()->hash();
		return;
	}

	FilteredSceneProcessor::hashSet( setName, context, parent, h );
	inPlug()->setPlug()->hash( h );

	/// \todo Parallelise.
	for( PathMatcher::Iterator it = parentPaths.begin(), eIt = parentPaths.end(); it != eIt; ++it )
	{
		const ScenePlug::ScenePath &parentPath = *it;
		{
			ScenePlug::PathScope pathScope( context, parentPath );
			pathScope.setPath( parentPath );
			mappingPlug()->hash( h );
		}
		MurmurHash branchSetHash;
		hashBranchSet( parentPath, setName, context, branchSetHash );
		h.append( branchSetHash );
		h.append( parentPath.data(), parentPath.size() );
	}
}

IECore::ConstPathMatcherDataPtr BranchCreator::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstPathMatcherDataPtr inputSetData = inPlug()->setPlug()->getValue();

	const PathMatcher parentPaths = parentPathsForSet( setName, context );
	if( parentPaths.isEmpty() )
	{
		return inputSetData;
	}

	PathMatcherDataPtr outputSetData = inputSetData->copy();
	PathMatcher &outputSet = outputSetData->writable();

	/// \todo Parallelise.
	vector<InternedString> outputPrefix;
	for( PathMatcher::Iterator it = parentPaths.begin(), eIt = parentPaths.end(); it != eIt; ++it )
	{
		const ScenePlug::ScenePath &parentPath = *it;
		ConstPathMatcherDataPtr branchSetData = computeBranchSet( parentPath, setName, context );
		if( !branchSetData )
		{
			continue;
		}

		Private::ConstChildNamesMapPtr mapping;
		{
			ScenePlug::PathScope pathScope( context, parentPath );
			mapping = boost::static_pointer_cast<const Private::ChildNamesMap>( mappingPlug()->getValue() );
		}

		outputSet.addPaths(
			mapping->set( { nullptr, branchSetData } ),
			parentPath
		);
	}

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

IECore::PathMatcher BranchCreator::parentPathsForSet( const IECore::InternedString &setName, const Gaffer::Context *context ) const
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
			return IECore::PathMatcher();
		}
		const auto &branchSetNames = branchSetNamesData->readable();
		if( find( branchSetNames.begin(), branchSetNames.end(), setName ) == branchSetNames.end() )
		{
			return IECore::PathMatcher();
		}
	}

	return branches( context )->parentPaths();
}

bool BranchCreator::affectsParentPathsForSet( const Gaffer::Plug *input ) const
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

void BranchCreator::hashBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashBound( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), context, inPlug(), h );
}

void BranchCreator::hashBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashTransform( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), context, inPlug(), h );
}

void BranchCreator::hashBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashAttributes( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), context, inPlug(), h );
}

void BranchCreator::hashBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashObject( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), context, inPlug(), h );
}

void BranchCreator::hashBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashChildNames( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), context, inPlug(), h );
}

void BranchCreator::hashBranchSetNames( const ScenePath &parentPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

IECore::ConstInternedStringVectorDataPtr BranchCreator::computeBranchSetNames( const ScenePath &parentPath, const Gaffer::Context *context ) const
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

void BranchCreator::hashBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

IECore::ConstPathMatcherDataPtr BranchCreator::computeBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context ) const
{
	// See comments in computeBranchSetNames.
	return nullptr;
}

void BranchCreator::hashMapping( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const ScenePlug::ScenePath parent = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	MurmurHash branchChildNamesHash;
	hashBranchChildNames( parent, ScenePath(), context, branchChildNamesHash );
	h.append( branchChildNamesHash );
	inPlug()->childNamesPlug()->hash( h );
}

IECore::ConstDataPtr BranchCreator::computeMapping( const Gaffer::Context *context ) const
{
	const ScenePlug::ScenePath parent = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	return new Private::ChildNamesMap( {
		inPlug()->childNamesPlug()->getValue(),
		computeBranchChildNames( parent, ScenePath(), context )
	} );
}

BranchCreator::ConstBranchesDataPtr BranchCreator::branches( const Gaffer::Context *context ) const
{
	ScenePlug::GlobalScope globalScope( context );
	globalScope.remove( SceneAlgo::historyIDContextName() );
	return static_pointer_cast<const BranchesData>( branchesPlug()->getValue() );
}

IECore::PathMatcher::Result BranchCreator::parentAndBranchPaths( const ScenePath &path, ScenePath &parentPath, ScenePath &branchPath ) const
{
	ConstBranchesDataPtr branchesData = branches( Context::current() );
	const PathMatcher &parentPaths = branchesData->parentPaths();

	const unsigned match = parentPaths.match( path );
	if( match & PathMatcher::ExactMatch )
	{
		parentPath = path;
		return PathMatcher::ExactMatch;
	}
	else if( match & PathMatcher::AncestorMatch )
	{
		parentPath = path;
		do {
			parentPath.pop_back();
		} while( !(parentPaths.match( parentPath ) & PathMatcher::ExactMatch) );

		Private::ConstChildNamesMapPtr mapping;
		{
			ScenePlug::PathScope pathScope( Context::current(), parentPath );
			mapping = boost::static_pointer_cast<const Private::ChildNamesMap>( mappingPlug()->getValue() );
		}

		const Private::ChildNamesMap::Input input = mapping->input( path[parentPath.size()] );
		if( input.index == 1 )
		{
			branchPath.push_back( input.name );
			branchPath.insert( branchPath.end(), path.begin() + parentPath.size() + 1, path.end() );
			return PathMatcher::AncestorMatch;
		}
		else
		{
			// Descendant comes from the primary input, rather than being part of the generated branch.
			return PathMatcher::NoMatch;
		}
	}
	else if( match & PathMatcher::DescendantMatch )
	{
		return PathMatcher::DescendantMatch;
	}

	return PathMatcher::NoMatch;
}
