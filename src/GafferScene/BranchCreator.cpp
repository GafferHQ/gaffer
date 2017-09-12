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

#include "boost/algorithm/string/predicate.hpp"

#include "Gaffer/Context.h"
#include "Gaffer/StringAlgo.h"
#include "Gaffer/StringPlug.h"

#include "GafferScene/PathMatcherData.h"
#include "GafferScene/BranchCreator.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( BranchCreator );

size_t BranchCreator::g_firstPlugIndex = 0;

static InternedString g_childNamesKey( "__BranchCreatorChildNames" );
static InternedString g_parentKey( "__BranchCreatorParent" );
static InternedString g_forwardMappingKey( "__BranchCreatorForwardMappings" );

BranchCreator::BranchCreator( const std::string &name )
	:	SceneProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "parent" ) );
	addChild( new Gaffer::ObjectPlug( "__mapping", Gaffer::Plug::Out, new CompoundData() ) );

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

Gaffer::ObjectPlug *BranchCreator::mappingPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::ObjectPlug *BranchCreator::mappingPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 1 );
}

void BranchCreator::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );

	if( input->parent<ScenePlug>() == inPlug() )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
	else if( input == parentPlug() )
	{
		outputs.push_back( mappingPlug() );
	}
	else if( input == mappingPlug() )
	{
		outputs.push_back( outPlug()->boundPlug() );
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( outPlug()->attributesPlug() );
		outputs.push_back( outPlug()->objectPlug() );
		outputs.push_back( outPlug()->childNamesPlug() );
		// Globals plug deliberately omitted - because
		// it's just a pass-through connection.
		outputs.push_back( outPlug()->setNamesPlug() );
		outputs.push_back( outPlug()->setPlug() );
	}
}

void BranchCreator::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneProcessor::hash( output, context, h );

	if( output == mappingPlug() )
	{
		hashMapping( context, h );
	}
}

void BranchCreator::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == mappingPlug() )
	{
		static_cast<Gaffer::ObjectPlug *>( output )->setValue( computeMapping( context ) );
		return;
	}

	SceneProcessor::compute( output, context );
}

void BranchCreator::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstCompoundDataPtr mapping = boost::static_pointer_cast<const CompoundData>( mappingPlug()->getValue() );
	ScenePath parentPath, branchPath;
	Filter::Result parentMatch = parentAndBranchPaths( mapping.get(), path, parentPath, branchPath );

	if( parentMatch == Filter::AncestorMatch )
	{
		hashBranchBound( parentPath, branchPath, context, h );
	}
	else if( parentMatch == Filter::ExactMatch || parentMatch == Filter::DescendantMatch )
	{
		SceneProcessor::hashBound( path, context, parent, h );
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
	ConstCompoundDataPtr mapping = boost::static_pointer_cast<const CompoundData>( mappingPlug()->getValue() );
	ScenePath parentPath, branchPath;
	Filter::Result parentMatch = parentAndBranchPaths( mapping.get(), path, parentPath, branchPath );

	if( parentMatch == Filter::AncestorMatch )
	{
		return computeBranchBound( parentPath, branchPath, context );
	}
	else if( parentMatch == Filter::ExactMatch || parentMatch == Filter::DescendantMatch )
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
	ConstCompoundDataPtr mapping = boost::static_pointer_cast<const CompoundData>( mappingPlug()->getValue() );
	ScenePath parentPath, branchPath;
	Filter::Result parentMatch = parentAndBranchPaths( mapping.get(), path, parentPath, branchPath );

	if( parentMatch == Filter::AncestorMatch )
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
	ConstCompoundDataPtr mapping = boost::static_pointer_cast<const CompoundData>( mappingPlug()->getValue() );
	ScenePath parentPath, branchPath;
	Filter::Result parentMatch = parentAndBranchPaths( mapping.get(), path, parentPath, branchPath );

	if( parentMatch == Filter::AncestorMatch )
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
	ConstCompoundDataPtr mapping = boost::static_pointer_cast<const CompoundData>( mappingPlug()->getValue() );
	ScenePath parentPath, branchPath;
	Filter::Result parentMatch = parentAndBranchPaths( mapping.get(), path, parentPath, branchPath );

	if( parentMatch == Filter::AncestorMatch )
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
	ConstCompoundDataPtr mapping = boost::static_pointer_cast<const CompoundData>( mappingPlug()->getValue() );
	ScenePath parentPath, branchPath;
	Filter::Result parentMatch = parentAndBranchPaths( mapping.get(), path, parentPath, branchPath );

	if( parentMatch == Filter::AncestorMatch )
	{
		return computeBranchAttributes( parentPath, branchPath, context );
	}
	else
	{
		return inPlug()->attributesPlug()->getValue();
	}
}

void BranchCreator::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstCompoundDataPtr mapping = boost::static_pointer_cast<const CompoundData>( mappingPlug()->getValue() );
	ScenePath parentPath, branchPath;
	Filter::Result parentMatch = parentAndBranchPaths( mapping.get(), path, parentPath, branchPath );

	if( parentMatch == Filter::AncestorMatch )
	{
		hashBranchObject( parentPath, branchPath, context, h );
	}
	else
	{
		h = inPlug()->objectPlug()->hash();
	}
}

IECore::ConstObjectPtr BranchCreator::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstCompoundDataPtr mapping = boost::static_pointer_cast<const CompoundData>( mappingPlug()->getValue() );
	ScenePath parentPath, branchPath;
	Filter::Result parentMatch = parentAndBranchPaths( mapping.get(), path, parentPath, branchPath );

	if( parentMatch == Filter::AncestorMatch )
	{
		return computeBranchObject( parentPath, branchPath, context );
	}
	else
	{
		return inPlug()->objectPlug()->getValue();
	}
}

void BranchCreator::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstCompoundDataPtr mapping = boost::static_pointer_cast<const CompoundData>( mappingPlug()->getValue() );
	ScenePath parentPath, branchPath;
	Filter::Result parentMatch = parentAndBranchPaths( mapping.get(), path, parentPath, branchPath );

	if( parentMatch == Filter::AncestorMatch )
	{
		hashBranchChildNames( parentPath, branchPath, context, h );
	}
	else if( parentMatch == Filter::ExactMatch )
	{
		h = mapping->member<InternedStringVectorData>( g_childNamesKey )->Object::hash();
	}
	else
	{
		h = inPlug()->childNamesPlug()->hash();
	}
}

IECore::ConstInternedStringVectorDataPtr BranchCreator::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstCompoundDataPtr mapping = boost::static_pointer_cast<const CompoundData>( mappingPlug()->getValue() );
	ScenePath parentPath, branchPath;
	Filter::Result parentMatch = parentAndBranchPaths( mapping.get(), path, parentPath, branchPath );

	if( parentMatch == Filter::AncestorMatch )
	{
		return computeBranchChildNames( parentPath, branchPath, context );
	}
	else if( parentMatch == Filter::ExactMatch )
	{
		return mapping->member<InternedStringVectorData>( g_childNamesKey );
	}
	else
	{
		return inPlug()->childNamesPlug()->getValue();
	}
}

void BranchCreator::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstCompoundDataPtr mapping = boost::static_pointer_cast<const CompoundData>( mappingPlug()->getValue() );
	if( !mapping->readable().size() )
	{
		h = inPlug()->setNamesPlug()->hash();
		return;
	}

	MurmurHash branchSetNamesHash;
	hashBranchSetNames( mapping->member<InternedStringVectorData>( g_parentKey )->readable(), context, branchSetNamesHash );
	if( branchSetNamesHash == MurmurHash() )
	{
		h = inPlug()->setNamesPlug()->hash();
		return;
	}

	SceneProcessor::hashSetNames( context, parent, h );
	inPlug()->setNamesPlug()->hash( h );
	h.append( branchSetNamesHash );
}

IECore::ConstInternedStringVectorDataPtr BranchCreator::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstInternedStringVectorDataPtr inputSetNamesData = inPlug()->setNamesPlug()->getValue();

	ConstCompoundDataPtr mapping = boost::static_pointer_cast<const CompoundData>( mappingPlug()->getValue() );
	if( !mapping->readable().size() )
	{
		return inputSetNamesData;
	}

	ConstInternedStringVectorDataPtr branchSetNamesData = computeBranchSetNames( mapping->member<InternedStringVectorData>( g_parentKey )->readable(), context );
	if( !branchSetNamesData )
	{
		return inputSetNamesData;
	}

	const vector<InternedString> &branchSetNames = branchSetNamesData->readable();
	if( !branchSetNames.size() )
	{
		return inputSetNamesData;
	}

	InternedStringVectorDataPtr resultData = inputSetNamesData->copy();
	vector<InternedString> &result = resultData->writable();

	// This naive approach to merging set names preserves the order of the incoming names,
	// but at the expense of using linear search. We assume that the number of sets is small
	// enough and the InternedString comparison fast enough that this is OK.
	for( vector<InternedString>::const_iterator it = branchSetNames.begin(), eIt = branchSetNames.end(); it != eIt; ++it )
	{
		if( std::find( result.begin(), result.end(), *it ) == result.end() )
		{
			result.push_back( *it );
		}
	}

	return resultData;
}

void BranchCreator::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstCompoundDataPtr mapping;
	{
		ScenePlug::GlobalScope s( context );
		mapping = boost::static_pointer_cast<const CompoundData>( mappingPlug()->getValue() );
	}
	if( !mapping->readable().size() )
	{
		h = inPlug()->setPlug()->hash();
		return;
	}

	MurmurHash branchSetHash;
	hashBranchSet( mapping->member<InternedStringVectorData>( g_parentKey )->readable(), setName, context, branchSetHash );
	if( branchSetHash == MurmurHash() )
	{
		h = inPlug()->setPlug()->hash();
		return;
	}

	SceneProcessor::hashSet( setName, context, parent, h );
	h.append( inPlug()->setHash( setName ) );
	mapping->hash( h );
	h.append( branchSetHash );
}

GafferScene::ConstPathMatcherDataPtr BranchCreator::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstPathMatcherDataPtr inputSetData = inPlug()->set( setName );

	ConstCompoundDataPtr mapping;
	{
		ScenePlug::GlobalScope s( context );
		mapping = boost::static_pointer_cast<const CompoundData>( mappingPlug()->getValue() );
	}
	if( !mapping->readable().size() )
	{
		return inputSetData;
	}

	ScenePlug::ScenePath parentPath = mapping->member<InternedStringVectorData>( g_parentKey )->readable();

	ConstPathMatcherDataPtr branchSetData = computeBranchSet( parentPath, setName, context );
	if( !branchSetData )
	{
		return inputSetData;
	}

	const PathMatcher &branchSet = branchSetData->readable();
	if( branchSet.isEmpty() )
	{
		return inputSetData;
	}

	const CompoundData *forwardMapping = mapping->member<CompoundData>( g_forwardMappingKey );

	PathMatcherDataPtr outputSetData = inputSetData->copy();
	PathMatcher &outputSet = outputSetData->writable();

	vector<InternedString> outputPrefix( parentPath );
	for( PathMatcher::RawIterator pIt = branchSet.begin(), peIt = branchSet.end(); pIt != peIt; ++pIt )
	{
		const ScenePlug::ScenePath &branchPath = *pIt;
		if( !branchPath.size() )
		{
			continue; // Skip root
		}
		assert( branchPath.size() == 1 );

		const InternedStringData *outputName = forwardMapping->member<InternedStringData>( branchPath[0], /* throwExceptions = */ true );

		outputPrefix.resize( parentPath.size() + 1 );
		outputPrefix.back() = outputName->readable();
		outputSet.addPaths( branchSet.subTree( *pIt ), outputPrefix );

		pIt.prune(); // We only want to visit the first level
	}

	return outputSetData;
}

void BranchCreator::hashBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashBound( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), context, inPlug(), h );
}

void BranchCreator::hashBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashTransform( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), context, inPlug(), h );
}

void BranchCreator::hashBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashAttributes( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), context, inPlug(), h );
}

void BranchCreator::hashBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashObject( context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName ), context, inPlug(), h );
}

void BranchCreator::hashBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const InternedStringVectorData *fullPathData = context->get<InternedStringVectorData>( ScenePlug::scenePathContextName, NULL );
	if( fullPathData )
	{
		// In the common case, the full path is in the context already (and we just decomposed it
		// into parentPath and branchPath for the convenience of derived classes).
		SceneProcessor::hashChildNames( fullPathData->readable(), context, inPlug(), h );
	}
	else
	{
		// In the rare case that we're being called from from our own sets computation
		// via hashMapping(), the full path isn't in the context, so we need to
		// construct it ourselves.
		ScenePath fullPath( parentPath );
		fullPath.insert( fullPath.end(), branchPath.begin(), branchPath.end() );
		SceneProcessor::hashChildNames( fullPath, context, inPlug(), h );
	}
}

void BranchCreator::hashBranchSetNames( const ScenePath &parentPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

IECore::ConstInternedStringVectorDataPtr BranchCreator::computeBranchSetNames( const ScenePath &parentPath, const Gaffer::Context *context ) const
{
	// It's OK to return NULL, because the value returned from this method
	// isn't used as the result of a compute(), and won't be stored on a plug.
	// For the same reason, it's ok for hashBranchSetNames() to do nothing by default
	return NULL;
}

void BranchCreator::hashBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

GafferScene::ConstPathMatcherDataPtr BranchCreator::computeBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context ) const
{
	// See comments in computeBranchSetNames.
	return NULL;
}

void BranchCreator::hashMapping( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	string parentAsString = parentPlug()->getValue();
	h.append( parentAsString );

	ScenePlug::ScenePath parent;
	ScenePlug::stringToPath( parentAsString, parent );

	h.append( inPlug()->childNamesHash( parent ) );

	MurmurHash branchChildNamesHash;
	hashBranchChildNames( parent, ScenePath(), context, branchChildNamesHash );
	h.append( branchChildNamesHash );
}

/// \todo This mapping is very similar to the one created by the Group node. Perhaps
/// some generalisation of the two could form the basis for a nice unified HierarchyProcessor?
/// In this case I think we would have a custom mapping class rather than just pass around
/// CompoundData, and then parentAndBranchPaths() (or the future version of it) could be a method
/// on the mapping object.
IECore::ConstCompoundDataPtr BranchCreator::computeMapping( const Gaffer::Context *context ) const
{
	// get the parent. currently this is simply retrieving the value of parentPlug(),
	// but if we wanted to support multiple parents in future, here we would find the
	// parent appropriate to the current "scene:path" context entry.

	/// \todo We should introduce a plug type which stores its values as a ScenePath directly.
	ScenePlug::ScenePath parent;
	string parentAsString = parentPlug()->getValue();
	if( parentAsString.empty() )
	{
		// no parent specified so no mapping needed
		return static_cast<const CompoundData *>( mappingPlug()->defaultValue() );
	}
	ScenePlug::stringToPath( parentAsString, parent );

	// see if we're interested in creating children or not. if we're not
	// we can early out. no innuendo intended.

	ConstInternedStringVectorDataPtr branchChildNamesData = computeBranchChildNames( parent, ScenePath(), context );
	if( !branchChildNamesData->readable().size() )
	{
		return static_cast<const CompoundData *>( mappingPlug()->defaultValue() );
	}

	// create our result. in future it might be useful to create our datatype for this,
	// but for now we're just packing everything into a CompoundData.

	CompoundDataPtr result = new CompoundData;
	result->writable()[g_parentKey] = new InternedStringVectorData( parent );

	CompoundDataPtr forwardMapping = new CompoundData;
	result->writable()[g_forwardMappingKey] = forwardMapping;

	// calculate the child names for the result. this is the full list of child names
	// immediately below the parent. we need to be careful to ensure that we rename any
	// branch names which conflict with existing children of the parent.

	ConstInternedStringVectorDataPtr inChildNamesData = inPlug()->childNames( parent );
	InternedStringVectorDataPtr childNamesData = new InternedStringVectorData();

	const vector<InternedString> &inChildNames = inChildNamesData->readable();
	const vector<InternedString> &branchChildNames = branchChildNamesData->readable();
	vector<InternedString> &childNames = childNamesData->writable();

	result->writable()[g_childNamesKey] = childNamesData;

	set<InternedString> allNames;
	for( vector<InternedString>::const_iterator it = inChildNames.begin(); it != inChildNames.end(); ++it )
	{
		allNames.insert( *it );
		childNames.push_back( *it );
	}

	boost::format namePrefixSuffixFormatter( "%s%d" );

	for( vector<InternedString>::const_iterator it = branchChildNames.begin(); it != branchChildNames.end(); ++it )
	{
		InternedString name = *it;
		if( allNames.find( name ) != allNames.end() )
		{
			// uniqueify the name
			string prefix;
			int suffix = StringAlgo::numericSuffix( name, 1, &prefix );

			do
			{
				name = boost::str( namePrefixSuffixFormatter % prefix % suffix );
				suffix++;
			} while( allNames.find( name ) != allNames.end() );
		}

		allNames.insert( name );
		childNames.push_back( name );

		result->writable()[name] = new InternedStringData( *it );
		forwardMapping->writable()[*it] = new InternedStringData( name );
	}

	return result;
}

Filter::Result BranchCreator::parentAndBranchPaths( const IECore::CompoundData *mapping, const ScenePath &path, ScenePath &parentPath, ScenePath &branchPath ) const
{
	if( !mapping->readable().size() )
	{
		return Filter::NoMatch;
	}

	const ScenePath &parent = mapping->member<InternedStringVectorData>( g_parentKey )->readable();

	ScenePath::const_iterator parentIterator, parentIteratorEnd, pathIterator, pathIteratorEnd;

	for(
		parentIterator = parent.begin(), parentIteratorEnd = parent.end(),
		pathIterator = path.begin(), pathIteratorEnd = path.end();
		parentIterator != parentIteratorEnd && pathIterator != pathIteratorEnd;
		parentIterator++, pathIterator++
	)
	{
		if( *parentIterator != *pathIterator )
		{
			return Filter::NoMatch;
		}
	}

	if( pathIterator == pathIteratorEnd )
	{
		// path is ancestor of parent, or parent itself
		parentPath = parent;
		return parentIterator == parentIteratorEnd ? Filter::ExactMatch : Filter::DescendantMatch;
	}

	// path is descendant of parent

	const InternedStringData *branchName = mapping->member<InternedStringData>( *pathIterator );
	if( !branchName )
	{
		// descendant comes from the input, rather than being part of the generated branch
		return Filter::NoMatch;
	}

	// somewhere on the new branch

	parentPath = parent;
	branchPath.push_back( branchName->readable() );
	branchPath.insert( branchPath.end(), ++pathIterator, pathIteratorEnd );

	return Filter::AncestorMatch;
}
