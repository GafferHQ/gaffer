//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_SHUFFLEPLUG_INL
#define GAFFER_SHUFFLEPLUG_INL

#include "Gaffer/Node.h"
#include "Gaffer/PlugAlgo.h"

#include <unordered_set>

//////////////////////////////////////////////////////////////////////////
// Utility methods need by ShufflesPlug::shuffle()
//////////////////////////////////////////////////////////////////////////

namespace
{

const IECore::InternedString g_sourceVariable( "source" );

struct ShuffleValues
{
	bool enabled;
	bool deleteSource;
	std::string sourcePattern;
};

} // namespace

namespace Gaffer
{

template<typename T>
T ShufflesPlug::shuffle( const T &sourceContainer ) const
{
	T destinationContainer;

	size_t i = 0;
	std::vector<::ShuffleValues> shuffleValues( this->children().size() );
	for( auto &plug : ShufflePlug::Range( *this ) )
	{
		shuffleValues[i].enabled = plug->enabledPlug()->getValue();
		shuffleValues[i].deleteSource = plug->deleteSourcePlug()->getValue();
		shuffleValues[i].sourcePattern = plug->sourcePlug()->getValue();
		++i;
	}

	std::unordered_set<std::string> toDelete;
	std::unordered_set<std::string> newDestinations;

	Gaffer::Context::EditableScope scope( Gaffer::Context::current() );

	for( const auto &sourceData : sourceContainer )
	{
		// Quick way to get a string from a key that could be std::string or IECore::InternedString
		const std::string &source = sourceData.first;
		scope.set<std::string>( g_sourceVariable, &source );

		i = 0;
		bool deleteSource = false;

		for( auto &plug : ShufflePlug::Range( *this ) )
		{
			auto &shuffle = shuffleValues[i++];
			if( shuffle.enabled && !shuffle.sourcePattern.empty() )
			{
				// note we've disabled substitutions on the destination plug, so we're performing
				// both the $source substitution and any other context substitutions here.
				const std::string destination = scope.context()->substitute( plug->destinationPlug()->getValue() );
				if( !destination.empty() && IECore::StringAlgo::match( sourceData.first, shuffle.sourcePattern ) )
				{
					destinationContainer[destination] = sourceData.second;
					if( !newDestinations.insert( destination ).second )
					{
						throw IECore::Exception(
							boost::str(
								boost::format(
									"ShufflesPlug::shuffle : Destination plug \"%s\" is shuffling \"%s\" to \"%s\", " \
									"but this destination was already written by a previous Shuffle."
								) %
								plug->destinationPlug()->relativeName( plug->node() ? plug->node()->parent() : nullptr ) %
								sourceData.first %
								destination
							)
						);
					}

					deleteSource |= shuffle.deleteSource;
				}
			}

		}

		if( !deleteSource && newDestinations.find( sourceData.first ) == newDestinations.end() )
		{
			destinationContainer[sourceData.first] = sourceData.second;
		}
	}

	return destinationContainer;
}

} // namespace Gaffer

#endif // GAFFER_SHUFFLEPLUG_INL
