//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/FileSystemPath.h"

#include "Gaffer/CompoundPathFilter.h"
#include "Gaffer/FileSequencePathFilter.h"
#include "Gaffer/MatchPatternPathFilter.h"
#include "Gaffer/PathFilter.h"

#include "IECore/DateTimeData.h"
#include "IECore/FileSequenceFunctions.h"
#include "IECore/SimpleTypedData.h"

#include "boost/algorithm/string.hpp"
#include "boost/date_time/posix_time/conversion.hpp"
#include "boost/filesystem.hpp"
#include "boost/filesystem/operations.hpp"

#ifndef _MSC_VER
	#include <grp.h>
	#include <pwd.h>
#else
	#include <stdio.h>
	#include <Windows.h>
	#include <tchar.h>
	#include "accctrl.h"
	#include "aclapi.h"
#endif

#include <regex>
#include <sys/stat.h>

using namespace std;
using namespace boost::filesystem;
using namespace boost::algorithm;
using namespace boost::posix_time;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

#ifdef _MSC_VER

std::string getFileSecurityInfo( const std::string &pathString, SECURITY_INFORMATION info )
{
	/// \todo : There may be optimizations to be had by caching credentials such
	/// as the results of `LookupAccountSid` to avoid costly Windows API calls.
	PSID pSidOwner = NULL;
	PSID pSidGroup = NULL;
	PSID pSid = NULL;
	BOOL bRtnBool = TRUE;
	LPTSTR AcctName = NULL;
	LPTSTR DomainName = NULL;
	DWORD dwAcctName = 1;
	DWORD dwDomainName = 1;
	SID_NAME_USE eUse = SidTypeUnknown;

	DWORD result = GetNamedSecurityInfo(
		pathString.c_str(),
		SE_FILE_OBJECT,
		OWNER_SECURITY_INFORMATION | GROUP_SECURITY_INFORMATION,
		&pSidOwner,
		&pSidGroup,
		NULL,  // Out : DACL
		NULL,  // Out : SACL
		NULL  // Out : Security Descriptor
	);

	if( info == OWNER_SECURITY_INFORMATION )
	{
		pSid = pSidOwner;
	}
	else if( info == GROUP_SECURITY_INFORMATION )
	{
		pSid = pSidGroup;
	}
	else
	{
		return "";
	}

	// First call to LookupAccountSid to get the buffer sizes.
	bRtnBool = LookupAccountSid(
		NULL,
		pSid,
		AcctName,
		( LPDWORD )&dwAcctName,
		DomainName,
		( LPDWORD )&dwDomainName,
		&eUse
	);

	// Reallocate memory for the buffers.
	AcctName = ( LPTSTR )GlobalAlloc( GMEM_FIXED, dwAcctName );

	// Check GetLastError for GlobalAlloc error condition.
	if (AcctName == NULL)
	{
		return "";
	}

	DomainName = ( LPTSTR )GlobalAlloc( GMEM_FIXED, dwDomainName );

	// Check GetLastError for GlobalAlloc error condition.
	if ( DomainName == NULL )
	{
		return "";
	}

	// Second call to LookupAccountSid to get the account name.
	bRtnBool = LookupAccountSid(
		NULL,
		pSid,
		AcctName,
		(LPDWORD)&dwAcctName,
		DomainName,
		(LPDWORD)&dwDomainName,
		&eUse
	);

	if ( bRtnBool == FALSE )
	{
		return "";
	}

	return AcctName;
}

#endif

std::string getFileOwner( const std::string &pathString )
{
	std::string value;
#ifndef _MSC_VER
	struct stat s;
	stat(pathString.c_str(), &s);
	struct passwd *pw = getpwuid(s.st_uid);
	return pw ? pw->pw_name : "";

#else

	return getFileSecurityInfo( pathString, OWNER_SECURITY_INFORMATION );

#endif

}

std::string getFileGroup( const std::string &pathString )
{
	std::string value;
#ifndef _MSC_VER
	struct stat s;
	stat(pathString.c_str(), &s);
	struct group *gr = getgrgid( s.st_gid );

	return gr ? gr->gr_name : "";

#else

	return getFileSecurityInfo( pathString, GROUP_SECURITY_INFORMATION );

#endif

}

}  // namespace

//////////////////////////////////////////////////////////////////////////
// FileSystemPath implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( FileSystemPath );

static InternedString g_ownerPropertyName( "fileSystem:owner" );
static InternedString g_groupPropertyName( "fileSystem:group" );
static InternedString g_modificationTimePropertyName( "fileSystem:modificationTime" );
static InternedString g_sizePropertyName( "fileSystem:size" );
static InternedString g_frameRangePropertyName( "fileSystem:frameRange" );

static std::regex g_driveLetterPattern{ "[A-Za-z]:" };

FileSystemPath::FileSystemPath( PathFilterPtr filter, bool includeSequences )
	:	Path( filter ), m_includeSequences( includeSequences )
{
}

FileSystemPath::FileSystemPath( const std::string &path, PathFilterPtr filter, bool includeSequences )
	:	Path( filter ), m_includeSequences( includeSequences )
{
	setFromString( path );
}

FileSystemPath::FileSystemPath( const Names &names, const IECore::InternedString &root, PathFilterPtr filter, bool includeSequences )
	:	Path( names, root, filter ), m_includeSequences( includeSequences )
{
}

FileSystemPath::~FileSystemPath()
{
}

bool FileSystemPath::isValid( const IECore::Canceller *canceller ) const
{
	if( !Path::isValid() )
	{
		return false;
	}

	if( m_includeSequences && isFileSequence() )
	{
		return true;
	}

	const file_type t = symlink_status( path( this->string() ) ).type();
	return t != status_error && t != file_not_found;
}

bool FileSystemPath::isLeaf( const IECore::Canceller *canceller ) const
{
	return isValid() && !is_directory( path( this->string() ) );
}

bool FileSystemPath::getIncludeSequences() const
{
	return m_includeSequences;
}

void FileSystemPath::setIncludeSequences( bool includeSequences )
{
	m_includeSequences = includeSequences;
}

bool FileSystemPath::isFileSequence() const
{
	if( !m_includeSequences || is_directory( path( this->string() ) ) )
	{
		return false;
	}

	try
	{
		return boost::regex_match( this->string(), FileSequence::fileNameValidator() );
	}
	catch( ... )
	{
	}

	return false;
}

FileSequencePtr FileSystemPath::fileSequence() const
{
	if( !m_includeSequences || is_directory( path( this->string() ) ) )
	{
		return nullptr;
	}

	FileSequencePtr sequence = nullptr;
	/// \todo Add cancellation support to `ls`.
	IECore::ls( this->nativeString(), sequence, /* minSequenceSize = */ 1 );
	return sequence;
}

void FileSystemPath::propertyNames( std::vector<IECore::InternedString> &names, const IECore::Canceller *canceller ) const
{
	Path::propertyNames( names );

	names.push_back( g_ownerPropertyName );
	names.push_back( g_groupPropertyName );
	names.push_back( g_modificationTimePropertyName );
	names.push_back( g_sizePropertyName );

	if( m_includeSequences )
	{
		names.push_back( g_frameRangePropertyName );
	}
}

IECore::ConstRunTimeTypedPtr FileSystemPath::property( const IECore::InternedString &name, const IECore::Canceller *canceller ) const
{
	if( name == g_ownerPropertyName )
	{
		if( m_includeSequences )
		{
			IECore::Canceller::check( canceller );
			FileSequencePtr sequence = fileSequence();
			if( sequence )
			{
				IECore::Canceller::check( canceller );
				std::vector<std::string> files;
				sequence->fileNames( files );

				size_t maxCount = 0;
				std::string mostCommon = "";
				std::map<std::string,size_t> ownerCounter;
				for( std::vector<std::string>::iterator it = files.begin(); it != files.end(); ++it )
				{
					IECore::Canceller::check( canceller );
					std::string value = getFileOwner( it->c_str() );
					std::pair<std::map<std::string,size_t>::iterator,bool> oIt = ownerCounter.insert( std::pair<std::string,size_t>( value, 0 ) );
					oIt.first->second++;
					if( oIt.first->second > maxCount )
					{
						mostCommon = value;
					}
				}

				return new StringData( mostCommon );
			}
		}

		std::string n = this->string();

		return new StringData( getFileOwner( n.c_str() ) );
	}
	else if( name == g_groupPropertyName )
	{
		if( m_includeSequences )
		{
			IECore::Canceller::check( canceller );
			FileSequencePtr sequence = fileSequence();
			if( sequence )
			{
				IECore::Canceller::check( canceller );
				std::vector<std::string> files;
				sequence->fileNames( files );

				size_t maxCount = 0;
				std::string mostCommon = "";
				std::map<std::string,size_t> ownerCounter;
				for( std::vector<std::string>::iterator it = files.begin(); it != files.end(); ++it )
				{
					IECore::Canceller::check( canceller );
					std::string value = getFileGroup( *it );
					std::pair<std::map<std::string,size_t>::iterator,bool> oIt = ownerCounter.insert( std::pair<std::string,size_t>( value, 0 ) );
					oIt.first->second++;
					if( oIt.first->second > maxCount )
					{
						mostCommon = value;
					}
				}

				return new StringData( mostCommon );
			}
		}

		std::string n = this->string();
		return new StringData( getFileGroup( n ) );
	}
	else if( name == g_modificationTimePropertyName )
	{
		boost::system::error_code e;

		if( m_includeSequences )
		{
			IECore::Canceller::check( canceller );
			FileSequencePtr sequence = fileSequence();
			if( sequence )
			{
				IECore::Canceller::check( canceller );
				std::vector<std::string> files;
				sequence->fileNames( files );

				std::time_t newest = 0;
				for( std::vector<std::string>::iterator it = files.begin(); it != files.end(); ++it )
				{
					IECore::Canceller::check( canceller );
					std::time_t t = last_write_time( path( *it ), e );
					if( t > newest )
					{
						newest = t;
					}
				}

				return new DateTimeData( from_time_t( newest ) );
			}
		}

		std::time_t t = last_write_time( path( this->string() ), e );
		return new DateTimeData( from_time_t( t ) );
	}
	else if( name == g_sizePropertyName )
	{
		boost::system::error_code e;

		if( m_includeSequences )
		{
			IECore::Canceller::check( canceller );
			FileSequencePtr sequence = fileSequence();
			if( sequence )
			{
				IECore::Canceller::check( canceller );
				std::vector<std::string> files;
				sequence->fileNames( files );

				uintmax_t total = 0;
				for( std::vector<std::string>::iterator it = files.begin(); it != files.end(); ++it )
				{
					IECore::Canceller::check( canceller );
					uintmax_t s = file_size( path( *it ), e );
					if( !e )
					{
						total += s;
					}
				}

				return new UInt64Data( total );
			}
		}

		uintmax_t s = file_size( path( this->string() ), e );
		return new UInt64Data( !e ? s : 0 );
	}
	else if( name == g_frameRangePropertyName )
	{
		FileSequencePtr sequence = fileSequence();
		if( sequence )
		{
			return new StringData( sequence->getFrameList()->asString() );
		}

		return new StringData;
	}

	return Path::property( name );
}

PathPtr FileSystemPath::copy() const
{
	return new FileSystemPath( names(), root(), const_cast<PathFilter *>( getFilter() ), m_includeSequences );
}

void FileSystemPath::doChildren( std::vector<PathPtr> &children, const IECore::Canceller *canceller ) const
{
	path p( this->string() );

	if( !is_directory( p ) )
	{
		return;
	}

	for( directory_iterator it( p ), eIt; it != eIt; ++it )
	{
		IECore::Canceller::check( canceller );
		children.push_back( new FileSystemPath( it->path().generic_string(), const_cast<PathFilter *>( getFilter() ), m_includeSequences ) );
	}

	if( m_includeSequences )
	{
		IECore::Canceller::check( canceller );
		std::vector<FileSequencePtr> sequences;
		IECore::ls( this->nativeString(), sequences, /* minSequenceSize */ 1 );
		for( std::vector<FileSequencePtr>::iterator it = sequences.begin(); it != sequences.end(); ++it )
		{
			IECore::Canceller::check( canceller );
			std::vector<FrameList::Frame> frames;
			(*it)->getFrameList()->asList( frames );
			if ( !is_directory( path( (*it)->fileNameForFrame( frames[0] ) ) ) )
			{
				children.push_back( new FileSystemPath( path( p / (*it)->getFileName() ).generic_string(), const_cast<PathFilter *>( getFilter() ), m_includeSequences ) );
			}
		}
	}
}

PathFilterPtr FileSystemPath::createStandardFilter( const std::vector<std::string> &extensions, const std::string &extensionsLabel, bool includeSequenceFilter )
{
	CompoundPathFilterPtr result = new CompoundPathFilter();

	// Filter for the extensions

	if( extensions.size() )
	{
		std::string defaultLabel = "Show only ";
		vector<StringAlgo::MatchPattern> patterns;
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

	// Filter for sequences
	if( includeSequenceFilter )
	{
		result->addFilter( new FileSequencePathFilter( /* mode = */ FileSequencePathFilter::Concise ) );
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

#ifdef _MSC_VER

void FileSystemPath::rootAndNames(const std::string &string, InternedString &root, Names &names ) const
{
	std::string sanitizedString = string;

	// Parsing a filename with characters that are meant to be escaped by string substitution will cause
	// unwanted path splits. We replace Gaffer's escaped special characters with characters that can't be
	// used in Windows paths (so they won't be expected to be part of the input), then convert back after
	// splitting the path.
	using ReplacementPair = std::pair<std::string, std::string>;
	std::vector<ReplacementPair> replacements = { { "\\~", "<" }, { "\\$", ">" }, { "\\#", "?" } };
	for( std::vector<ReplacementPair>::const_iterator it = replacements.begin(), eIt = replacements.end(); it < eIt; ++it )
	{
		boost::replace_all( sanitizedString, it->first, it->second );
	}

	if( sanitizedString == "/" || sanitizedString == "\\" )
	{
		// We consider a single forward or back slash to be invalid, and convert it to the start
		// of a UNC path. Windows will return a directory listing of the current drive root contents
		// given a single slash, but with the permutations below, the child paths of that
		// listing will have roots but `names()` will be empty. This causes a crash when listing
		// such directories in `PathListingWidget`.
		sanitizedString = "//";
	}
	else if( sanitizedString.size() && sanitizedString[0] == '/' )
	{
		// If `string` is coming from a PathMatcher, it will always have a single leading slash.
		// On Windows, check to see if the first element is a drive letter path and strip the leading
		// slash if so. If it's not a drive letter path, interpret it as a UNC path.

		Names splitPath;
		StringAlgo::tokenize(sanitizedString, '/', splitPath);
		if( splitPath.size() )
		{
			const std::string firstElement = splitPath[0].string();
			if( std::regex_match( firstElement, g_driveLetterPattern ) )
			{
				sanitizedString.erase( sanitizedString.begin(), sanitizedString.begin() + 1 );
			}
			else if( sanitizedString.size() > 1 && sanitizedString[1] != '/' )
			{
				sanitizedString = "/" + sanitizedString;
			}
		}
	}

	const path convertedPath( sanitizedString );
	std::string rootString = convertedPath.root_path().generic_string();
	for( std::vector<ReplacementPair>::const_iterator it = replacements.begin(), eIt = replacements.end(); it < eIt; ++it )
	{
		boost::replace_all( rootString, it->second, it->first );
	}
	root = rootString;

	path::const_iterator startIt = convertedPath.begin();

	// path iteration includes the root name and directory, if present
	if( convertedPath.has_root_name() )
	{
		++startIt;
	}

	if( convertedPath.has_root_directory() )
	{
		++startIt;
	}

	for( path::const_iterator it = startIt, eIt = convertedPath.end(); it != eIt; ++it )
	{
		std::string itString = it->string();
		if( itString != "." )
		{
			for( std::vector<ReplacementPair>::const_iterator it = replacements.begin(), eIt = replacements.end(); it < eIt; ++it )
			{
				boost::replace_all( itString, it->second, it->first );
			}
			names.push_back( itString );
		}
	}
}

#endif

std::string FileSystemPath::nativeString() const
{
#ifndef _MSC_VER
	return string();
#endif

	path p( string() );
	// This is used instead of `nativeString()` because `nativeString()` on Windows
	// returns a `wstring`.
	p.make_preferred();
	return p.string();
}
