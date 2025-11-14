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

#include "GafferDispatch/FileList.h"

#include "IECore/FileSequenceFunctions.h"
#include "IECore/PathMatcher.h"
#include "IECore/StringAlgo.h"

#include "boost/algorithm/string/case_conv.hpp"

#include <unordered_set>

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferDispatch;

namespace
{

void fileListWalk( const filesystem::path fileSystemPath, const vector<InternedString> &path, const IECore::PathMatcher &inclusions, const IECore::PathMatcher &exclusions, vector<filesystem::path> &pathList )
{
	const unsigned exclusionsMatch = exclusions.match( path );
	if( exclusionsMatch & PathMatcher::ExactMatch )
	{
		return;
	}

	const unsigned inclusionsMatch = inclusions.match( path );
	if( ( inclusionsMatch & PathMatcher::ExactMatch ) && path.size() )
	{
		pathList.push_back( fileSystemPath );
	}

	if( ( inclusionsMatch & PathMatcher::DescendantMatch ) && filesystem::is_directory( fileSystemPath ) )
	{
		vector<InternedString> childPath = path; childPath.push_back( InternedString() );
		for( auto directoryEntry : filesystem::directory_iterator( fileSystemPath ) )
		{
			childPath.back() = InternedString( directoryEntry.path().filename().string() );
			fileListWalk( directoryEntry.path(), childPath, inclusions, exclusions, pathList );
		}
	}
}

PathMatcher pathMatcher( const string &patterns, bool recurse )
{
	PathMatcher result;

	std::vector<string> patternsSplit;
	IECore::StringAlgo::tokenize( patterns, ' ', patternsSplit );
	for( const auto &pattern : patternsSplit )
	{
		result.addPath( pattern );
	}

	if( recurse )
	{
		PathMatcher recursiveResult;
		recursiveResult.addPaths( result, { "..." } );
		result = recursiveResult;
	}

	return result;
}

StringVectorDataPtr fileList( const std::filesystem::path &directory,
	const string &inclusions, const string &exclusions, const string &fileExtensions,
	bool recurse, bool absolute, FileList::SequenceMode sequenceMode
)
{
	if( directory.empty() )
	{
		return new StringVectorData;
	}

	const PathMatcher inclusionsPathMatcher = pathMatcher( inclusions, recurse );
	const PathMatcher exclusionsPathMatcher = pathMatcher( exclusions, recurse );

	vector<filesystem::path> pathList;
	fileListWalk( directory, {}, inclusionsPathMatcher, exclusionsPathMatcher, pathList );
	std::sort( pathList.begin(), pathList.end() );

	const string fileExtensionsLower = boost::algorithm::to_lower_copy( fileExtensions );

	vector<string> fileList; fileList.reserve( pathList.size() );
	for( const auto &path : pathList )
	{
		const string extension = boost::algorithm::to_lower_copy( path.extension().string() );
		const char *extensionWithoutDot = extension.size() ? extension.c_str() + 1 : extension.c_str();
		if( !IECore::StringAlgo::matchMultiple( extensionWithoutDot, fileExtensionsLower ) )
		{
			continue;
		}

		if( absolute )
		{
			fileList.push_back( filesystem::absolute( path ).generic_string() );
		}
		else
		{
			fileList.push_back( filesystem::relative( path, directory ).generic_string() );
		}
	}

	if( sequenceMode != FileList::SequenceMode::Files )
	{
		vector<FileSequencePtr> sequences;
		IECore::findSequences( fileList, sequences );

		if( sequenceMode == FileList::SequenceMode::Sequences )
		{
			fileList.clear();
		}
		else
		{
			// Remove files that are not in a sequence.
			vector<string> sequenceFiles;
			for( const auto &sequence : sequences )
			{
				sequence->fileNames( sequenceFiles );
			}
			unordered_set<string> sequenceFilesSet( sequenceFiles.begin(), sequenceFiles.end() );
			fileList.erase(
				std::remove_if(
					fileList.begin(),
					fileList.end(),
					[&] ( const string &x ) -> bool {
						return sequenceFilesSet.count( x );
					}
				),
				fileList.end()
			);
		}

		for( const auto &sequence : sequences )
		{
			fileList.push_back( sequence->getFileName() );
		}
	}

	return new StringVectorData( std::move( fileList ) );
}

} // namespace

GAFFER_NODE_DEFINE_TYPE( FileList );

size_t FileList::g_firstPlugIndex = 0;

FileList::FileList( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new BoolPlug( "enabled", Plug::In, true ) );
	addChild( new StringPlug( "directory" ) );
	addChild( new IntPlug( "refreshCount" ) );
	addChild( new StringPlug( "inclusions", Plug::In, "*" ) );
	addChild( new StringPlug( "exclusions", Plug::In, "" ) );
	addChild( new StringPlug( "extensions", Plug::In, "*" ) );
	addChild( new BoolPlug( "searchSubdirectories" ) );
	addChild( new BoolPlug( "absolute", Plug::In, true ) );
	addChild( new IntPlug( "sequenceMode", Plug::In, (int)SequenceMode::Files, (int)SequenceMode::Files, (int)SequenceMode::FilesAndSequences ) );
	addChild( new StringVectorDataPlug( "out", Plug::Out ) );
}

FileList::~FileList()
{
}

Gaffer::BoolPlug *FileList::enabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

const Gaffer::BoolPlug *FileList::enabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *FileList::directoryPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *FileList::directoryPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *FileList::refreshCountPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *FileList::refreshCountPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *FileList::inclusionsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *FileList::inclusionsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *FileList::exclusionsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *FileList::exclusionsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringPlug *FileList::extensionsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringPlug *FileList::extensionsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

Gaffer::BoolPlug *FileList::searchSubdirectoriesPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::BoolPlug *FileList::searchSubdirectoriesPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

Gaffer::BoolPlug *FileList::absolutePlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::BoolPlug *FileList::absolutePlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 7 );
}

Gaffer::IntPlug *FileList::sequenceModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::IntPlug *FileList::sequenceModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 8 );
}

Gaffer::StringVectorDataPlug *FileList::outPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::StringVectorDataPlug *FileList::outPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 9 );
}

void FileList::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == enabledPlug() ||
		input == directoryPlug() ||
		input == refreshCountPlug() ||
		input == inclusionsPlug() ||
		input == exclusionsPlug() ||
		input == extensionsPlug() ||
		input == searchSubdirectoriesPlug() ||
		input == absolutePlug() ||
		input == sequenceModePlug()
	)
	{
		outputs.push_back( outPlug() );
	}
}

void FileList::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	if( output == outPlug() )
	{
		ComputeNode::hash( output, context, h );
		if( enabledPlug()->getValue() )
		{
			directoryPlug()->hash( h );
			refreshCountPlug()->hash( h );
			inclusionsPlug()->hash( h );
			exclusionsPlug()->hash( h );
			extensionsPlug()->hash( h );
			searchSubdirectoriesPlug()->hash( h );
			absolutePlug()->hash( h );
			sequenceModePlug()->hash( h );
		}
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void FileList::compute( ValuePlug *output, const Context *context ) const
{
	if( output == outPlug() )
	{
		if( enabledPlug()->getValue() )
		{
			static_cast<StringVectorDataPlug *>( output )->setValue(
				fileList(
					directoryPlug()->getValue(),
					inclusionsPlug()->getValue(),
					exclusionsPlug()->getValue(),
					extensionsPlug()->getValue(),
					searchSubdirectoriesPlug()->getValue(),
					absolutePlug()->getValue(),
					(SequenceMode)sequenceModePlug()->getValue()
				)
			);
		}
		else
		{
			output->setToDefault();
		}
	}
	else
	{
		ComputeNode::compute( output, context );
	}
}

ValuePlug::CachePolicy FileList::computeCachePolicy( const ValuePlug *output ) const
{
	if( output == outPlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ComputeNode::computeCachePolicy( output );
}
