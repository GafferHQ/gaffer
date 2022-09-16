//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/Rename.h"

#include "GafferScene/SceneAlgo.h"

#include "IECore/NullObject.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string/replace.hpp"
#include "boost/multi_index/hashed_index.hpp"
#include "boost/multi_index/member.hpp"
#include "boost/multi_index_container.hpp"

#include "tbb/enumerable_thread_specific.h"

/// \todo Add the latest `fmtlib` to GafferHQ/dependencies
/// and get it from there. We don't want to rely on OpenImageIO
/// here, especially not its implementation details.
#define FMT_HEADER_ONLY
#include "OpenImageIO/detail/fmt/format.h"

#include <regex>
#include <unordered_set>

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// Equivalent to `std::regex_replace`, but using `fmtlib` as the formatter
// rather than the default `\N` or `$N` formatting. We prefer `fmtlib` for
// several reasons :
//
// - It shares syntax with Python's string formatting, which is more likely
//   to already be familiar to our users.
// - It doesn't require escaping, whereas both `\N` and `$N` syntaxes require
//   escaping to sneak past StringPlug's built in substitutions.
// - It is much more flexible, providing things like padding and fill.
string regexReplace( const std::string &s, const std::regex &r, const std::string &f )
{
	// Iterator for all regex matches within `s`.
	sregex_iterator matchIt( s.begin(), s.end(), r );
	sregex_iterator matchEnd;

	if( matchIt == matchEnd )
	{
		// No matches
		return s;
	}

	ssub_match suffix;
	std::string result;
	for( ; matchIt != matchEnd; ++matchIt )
	{
		// Add any unmatched text from before this match.
		result.insert( result.end(), matchIt->prefix().first, matchIt->prefix().second );

		// Format this match using the format string provided, and
		// add it to our result.
		fmt::format_args formatArgs;
		fmt::dynamic_format_arg_store<fmt::format_context> store;
		for( const auto &subMatch : *matchIt )
		{
			store.push_back( subMatch.str() );
		}

		try
		{
			result += fmt::vformat( f, store );
		}
		catch( fmt::format_error &e )
		{
			// Augment the error with a little bit more information, to
			// give people half a chance of figuring out the problem.
			throw IECore::Exception(
				fmt::format( "Error applying replacement `{}` : {}", f, e.what() )
			);
		}

		suffix = matchIt->suffix();
	}
	// The suffix for one match is the same as the prefix for the next
	// match. So we only need to add the suffix from the last match.
	result.insert( result.end(), suffix.first, suffix.second );

	return result;
}

struct InternedStringAddressHash
{
	inline size_t operator()( const IECore::InternedString &v ) const
	{
		return boost::hash<const char *>()( v.c_str() );
	}
};

// Used to store the bidirectional mapping between input name and output
// name for renamed locations.
struct NameMapData : public IECore::Data
{

	struct Names
	{
		InternedString inputName;
		InternedString outputName;
	};

	using Map = boost::multi_index::multi_index_container<
		Names,
		boost::multi_index::indexed_by<
			// First index allows lookup using `inputName`.
			boost::multi_index::hashed_unique<boost::multi_index::member<Names, IECore::InternedString, &Names::inputName>, InternedStringAddressHash>,
			// Second index allows lookup using `outputName`.
			boost::multi_index::hashed_unique<boost::multi_index::member<Names, IECore::InternedString, &Names::outputName>, InternedStringAddressHash>
		>
	>;

	Map map;

};

IE_CORE_DECLAREPTR( NameMapData );

const ConstNameMapDataPtr g_emptyNameMap = new NameMapData;

} // namespace

//////////////////////////////////////////////////////////////////////////
// Rename implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Rename );

size_t Rename::g_firstPlugIndex = 0;

// Context scope which, when constructed from an output scope,
// modifies `scene:path` to be the appropriate input path.
struct Rename::InputScope : ScenePlug::PathScope
{

	InputScope( const Context *context, const InternedStringVectorDataPlug *inputPathPlug, const ScenePlug::ScenePath *outputPath = nullptr )
		:	PathScope( context )
	{
		if( outputPath )
		{
			setPath( outputPath );
		}
		m_inputPath = inputPathPlug->getValue();
		setPath( &m_inputPath->readable() );
	}

	const ConstInternedStringVectorDataPtr &inputPath() const
	{
		return m_inputPath;
	}

	private :

		ConstInternedStringVectorDataPtr m_inputPath;

};

Rename::Rename( const std::string &name )
	:	FilteredSceneProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "name", Plug::In, "" ) );
	addChild( new StringPlug( "deletePrefix", Plug::In, "" ) );
	addChild( new StringPlug( "deleteSuffix", Plug::In, "" ) );
	addChild( new StringPlug( "find", Plug::In, "" ) );
	addChild( new StringPlug( "replace", Plug::In, "" ) );
	addChild( new BoolPlug( "useRegularExpressions", Plug::In, false ) );
	addChild( new StringPlug( "addPrefix", Plug::In, "" ) );
	addChild( new StringPlug( "addSuffix", Plug::In, "" ) );
	addChild( new ObjectPlug( "__nameMap", Plug::Out, NullObject::defaultNullObject() ) );
	addChild( new InternedStringVectorDataPlug( "__inputPath", Plug::Out, new InternedStringVectorData() ) );

	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
}

Rename::~Rename()
{
}

Gaffer::StringPlug *Rename::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Rename::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *Rename::deletePrefixPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *Rename::deletePrefixPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *Rename::deleteSuffixPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *Rename::deleteSuffixPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *Rename::findPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *Rename::findPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *Rename::replacePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}
const Gaffer::StringPlug *Rename::replacePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::BoolPlug *Rename::useRegularExpressionsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::BoolPlug *Rename::useRegularExpressionsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 5 );
}

Gaffer::StringPlug *Rename::addPrefixPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::StringPlug *Rename::addPrefixPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

Gaffer::StringPlug *Rename::addSuffixPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 7 );
}
const Gaffer::StringPlug *Rename::addSuffixPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::ObjectPlug *Rename::nameMapPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::InternedStringVectorDataPlug *Rename::inputPathPlug() const
{
	return getChild<InternedStringVectorDataPlug>( g_firstPlugIndex + 9 );
}

void Rename::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if( affectsNameMap( input ) )
	{
		outputs.push_back( nameMapPlug() );
	}

	if( affectsInputPath( input ) )
	{
		outputs.push_back( inputPathPlug() );
	}

	if( input == inputPathPlug() || input == inPlug()->transformPlug() )
	{
		outputs.push_back( outPlug()->transformPlug() );
	}

	if( input == inputPathPlug() || input == inPlug()->boundPlug() )
	{
		outputs.push_back( outPlug()->boundPlug() );
	}

	if( input == inputPathPlug() || input == inPlug()->attributesPlug() )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}

	if( input == inputPathPlug() || input == inPlug()->objectPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}

	if(
		input == inputPathPlug() ||
		input == nameMapPlug() ||
		input == inPlug()->childNamesPlug()
	)
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}

	if(
		input == inPlug()->setPlug() ||
		input == inPlug()->childNamesPlug() ||
		input == filterPlug() ||
		input == nameMapPlug()
	)
	{
		outputs.push_back( outPlug()->setPlug() );
	}
}

void Rename::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == nameMapPlug() )
	{
		hashNameMap( context, h );
	}
	else if( output == inputPathPlug() )
	{
		hashInputPath( context, h );
	}
	else
	{
		FilteredSceneProcessor::hash( output, context, h );
	}
}

void Rename::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == nameMapPlug() )
	{
		static_cast<ObjectPlug *>( output )->setValue( computeNameMap( context ) );
	}
	else if( output == inputPathPlug() )
	{
		static_cast<InternedStringVectorDataPlug *>( output )->setValue( computeInputPath( context ) );
	}
	else
	{
		FilteredSceneProcessor::compute( output, context );
	}
}

Gaffer::ValuePlug::CachePolicy Rename::hashCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == outPlug()->setPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}

	return FilteredSceneProcessor::hashCachePolicy( output );
}

Gaffer::ValuePlug::CachePolicy Rename::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == outPlug()->setPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}

	return FilteredSceneProcessor::computeCachePolicy( output );
}

bool Rename::affectsOutputName( const Gaffer::Plug *input ) const
{
	return
		input == namePlug() ||
		input == deletePrefixPlug() ||
		input == deleteSuffixPlug() ||
		input == findPlug() ||
		input == replacePlug() ||
		input == useRegularExpressionsPlug() ||
		input == addPrefixPlug() ||
		input == addSuffixPlug()
	;
}

void Rename::hashOutputName( IECore::MurmurHash &h ) const
{
	namePlug()->hash( h );
	deletePrefixPlug()->hash( h );
	deleteSuffixPlug()->hash( h );
	findPlug()->hash( h );
	replacePlug()->hash( h );
	useRegularExpressionsPlug()->hash( h );
	addPrefixPlug()->hash( h );
	addSuffixPlug()->hash( h );
}

std::string Rename::outputName( IECore::InternedString inputName ) const
{
	string result = namePlug()->getValue();
	if( result.size() )
	{
		return result;
	}

	result = inputName.string();

	const string deletePrefix = deletePrefixPlug()->getValue();
	if( boost::starts_with( result, deletePrefix ) )
	{
		result.erase( 0, deletePrefix.size() );
	}

	const string deleteSuffix = deleteSuffixPlug()->getValue();
	if( boost::ends_with( result, deleteSuffix ) )
	{
		result.erase( result.size() - deleteSuffix.size() );
	}

	const string find = findPlug()->getValue();
	if( find.size() )
	{
		if( useRegularExpressionsPlug()->getValue() )
		{
			result = regexReplace( result, regex( find ), replacePlug()->getValue() );
		}
		else
		{
			boost::replace_all( result, find, replacePlug()->getValue() );
		}
	}

	result.insert( 0, addPrefixPlug()->getValue() );
	result.insert( result.size(), addSuffixPlug()->getValue() );

	return result.size() ? result : "invalidName";
}

bool Rename::affectsNameMap( const Gaffer::Plug *input ) const
{
	return
		input == filterPlug() ||
		input == inPlug()->childNamesPlug() ||
		affectsOutputName( input )
	;
}

void Rename::hashNameMap( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hash( nameMapPlug(), context, h );

	if( !(filterValue( context ) & PathMatcher::DescendantMatch) )
	{
		return;
	}

	ConstInternedStringVectorDataPtr inputChildNames = inPlug()->childNamesPlug()->getValue();
	ScenePlug::PathScope childScope( context );
	ScenePlug::ScenePath childPath = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	childPath.push_back( InternedString() ); // Room for child name

	bool haveRenames = false;
	IECore::MurmurHash renamesHash;
	for( const auto &childName : inputChildNames->readable() )
	{
		childPath.back() = childName;
		childScope.setPath( &childPath );
		if( filterValue( childScope.context() ) & PathMatcher::ExactMatch )
		{
			haveRenames = true;
			hashOutputName( renamesHash );
		}
		renamesHash.append( childName );
	}

	if( !haveRenames )
	{
		return;
	}

	h.append( renamesHash );
}

IECore::ConstObjectPtr Rename::computeNameMap( const Gaffer::Context *context ) const
{
	if( !(filterValue( context ) & PathMatcher::DescendantMatch) )
	{
		// No renaming here.
		return g_emptyNameMap;
	}

	// Children are possibly being renamed.

	vector<pair<InternedString, InternedString>> renames;
	std::unordered_set<InternedString> usedNames;

	ConstInternedStringVectorDataPtr inputChildNames = inPlug()->childNamesPlug()->getValue();

	ScenePlug::PathScope childScope( context );
	ScenePlug::ScenePath inputChildPath = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	inputChildPath.push_back( InternedString() ); // Room for child name

	for( const auto &inputChildName : inputChildNames->readable() )
	{
		inputChildPath.back() = inputChildName;
		childScope.setPath( &inputChildPath );
		if( filterValue( childScope.context() ) & PathMatcher::ExactMatch )
		{
			const string outputChildName = outputName( inputChildName );
			if( outputChildName != inputChildName.string() )
			{
				renames.push_back( { inputChildName, outputChildName } );
				continue;
			}
		}
		// This child not being renamed.
		usedNames.insert( inputChildName );
	}

	if( !renames.size() )
	{
		return g_emptyNameMap;
	}

	// We've renamed some things, but we need to make sure the new
	// names are unique with respect to everything that wasn't renamed.

	boost::format namePrefixSuffixFormatter( "%s%d" );

	NameMapDataPtr nameMapData = new NameMapData;
	for( auto &[inputName, outputName] : renames )
	{
		if( usedNames.find( outputName ) != usedNames.end() )
		{
			// Uniqueify the name
			string prefix;
			int suffix = IECore::StringAlgo::numericSuffix( outputName.string(), 1, &prefix );

			do
			{
				outputName = boost::str( namePrefixSuffixFormatter % prefix % suffix );
				suffix++;
			} while( usedNames.find( outputName ) != usedNames.end() );
		}
		usedNames.insert( outputName );
		nameMapData->map.insert( { inputName, outputName } );
	}

	return nameMapData;
}

bool Rename::affectsInputPath( const Gaffer::Plug *input ) const
{
	return input == nameMapPlug();
}

void Rename::hashInputPath( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const ScenePlug::ScenePath &outputPath = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	if( outputPath.empty() )
	{
		h = inputPathPlug()->defaultHash();
		return;
	}

	FilteredSceneProcessor::hash( inputPathPlug(), context, h );

	ConstInternedStringVectorDataPtr parentInputPathData;
	ScenePlug::ScenePath parentOutputPath( outputPath.begin(), outputPath.end() -1 );
	{
		InputScope inputScope( context, inputPathPlug(), &parentOutputPath );
		parentInputPathData = inputScope.inputPath();
		nameMapPlug()->hash( h );
	}

	h.append( parentInputPathData->readable() );
	h.append( outputPath.back() );
}

IECore::ConstInternedStringVectorDataPtr Rename::computeInputPath( const Gaffer::Context *context ) const
{
	const ScenePlug::ScenePath &outputPath = context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
	if( outputPath.empty() )
	{
		// Root location. Cannot be renamed.
		return inputPathPlug()->defaultValue();
	}

	ConstInternedStringVectorDataPtr parentInputPathData;
	ConstNameMapDataPtr parentNameMapData;
	ScenePlug::ScenePath parentOutputPath( outputPath.begin(), outputPath.end() -1 );
	{
		InputScope inputScope( context, inputPathPlug(), &parentOutputPath );
		parentInputPathData = inputScope.inputPath();
		parentNameMapData = boost::static_pointer_cast<const NameMapData>( nameMapPlug()->getValue() );
	}

	InternedString inputName = outputPath.back();
	auto &outputIndex = parentNameMapData->map.get<1>();
	auto it = outputIndex.find( outputPath.back() );
	if( it != outputIndex.end() )
	{
		inputName = it->inputName;
	}

	InternedStringVectorDataPtr result = new InternedStringVectorData( parentInputPathData->readable() );
	result->writable().push_back( inputName );
	return result;
}

void Rename::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	InputScope inputScope( context, inputPathPlug() );
	h = inPlug()->transformPlug()->hash();
}

Imath::M44f Rename::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	InputScope inputScope( context, inputPathPlug() );
	return inPlug()->transformPlug()->getValue();
}

void Rename::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	InputScope inputScope( context, inputPathPlug() );
	h = inPlug()->boundPlug()->hash();
}

Imath::Box3f Rename::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	InputScope inputScope( context, inputPathPlug() );
	return inPlug()->boundPlug()->getValue();
}

void Rename::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	InputScope inputScope( context, inputPathPlug() );
	h = inPlug()->attributesPlug()->hash();
}

IECore::ConstCompoundObjectPtr Rename::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	InputScope inputScope( context, inputPathPlug() );
	return inPlug()->attributesPlug()->getValue();
}

void Rename::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	InputScope inputScope( context, inputPathPlug() );
	h = inPlug()->objectPlug()->hash();
}

IECore::ConstObjectPtr Rename::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	InputScope inputScope( context, inputPathPlug() );
	return inPlug()->objectPlug()->getValue();
}

void Rename::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	InputScope inputScope( context, inputPathPlug() );

	ConstNameMapDataPtr nameMapData = boost::static_pointer_cast<const NameMapData>( nameMapPlug()->getValue() );
	if( nameMapData->map.empty() )
	{
		h = inPlug()->childNamesPlug()->hash();
		return;
	}

	FilteredSceneProcessor::hashChildNames( path, context, parent, h );
	inPlug()->childNamesPlug()->hash( h );
	nameMapPlug()->hash( h );
}

IECore::ConstInternedStringVectorDataPtr Rename::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	InputScope inputScope( context, inputPathPlug() );

	ConstNameMapDataPtr nameMapData = boost::static_pointer_cast<const NameMapData>( nameMapPlug()->getValue() );
	if( nameMapData->map.empty() )
	{
		// No children of this location have been renamed.
		return inPlug()->childNamesPlug()->getValue();
	}

	const NameMapData::Map &nameMap = nameMapData->map;
	InternedStringVectorDataPtr result = new InternedStringVectorData( inPlug()->childNamesPlug()->getValue()->readable() );
	for( auto &name : result->writable() )
	{
		auto it = nameMap.find( name );
		if( it != nameMap.end() )
		{
			name = it->outputName;
		}
	}

	return result;
}

void Rename::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	// This hash is a brute force implementation that matches `computeSet()` closely.
	// Things in it's favour :
	//
	// - If the intersection of the set and the filter is small, it visits few locations.
	// - It never visits more locations then needed.
	// - It is accurate, and doesn't lead to more computes than necessary.
	//
	// Other possibilities include :
	//
	// 1. Computing a one-off "hash of all the renamed locations" on another plug, so
	//    that the hash for any set is just the input hash plus the hash of renamed
	//    locations. This might do more work than necessary if the sets required don't
	//    intersect the filter. But in the case of many sets covering large portions of
	//    of the scene it might be a win?
	//
	// 2. Doing a "poor man's hash" where we hash the filter for the whole scene (cheap
	//    for PathFilter and SetFilter) and use `dirtyCount()` and `Context::hash()` to
	//    represent the values delivered by `namePlug()`. This would be fast, but would
	//    potentially expose us to a lot of unnecessary recomputes.
	//
	// We currently anticipate the number of locations hit by a single Rename node to
	// be relatively small, so hopefully the current strategy is reasonable.

	const MurmurHash inputSetHash = inPlug()->setPlug()->hash();
	ConstPathMatcherDataPtr inputSetData = inPlug()->setPlug()->getValue( &inputSetHash );

	using ThreadLocalHash = tbb::enumerable_thread_specific<IECore::MurmurHash>;

	struct LocationProcessor
	{

		LocationProcessor( const Rename *rename, const PathMatcher &inputSet, ThreadLocalHash &hash )
			:	m_rename( rename ), m_parent( nullptr ), m_inputSet( inputSet ), m_hash( hash )
		{
		}

		LocationProcessor( const LocationProcessor &parent )
			:	m_rename( parent.m_rename ), m_parent( &parent ), m_inputSet( parent.m_inputSet ), m_hash( parent.m_hash )
		{
		}

		bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path )
		{
			const int setMatch = m_inputSet.match( path );
			if( !( setMatch & ( PathMatcher::ExactMatch | PathMatcher::DescendantMatch ) ) )
			{
				return false;
			}

			const int filterMatch = m_rename->filterValue( Context::current() );
			if( m_parent && (filterMatch & PathMatcher::ExactMatch) )
			{
				const NameMapData::Map &nameMap = m_parent->m_nameMap->map;
				auto it = nameMap.find( path.back() );
				if( it != nameMap.end() )
				{
					MurmurHash renameHash;
					renameHash.append( path );
					renameHash.append( it->outputName );
					MurmurHash &hash = m_hash.local();
					hash = MurmurHash( hash.h1() + renameHash.h1(), hash.h2() + renameHash.h2() );
				}
			}

			if( filterMatch & PathMatcher::DescendantMatch )
			{
				m_nameMap = boost::static_pointer_cast<const NameMapData>( m_rename->nameMapPlug()->getValue() );
				return true;
			}
			else
			{
				return false;
			}
		}

		private :

			const Rename *m_rename;
			const LocationProcessor *m_parent;
			const PathMatcher &m_inputSet;
			ThreadLocalHash &m_hash;
			ConstNameMapDataPtr m_nameMap;

	};

	ScenePlug::GlobalScope globalScope( context );
	ThreadLocalHash threadLocalHash;
	LocationProcessor processor( this, inputSetData->readable(), threadLocalHash );
	SceneAlgo::parallelProcessLocations( inPlug(), processor );

	const MurmurHash renamesHash = threadLocalHash.combine(
		[] ( const MurmurHash &a, const MurmurHash &b ) {
			// See SceneAlgo's ThreadablePathHashAccumulator for further discussion of
			// this "sum of hashes" strategy for deterministic parallel hashing.
			return MurmurHash( a.h1() + b.h1(), a.h2() + b.h2() );
		}
	);

	if( renamesHash != MurmurHash() )
	{
		FilteredSceneProcessor::hashSet( setName, context, parent, h );
		h.append( inputSetHash );
		h.append( renamesHash );
	}
	else
	{
		h = inputSetHash;
	}
}

IECore::ConstPathMatcherDataPtr Rename::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstPathMatcherDataPtr inputSetData = inPlug()->setPlug()->getValue();
	const PathMatcher &inputSet = inputSetData->readable();
	if( inputSet.isEmpty() )
	{
		return inputSetData;
	}

	// Thread-local PathMatcher so we can build an output set in a thread-safe
	// manner.
	/// \todo If `parallelProcessLocations()` supported a `gatherChildren()`
	/// method, we could build a single set recursively, passing subtrees from
	/// child to parent.
	using ThreadLocalSet = tbb::enumerable_thread_specific<IECore::PathMatcher>;

	struct LocationProcessor
	{

		LocationProcessor( const Rename *rename, const PathMatcher &inputSet, ThreadLocalSet &outputSet )
			:	m_rename( rename ), m_parent( nullptr ), m_inputSet( inputSet ), m_outputSet( outputSet )
		{
		}

		// Constructor used for child locations, allowing us to inherit stuff
		// from the parent processor.
		LocationProcessor( const LocationProcessor &parent )
			:	m_rename( parent.m_rename ), m_parent( &parent ), m_inputSet( parent.m_inputSet ), m_outputSet( parent.m_outputSet )
		{
		}

		bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path )
		{
			const int setMatch = m_inputSet.match( path );
			if( !( setMatch & ( PathMatcher::ExactMatch | PathMatcher::DescendantMatch ) ) )
			{
				// Not in set, and no descendants in set. Terminate recursion.
				return false;
			}

			// Get output path for this location.

			const int filterMatch = m_rename->filterValue( Context::current() );

			if( m_parent )
			{
				m_outputPath = m_parent->m_outputPath;
				InternedString name = path.back();
				if( filterMatch & PathMatcher::ExactMatch )
				{
					const NameMapData::Map &nameMap = m_parent->m_nameMap->map;
					auto it = nameMap.find( name );
					if( it != nameMap.end() )
					{
						name = it->outputName;
					}
				}
				m_outputPath.push_back( name );
			}

			// Add to set if necessary and deal with recursion.

			if( filterMatch & PathMatcher::DescendantMatch )
			{
				if( setMatch & PathMatcher::ExactMatch )
				{
					m_outputSet.local().addPath( m_outputPath );
				}
				// Get child map ready for use in our children, and return
				// `true` to continue recursion.
				m_nameMap = boost::static_pointer_cast<const NameMapData>( m_rename->nameMapPlug()->getValue() );
				return true;
			}
			else
			{
				// No descendants being renamed. We can directly reference
				// the entire subtree of the set from this point down, and
				// have no need to recurse any further.
				m_outputSet.local().addPaths( m_inputSet.subTree( path ), m_outputPath );
				return false;
			}
		}

		private :

			const Rename *m_rename;
			const LocationProcessor *m_parent;
			const PathMatcher &m_inputSet;
			ThreadLocalSet &m_outputSet;
			ScenePlug::ScenePath m_outputPath;
			ConstNameMapDataPtr m_nameMap;

	};

	ScenePlug::GlobalScope globalScope( context );
	ThreadLocalSet outputSets;
	LocationProcessor processor( this, inputSet, outputSets );
	SceneAlgo::parallelProcessLocations( inPlug(), processor );

	return new PathMatcherData(
		outputSets.combine(
			[] ( const PathMatcher &a, const PathMatcher &b ) {
				PathMatcher c = a;
				c.addPaths( b );
				return c;
			}
		)
	);
}
