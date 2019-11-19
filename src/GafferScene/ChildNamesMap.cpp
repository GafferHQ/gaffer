//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Private/ChildNamesMap.h"

#include "IECore/StringAlgo.h"

#include "boost/format.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/regex.hpp"

#include <unordered_set>

using namespace std;
using namespace IECore;

namespace IECore
{

/// \todo Move to Cortex. This `hash_value()` implementation differs from the existing
/// `std::hash` implementation that Cortex has in that it hashes the pointer and not
/// the string contents. I don't see any reason not to make `std::hash` use the faster
/// option as well.
/// Override `boost::hash_value()` to allow InternedString to be used
/// with `hashed_index`.
size_t hash_value( const IECore::InternedString &v )
{
	return boost::hash<const char *>()( v.c_str() );
}

} // namespace IECore

namespace GafferScene
{

namespace Private
{

// Override `boost::hash_value()` to allow Input to be used
/// with `hashed_index`.
size_t hash_value( const ChildNamesMap::Input &v )
{
	size_t s = 0;
	boost::hash_combine( s, v.name );
	boost::hash_combine( s, v.index );
	return s;
}

ChildNamesMap::ChildNamesMap( const std::vector<IECore::ConstInternedStringVectorDataPtr> &inputChildNames )
	:	m_childNames( new InternedStringVectorData() )
{
	vector<InternedString> &outputChildNames = m_childNames->writable();
	boost::format namePrefixSuffixFormatter( "%s%d" );

	unordered_set<InternedString> allNames;
	size_t index = 0;
	for( const auto &childNamesData : inputChildNames )
	{
		for( const auto &inputChildName : childNamesData->readable() )
		{
			InternedString outputChildName = inputChildName;
			if( allNames.find( inputChildName ) != allNames.end() )
			{
				// uniqueify the name
				string prefix;
				int suffix = IECore::StringAlgo::numericSuffix( inputChildName.string(), 1, &prefix );

				do
				{
					outputChildName = boost::str( namePrefixSuffixFormatter % prefix % suffix );
					suffix++;
				} while( allNames.find( outputChildName ) != allNames.end() );
			}

			allNames.insert( outputChildName );
			outputChildNames.push_back( outputChildName );

			m_map.insert( { { inputChildName, index }, outputChildName } );
		}
		index++;
	}
}

const IECore::InternedStringVectorData *ChildNamesMap::outputChildNames() const
{
	return m_childNames.get();
}

const ChildNamesMap::Input &ChildNamesMap::input( IECore::InternedString outputName ) const
{
	auto it = m_map.find( outputName );
	if( it == m_map.end() )
	{
		throw IECore::Exception(
			boost::str( boost::format( "Invalid child name \"%1%\"" ) % outputName )
		);
	}

	return it->input;
}

IECore::PathMatcher ChildNamesMap::set( const std::vector<IECore::ConstPathMatcherDataPtr> &inputSets ) const
{
	IECore::PathMatcher result;
	size_t inputIndex = 0;
	for( const auto &inputSetData : inputSets )
	{
		if( inputSetData )
		{
			const PathMatcher &inputSet = inputSetData->readable();
			// We want our outputSet to reference the data within inputSet rather
			// than do an expensive copy. But we may need to rename the children of
			// the root location according to m_map. Here we do that by taking subtrees
			// of the input and adding them to our output under a renamed prefix.
			for( PathMatcher::RawIterator pIt = inputSet.begin(), peIt = inputSet.end(); pIt != peIt; ++pIt )
			{
				const vector<InternedString> &inputPath = *pIt;
				if( !inputPath.size() )
				{
					// Skip root.
					continue;
				}
				assert( inputPath.size() == 1 );

				const auto &inputMap = m_map.get<1>();
				auto it = inputMap.find( Input{ inputPath[0], inputIndex } );
				if( it != inputMap.end() )
				{
					result.addPaths( inputSet.subTree( inputPath ), { it->output } );
				}
				else
				{
					// The set contains an invalid path that is not present in
					// the scene (as defined by the `inputChildNames` passed to our
					// constructor). We could throw an error, but since it's currently
					// relatively easy for a user to make an invalid set via
					// `Set::pathsPlug()`, we do the more helpful thing and just omit
					// the invalid path from the output set.
				}

				pIt.prune(); // We only want to visit the first level
			}
		}
	 	inputIndex++;
	}

	return result;
}

} // namespace Private

} // namespace GafferScene
