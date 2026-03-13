//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferDispatch/RenameFiles.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string/replace.hpp"

#include "fmt/args.h"
#include "fmt/format.h"
#include "fmt/std.h"

#include <filesystem>
#include <regex>

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferDispatch;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo This is copied from `GafferScene/Rename.cpp`. We should probably
/// find a shared home for it at some point.
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

const IECore::InternedString g_sourceVariable( "source" );
const IECore::InternedString g_sourceStemVariable( "source:stem" );
const IECore::InternedString g_sourceExtensionVariable( "source:extension" );

} // namespace

//////////////////////////////////////////////////////////////////////////
// RenameFiles
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( RenameFiles );

size_t RenameFiles::g_firstPlugIndex = 0;

RenameFiles::RenameFiles( const std::string &name )
	:	TaskNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringVectorDataPlug( "files" ) );
	addChild( new StringPlug( "name" ) );
	addChild( new StringPlug( "deletePrefix" ) );
	addChild( new StringPlug( "deleteSuffix" ) );
	addChild( new StringPlug( "find" ) );
	addChild( new StringPlug( "replace" ) );
	addChild( new BoolPlug( "useRegularExpressions" ) );
	addChild( new StringPlug( "addPrefix" ) );
	addChild( new StringPlug( "addSuffix" ) );
	addChild( new BoolPlug( "replaceExtension" ) );
	addChild( new StringPlug( "extension" ) );
	addChild( new BoolPlug( "overwrite" ) );
}

RenameFiles::~RenameFiles()
{
}

Gaffer::StringVectorDataPlug *RenameFiles::filesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex );
}

const Gaffer::StringVectorDataPlug *RenameFiles::filesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *RenameFiles::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *RenameFiles::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *RenameFiles::deletePrefixPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *RenameFiles::deletePrefixPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *RenameFiles::deleteSuffixPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *RenameFiles::deleteSuffixPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *RenameFiles::findPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *RenameFiles::findPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringPlug *RenameFiles::replacePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}
const Gaffer::StringPlug *RenameFiles::replacePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

Gaffer::BoolPlug *RenameFiles::useRegularExpressionsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::BoolPlug *RenameFiles::useRegularExpressionsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

Gaffer::StringPlug *RenameFiles::addPrefixPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::StringPlug *RenameFiles::addPrefixPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 7 );
}

Gaffer::StringPlug *RenameFiles::addSuffixPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 8 );
}
const Gaffer::StringPlug *RenameFiles::addSuffixPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 8 );
}

Gaffer::BoolPlug *RenameFiles::replaceExtensionPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::BoolPlug *RenameFiles::replaceExtensionPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 9 );
}

Gaffer::StringPlug *RenameFiles::extensionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 10 );
}

const Gaffer::StringPlug *RenameFiles::extensionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 10 );
}

Gaffer::BoolPlug *RenameFiles::overwritePlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 11 );
}

const Gaffer::BoolPlug *RenameFiles::overwritePlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 11 );
}

IECore::MurmurHash RenameFiles::hash( const Gaffer::Context *context ) const
{
	ConstStringVectorDataPtr filesData = filesPlug()->getValue();
	if( filesData->readable().empty() )
	{
		return IECore::MurmurHash();
	}

	IECore::MurmurHash h = TaskNode::hash( context );
	filesData->hash( h );
	namePlug()->hash( h );
	deletePrefixPlug()->hash( h );
	deleteSuffixPlug()->hash( h );
	findPlug()->hash( h );
	replacePlug()->hash( h );
	useRegularExpressionsPlug()->hash( h );
	addPrefixPlug()->hash( h );
	addSuffixPlug()->hash( h );
	replaceExtensionPlug()->hash( h );
	extensionPlug()->hash( h );
	overwritePlug()->hash( h );
	return h;
}

void RenameFiles::execute() const
{
	ConstStringVectorDataPtr filesData = filesPlug()->getValue();
	const string deletePrefix = deletePrefixPlug()->getValue();
	const string deleteSuffix = deleteSuffixPlug()->getValue();
	const string find = findPlug()->getValue();
	const string replace = replacePlug()->getValue();
	const bool useRegularExpressions = useRegularExpressionsPlug()->getValue();
	const string addPrefix = addPrefixPlug()->getValue();
	const string addSuffix = addSuffixPlug()->getValue();
	std::optional<string> extension;
	if( replaceExtensionPlug()->getValue() )
	{
		extension = extensionPlug()->getValue();
		if( extension->size() && (*extension)[0] != '.' )
		{
			extension->insert( 0, "." );
		}
	}

	// Build a map from destination path to source path. This allows
	// us to sanity check the operation before committing to doing it.
	std::map<filesystem::path, filesystem::path> destinationToSource;

	Context::EditableScope context( Context::current() );
	for( const auto &file : filesData->readable() )
	{
		context.set( g_sourceVariable, &file );
		const filesystem::path sourceFilePath = filesystem::canonical( file );

		const string sourceStem = sourceFilePath.stem().string();
		context.set( g_sourceStemVariable, &sourceStem );

		const string sourceExtension = sourceFilePath.extension().string();
		context.set( g_sourceExtensionVariable, &sourceExtension );

		string name = namePlug()->getValue();
		if( !name.size() )
		{
			string stem = sourceFilePath.stem().string();

			if( boost::starts_with( stem, deletePrefix ) )
			{
				stem.erase( 0, deletePrefix.size() );
			}

			if( boost::ends_with( stem, deleteSuffix ) )
			{
				stem.erase( stem.size() - deleteSuffix.size() );
			}

			if( find.size() )
			{
				if( useRegularExpressions )
				{
					stem = regexReplace( stem, regex( find ), replace );
				}
				else
				{
					boost::replace_all( stem, find, replace );
				}
			}

			stem.insert( 0, addPrefixPlug()->getValue() );
			stem.insert( stem.size(), addSuffixPlug()->getValue() );

			name = stem;
			if( extension )
			{
				name += *extension;
			}
			else
			{
				name += sourceFilePath.extension().string();
			}
		}

		filesystem::path destinationFilePath = sourceFilePath;
		destinationFilePath.replace_filename( name );

		const auto [it, inserted] = destinationToSource.insert( { destinationFilePath, sourceFilePath } );
		if( !inserted )
		{
			throw IECore::Exception(
				fmt::format(
					"Destination \"{}\" has multiple source files : \"{}\" and \"{}\"",
					destinationFilePath.generic_string(), it->second.generic_string(), sourceFilePath.generic_string()
				)
			);
		}
	}

	// Check that we're not writing over any source files.

	for( const auto &[destinationFilePath, sourceFilePath] : destinationToSource )
	{
		auto it = destinationToSource.find( sourceFilePath );
		if( it != destinationToSource.end() )
		{
			throw IECore::Exception(
				fmt::format(
					"Renaming of \"{}\" would overwrite source \"{}\"",
					it->second.generic_string(), sourceFilePath.generic_string()
				)
			);
		}
	}

	// Finally do the work.

	const bool overwrite = overwritePlug()->getValue();
	for( const auto &[destinationFilePath, sourceFilePath] : destinationToSource )
	{
		if( !overwrite && filesystem::exists( destinationFilePath ) )
		{
			throw IECore::Exception(
				fmt::format(
					"Can not overwrite destination \"{}\" unless `overwrite` plug is set.", destinationFilePath.generic_string()
				)
			);
		}
		filesystem::rename( sourceFilePath, destinationFilePath );
	}
}
