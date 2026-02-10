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

#include "GafferDispatch/CopyFiles.h"

#include <filesystem>

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferDispatch;

GAFFER_NODE_DEFINE_TYPE( CopyFiles );

size_t CopyFiles::g_firstPlugIndex = 0;

CopyFiles::CopyFiles( const std::string &name )
	:	TaskNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringVectorDataPlug( "files" ) );
	addChild( new StringPlug( "destination" ) );
	addChild( new BoolPlug( "overwrite" ) );
	addChild( new BoolPlug( "deleteSource" ) );
}

CopyFiles::~CopyFiles()
{
}

Gaffer::StringVectorDataPlug *CopyFiles::filesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex );
}

const Gaffer::StringVectorDataPlug *CopyFiles::filesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *CopyFiles::destinationPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *CopyFiles::destinationPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *CopyFiles::overwritePlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *CopyFiles::overwritePlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *CopyFiles::deleteSourcePlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *CopyFiles::deleteSourcePlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

IECore::MurmurHash CopyFiles::hash( const Gaffer::Context *context ) const
{
	ConstStringVectorDataPtr filesData = filesPlug()->getValue();
	const std::string destination = destinationPlug()->getValue();
	if( filesData->readable().empty() || destination.empty() )
	{
		return IECore::MurmurHash();
	}

	IECore::MurmurHash h = TaskNode::hash( context );
	filesData->hash( h );
	h.append( destination );
	overwritePlug()->hash( h );
	deleteSourcePlug()->hash( h );
	return h;
}

void CopyFiles::execute() const
{
	ConstStringVectorDataPtr filesData = filesPlug()->getValue();
	filesystem::path destination = destinationPlug()->getValue();
	if( filesData->readable().empty() || destination.empty() )
	{
		return;
	}

	filesystem::path destinationPath( destination );
	filesystem::create_directories( destinationPath );

	const bool deleteSource = deleteSourcePlug()->getValue();
	const bool overwrite = overwritePlug()->getValue();

	filesystem::copy_options options = filesystem::copy_options::recursive;
	if( overwrite )
	{
		options |= filesystem::copy_options::overwrite_existing;
	}

	for( const auto &file : filesData->readable() )
	{
		const filesystem::path filePath = file;
		const filesystem::path destinationFilePath = destinationPath / filePath.filename();
		if( deleteSource && ( overwrite || !filesystem::exists( destinationFilePath ) ) )
		{
			try
			{
				// If we can simply rename the file, then that will be faster.
				std::filesystem::rename( file, destinationFilePath );
				continue;
			}
			catch( const filesystem::filesystem_error & )
			{
				// Couldn't rename. This could be because source and destination
				// are on different filesystems, in which case we suppress the
				// exception and fall through to copy/remove which should succeed.
				// Or it could be due to another problem such as permissions, in
				// which case we still suppress and fall through, expecting to
				// throw again.
			}
		}
		filesystem::copy( filePath, destinationFilePath, options );
		if( deleteSource )
		{
			filesystem::remove_all( filePath );
		}
	}

}
