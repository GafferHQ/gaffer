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

} // namespace

namespace Gaffer
{

template<typename T>
T ShufflesPlug::shuffle( const T &sourceContainer ) const
{
	using NameContainer = std::unordered_set< typename T::key_type >;

	// NOTE : The shuffles are applied in the same order they were added to the parent plug.
	//        Each shuffle's source may contain wildcards, so a single shuffle may read from
	//        multiple source names and write to multiple destination names, therefore each
	//        shuffle specifies a set of data "moves". As each shuffle's set of moves is
	//        unordered, moves with the same destination name eg. {a->c, b->c} are invalid.
	//        Identity moves eg. {a->a, b->b} are ignored. Cyclic moves eg. {a->b, b->a} and
	//        chained moves eg. {a->b, b->c} are valid as data is always copied from the source
	//        container. If the delete source flag is specified for a shuffle the source names
	//        are deleted after all shuffles have completed. If the replace destination flag is
	//        false for a shuffle each move will not replace data with the same name as its destination.

	T destinationContainer( sourceContainer ); // NOTE : initial copy of all source data to destination.

	NameContainer names;

	for( const ConstShufflePlugPtr &plug : ShufflePlug::Range( *this ) )
	{
		// NOTE : "source" context variable only applies to the destination plug.
		//        So retrieve values of other plugs before setting context variable.

		if( ! plug->enabledPlug()->getValue() )
			continue;

		const std::string &srcPattern = plug->sourcePlug()->getValue();
		if( srcPattern.empty() )
			continue;

		const bool srcDelete = plug->deleteSourcePlug()->getValue();
		const bool dstReplace = plug->replaceDestinationPlug()->getValue();

		// NOTE : Check if the source plug value contains wildcards. The destination
		//        plug value cannot contain wildcards but may contain substitutions.
		//        Any source substitutons should have already been done when evaluating
		//        the source plug. We need to do destination substitutions manually.

		if( ! IECore::StringAlgo::hasWildcards( srcPattern ) )
		{
			// NOTE : No wildcards in source so shuffle is one move.

			const std::string &srcName = srcPattern;
			const typename T::const_iterator sIt = sourceContainer.find( srcName );
			if( sIt != sourceContainer.end() )
			{
				Gaffer::Context::EditableScope scope( Gaffer::Context::current() );
				scope.set<std::string>( g_sourceVariable, &srcName );
				const std::string &dstPattern = plug->destinationPlug()->getValue();
				if( ! dstPattern.empty() )
				{
					const std::string dstName = scope.context()->substitute( dstPattern );
					if( srcName != dstName )
					{
						if( dstReplace || ( destinationContainer.find( dstName ) == destinationContainer.end() ) )
						{
							destinationContainer[ dstName ] = sIt->second;
							names.insert( dstName );
						}

						if( srcDelete && ( names.find( srcName ) == names.end() ) )
						{
							destinationContainer.erase( srcName );
						}
					}
				}
			}
		}
		else
		{
			// NOTE : The source contains wildcards so shuffle may be composed of
			//        multiple moves. Match source pattern against each source name
			//        and do destination substitutions.

			Gaffer::Context::EditableScope scope( Gaffer::Context::current() );

			NameContainer moveNames;
			for( typename T::const_iterator
					sIt    = sourceContainer.begin(),
					sItEnd = sourceContainer.end(); sIt != sItEnd; ++sIt )
			{
				// NOTE : Quick way to get a string from a key that could be std::string or IECore::InternedString

				const std::string &srcName = sIt->first;
				if( IECore::StringAlgo::match( srcName, srcPattern ) )
				{
					scope.set<std::string>( g_sourceVariable, &srcName );
					const std::string &dstPattern = plug->destinationPlug()->getValue();
					if( ! dstPattern.empty() )
					{
						const std::string dstName = scope.context()->substitute( dstPattern );
						if( srcName != dstName )
						{
							// NOTE : Check for clashing move destination names within this shuffle.
							//        Do check regardless of whether shuffle's replace destination
							//        flag means destination is not actually written.

							if( ! moveNames.insert( dstName ).second )
							{
								throw IECore::Exception(
									boost::str(
										boost::format(
											"ShufflesPlug::shuffle : Destination plug \"%s\" shuffles from \"%s\" to \"%s\", " \
											"cannot write from multiple sources to destination \"%s\"" )
											% plug->destinationPlug()->relativeName( plug->node() ? plug->node()->parent() : nullptr )
											% srcPattern
											% dstPattern
											% dstName
								) );
							}

							if( dstReplace || ( destinationContainer.find( dstName ) == destinationContainer.end() ) )
							{
								destinationContainer[ dstName ] = sIt->second;
								names.insert( dstName );
							}

							if( srcDelete && ( names.find( srcName ) == names.end() ) )
							{
								destinationContainer.erase( srcName );
							}
						}
					}
				}
			}
		}
	}

	return destinationContainer;
}

} // namespace Gaffer

#endif // GAFFER_SHUFFLEPLUG_INL
