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
// BranchCreator
//////////////////////////////////////////////////////////////////////////


GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( BranchCreator );

size_t BranchCreator::g_firstPlugIndex = 0;

static InternedString g_childNamesKey( "__BranchCreatorChildNames" );
static InternedString g_forwardMappingKey( "__BranchCreatorForwardMappings" );

BranchCreator::BranchCreator( const std::string &name )
	:	FilteredSceneProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "parent" ) );

	addChild( new PathMatcherDataPlug( "__filteredPaths", Gaffer::Plug::In, new IECore::PathMatcherData(), Plug::Default & ~Plug::Serialisable ) );
	addChild( new PathMatcherDataPlug( "__parentPaths", Gaffer::Plug::Out, new IECore::PathMatcherData() ) );

	addChild( new ObjectPlug( "__mapping", Gaffer::Plug::Out, IECore::NullObject::defaultNullObject() ) );

	FilterResultsPtr filterResults = new FilterResults( "__filterResults" );
	addChild( filterResults );
	filterResults->scenePlug()->setInput( inPlug() );
	filterResults->filterPlug()->setInput( filterPlug() );
	filteredPathsPlug()->setInput( filterResults->outPlug() );

	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
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

Gaffer::PathMatcherDataPlug *BranchCreator::filteredPathsPlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::PathMatcherDataPlug *BranchCreator::filteredPathsPlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 1 );
}

Gaffer::PathMatcherDataPlug *BranchCreator::parentPathsPlug()
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::PathMatcherDataPlug *BranchCreator::parentPathsPlug() const
{
	return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 2 );
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

	if( input == parentPlug() || input == filteredPathsPlug() )
	{
		outputs.push_back( parentPathsPlug() );
	}

	if( input == inPlug()->childNamesPlug() || affectsBranchChildNames( input ) )
	{
		outputs.push_back( mappingPlug() );
	}

	if(
		input == parentPathsPlug() ||
		input == mappingPlug() ||
		input == inPlug()->boundPlug() ||
		affectsBranchBound( input )
	)
	{
		outputs.push_back( outPlug()->boundPlug() );
	}

	if(
		input == parentPathsPlug() ||
		input == mappingPlug() ||
		input == inPlug()->transformPlug() ||
		affectsBranchTransform( input )
	)
	{
		outputs.push_back( outPlug()->transformPlug() );
	}

	if(
		input == parentPathsPlug() ||
		input == mappingPlug() ||
		input == inPlug()->attributesPlug() ||
		affectsBranchAttributes( input )
	)
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}

	if(
		input == parentPathsPlug() ||
		input == mappingPlug() ||
		input == inPlug()->objectPlug() ||
		affectsBranchObject( input )
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}

	if(
		input == parentPathsPlug() ||
		input == mappingPlug() ||
		input == inPlug()->childNamesPlug() ||
		affectsBranchChildNames( input )
	)
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}

	if(
		input == parentPathsPlug() ||
		input == inPlug()->setNamesPlug() ||
		affectsBranchSetNames( input )
	)
	{
		outputs.push_back( outPlug()->setNamesPlug() );
	}

	if(
		input == parentPathsPlug() ||
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

	if( output == parentPathsPlug() )
	{
		ScenePlug::GlobalScope globalScope( context );
		filteredPathsPlug()->hash( h );

		if( !filterPlug()->getInput() )
		{
			const auto parent = parentPlugPath();
			if( parent )
			{
				h.append( parent->data(), parent->size() );
				h.append( (uint64_t)parent->size() );
			}
		}
	}
	else if( output == mappingPlug() )
	{
		hashMapping( context, h );
	}
}

void BranchCreator::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == parentPathsPlug() )
	{
		ScenePlug::GlobalScope globalScope( context );
		PathMatcherDataPtr parentPaths = new PathMatcherData;
		parentPaths->writable() = filteredPathsPlug()->getValue()->readable();

		if( !filterPlug()->getInput() )
		{
			const auto parent = parentPlugPath();
			if( parent )
			{
				parentPaths->writable().addPath( *parent );
			}
		}
		static_cast<Gaffer::PathMatcherDataPlug *>( output )->setValue( parentPaths );
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
		h.append( hashOfTransformedChildBounds( path, outPlug() ) );
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
		result.extendBy( unionOfTransformedChildBounds( path, outPlug() ) );
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
	ConstPathMatcherDataPtr parentPathsData = parentPathsPlug()->getValue();
	const PathMatcher &parentPaths = parentPathsData->readable();

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
	ConstPathMatcherDataPtr parentPathsData = parentPathsPlug()->getValue();
	const PathMatcher &parentPaths = parentPathsData->readable();

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
	ConstPathMatcherDataPtr parentPathsData = parentPathsPlug()->getValue();
	const PathMatcher &parentPaths = parentPathsData->readable();

	if( parentPaths.isEmpty() )
	{
		h = inPlug()->setPlug()->hash();
	}

	FilteredSceneProcessor::hashSet( setName, context, parent, h );
	h.append( inPlug()->setHash( setName ) );

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
	}
}

IECore::ConstPathMatcherDataPtr BranchCreator::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstPathMatcherDataPtr parentPathsData = parentPathsPlug()->getValue();
	const PathMatcher &parentPaths = parentPathsData->readable();

	ConstPathMatcherDataPtr inputSetData = inPlug()->set( setName );
	if( parentPaths.isEmpty() )
	{
		return inputSetData;
	}

	PathMatcherDataPtr outputSetData = inputSetData->copy();
	PathMatcher &outputSet = outputSetData->writable();

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

IECore::PathMatcher::Result BranchCreator::parentAndBranchPaths( const ScenePath &path, ScenePath &parentPath, ScenePath &branchPath ) const
{
	ConstPathMatcherDataPtr parentPathsData = parentPathsPlug()->getValue();
	const PathMatcher &parentPaths = parentPathsData->readable();

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
