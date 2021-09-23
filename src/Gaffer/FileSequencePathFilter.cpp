//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/FileSequencePathFilter.h"

#include "Gaffer/FileSystemPath.h"

#include "IECore/FileSequence.h"
#include "IECore/FileSequenceFunctions.h"

#include "boost/bind.hpp"
#include "boost/filesystem.hpp"

using namespace std;
using namespace IECore;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( FileSequencePathFilter );

FileSequencePathFilter::FileSequencePathFilter( Keep mode, IECore::CompoundDataPtr userData )
	:	PathFilter( userData ), m_mode( mode )
{
}

FileSequencePathFilter::~FileSequencePathFilter()
{
}

FileSequencePathFilter::Keep FileSequencePathFilter::getMode() const
{
	return m_mode;
}

void FileSequencePathFilter::setMode( Keep mode )
{
	if ( mode == m_mode )
	{
		return;
	}

	m_mode = mode;
	changedSignal()( this );
}

void FileSequencePathFilter::doFilter( std::vector<PathPtr> &paths, const IECore::Canceller *canceller ) const
{
	paths.erase(
		std::remove_if(
			paths.begin(),
			paths.end(),
			boost::bind( &FileSequencePathFilter::remove, this, ::_1 )
		),
		paths.end()
	);
}

bool FileSequencePathFilter::remove( PathPtr path ) const
{
	FileSystemPath *fileSystemPath = IECore::runTimeCast<FileSystemPath>( path.get() );
	if( !fileSystemPath )
	{
		// if it's not a FileSystemPath we shouldn't be removing anything
		return false;
	}

	if( m_mode == All || boost::filesystem::is_directory( fileSystemPath->string() ) )
	{
		// always keep directories (and All)
		return false;
	}

	if( ( m_mode & Sequences ) && ( fileSystemPath->isFileSequence() ) )
	{
		// its a valid sequence, so keep it
		return false;
	}

	std::vector<std::string> names( 1, fileSystemPath->string() );
	std::vector<FileSequencePtr> sequences;
	IECore::findSequences( names, sequences, /* minSequenceSize = */ 1 );
	bool isSequentialFile = !sequences.empty();

	if( ( m_mode & SequentialFiles ) && isSequentialFile )
	{
		// its a file that could be part of a sequence, so keep it
		return false;
	}

	if( ( m_mode & Files ) && !isSequentialFile && boost::filesystem::is_regular_file( fileSystemPath->string() ) )
	{
		// its a real file on disk that isn't a sequential file, so keep it
		return false;
	}

	// remove anything that got here
	return true;
}
