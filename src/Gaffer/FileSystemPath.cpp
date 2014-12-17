//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

#include <pwd.h>
#include <grp.h>
#include <sys/stat.h>

#include "boost/filesystem.hpp"
#include "boost/filesystem/operations.hpp"
#include "boost/algorithm/string.hpp"
#include "boost/date_time/posix_time/conversion.hpp"

#include "IECore/SimpleTypedData.h"
#include "IECore/DateTimeData.h"

#include "Gaffer/PathFilter.h"
#include "Gaffer/FileSystemPath.h"
#include "Gaffer/CompoundPathFilter.h"
#include "Gaffer/MatchPatternPathFilter.h"

using namespace std;
using namespace boost::filesystem;
using namespace boost::algorithm;
using namespace boost::posix_time;
using namespace IECore;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( FileSystemPath );

static InternedString g_ownerAttributeName( "fileSystem:owner" );
static InternedString g_groupAttributeName( "fileSystem:group" );
static InternedString g_modificationTimeAttributeName( "fileSystem:modificationTime" );
static InternedString g_sizeAttributeName( "fileSystem:size" );

FileSystemPath::FileSystemPath( PathFilterPtr filter )
	:	Path( filter )
{
}

FileSystemPath::FileSystemPath( const std::string &path, PathFilterPtr filter )
	:	Path( path, filter )
{
}

FileSystemPath::FileSystemPath( const Names &names, const IECore::InternedString &root, PathFilterPtr filter )
	:	Path( names, root, filter )
{
}

FileSystemPath::~FileSystemPath()
{
}

bool FileSystemPath::isValid() const
{
	const file_type t = symlink_status( path( this->string() ) ).type();
	return Path::isValid() && t != status_error && t != file_not_found;
}

bool FileSystemPath::isLeaf() const
{
	return isValid() && !is_directory( path( this->string() ) );
}

void FileSystemPath::attributeNames( std::vector<IECore::InternedString> &names ) const
{
	Path::attributeNames( names );

	names.push_back( g_ownerAttributeName );
	names.push_back( g_groupAttributeName );
	names.push_back( g_modificationTimeAttributeName );
	names.push_back( g_sizeAttributeName );
}

IECore::ConstRunTimeTypedPtr FileSystemPath::attribute( const IECore::InternedString &name ) const
{
	if( name == g_ownerAttributeName )
	{
		std::string n = this->string();
		struct stat s;
		stat( n.c_str(), &s );
		struct passwd *pw = getpwuid( s.st_uid );
		return new StringData( pw ? pw->pw_name : "" );
	}
	else if( name == g_groupAttributeName )
	{
		std::string n = this->string();
		struct stat s;
		stat( n.c_str(), &s );
		struct group *gr = getgrgid( s.st_gid );
		return new StringData( gr ? gr->gr_name : "" );
	}
	else if( name == g_modificationTimeAttributeName )
	{
		boost::system::error_code e;
		std::time_t t = last_write_time( path( this->string() ), e );
		return new DateTimeData( from_time_t( t ) );
	}
	else if( name == g_sizeAttributeName )
	{
		boost::system::error_code e;
		uintmax_t s = file_size( path( this->string() ), e );
		return new UInt64Data( !e ? s : 0 );
	}

	return Path::attribute( name );
}

PathPtr FileSystemPath::copy() const
{
	return new FileSystemPath( names(), root(), const_cast<PathFilter *>( getFilter() ) );
}

void FileSystemPath::doChildren( std::vector<PathPtr> &children ) const
{
	path p( this->string() );

	if( !is_directory( p ) )
	{
		return;
	}

	for( directory_iterator it( p ), eIt; it != eIt; ++it )
	{
		children.push_back( new FileSystemPath( it->path().string(), const_cast<PathFilter *>( getFilter() ) ) );
	}
}

PathFilterPtr FileSystemPath::createStandardFilter( const std::vector<std::string> &extensions, const std::string &extensionsLabel )
{
	CompoundPathFilterPtr result = new CompoundPathFilter();

	// Filter for the extensions

	if( extensions.size() )
	{
		std::string defaultLabel = "Show only ";
		vector<MatchPattern> patterns;
		for( std::vector<std::string>::const_iterator it = extensions.begin(), eIt = extensions.end(); it != eIt; ++it )
		{
			patterns.push_back( "*." + to_lower_copy( *it ) );
			patterns.push_back( "*." + to_upper_copy( *it ) );
			// the form below is for file sequences, where the frame
			// range will come after the extension.
			patterns.push_back( "*." + to_lower_copy( *it ) + " *" );
			patterns.push_back( "*." + to_upper_copy( *it ) + " *" );

			if( it != extensions.begin() )
			{
				defaultLabel += ", ";
			}
			defaultLabel += "." + to_lower_copy( *it );
		}
		defaultLabel += " files";

		MatchPatternPathFilterPtr fileNameFilter = new MatchPatternPathFilter( patterns, "name" );
		CompoundDataPtr uiUserData = new CompoundData;
		uiUserData->writable()["label"] = new StringData( extensionsLabel.size() ? extensionsLabel : defaultLabel );
		fileNameFilter->userData()->writable()["UI"] = uiUserData;

		result->addFilter( fileNameFilter );
	}

	// Filter for hidden files

	std::vector<std::string> hiddenFilePatterns; hiddenFilePatterns.push_back( ".*" );
	MatchPatternPathFilterPtr hiddenFilesFilter = new MatchPatternPathFilter( hiddenFilePatterns, "name", /* leafOnly = */ false );
	hiddenFilesFilter->setInverted( true );

	CompoundDataPtr hiddenFilesUIUserData = new CompoundData;
	hiddenFilesUIUserData->writable()["label"] = new StringData( "Show hidden files" );
	hiddenFilesUIUserData->writable()["invertEnabled"] = new BoolData( true );
	hiddenFilesFilter->userData()->writable()["UI"] = hiddenFilesUIUserData;

	result->addFilter( hiddenFilesFilter );

	// User defined search filter

	std::vector<std::string> searchPatterns; searchPatterns.push_back( "" );
	MatchPatternPathFilterPtr searchFilter = new MatchPatternPathFilter( searchPatterns );
	searchFilter->setEnabled( false );

	CompoundDataPtr searchUIUserData = new CompoundData;
	searchUIUserData->writable()["editable"] = new BoolData( true );
	searchFilter->userData()->writable()["UI"] = searchUIUserData;

	result->addFilter( searchFilter );

	return result;
}
