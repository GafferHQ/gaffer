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

#include "GafferDispatch/DeleteFiles.h"

#include "Gaffer/Context.h"

#include <filesystem>

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferDispatch;

GAFFER_NODE_DEFINE_TYPE( DeleteFiles );

size_t DeleteFiles::g_firstPlugIndex = 0;

DeleteFiles::DeleteFiles( const std::string &name )
	:	TaskNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringVectorDataPlug( "files" ) );
	addChild( new BoolPlug( "deleteDirectories" ) );
}

DeleteFiles::~DeleteFiles()
{
}

Gaffer::StringVectorDataPlug *DeleteFiles::filesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex );
}

const Gaffer::StringVectorDataPlug *DeleteFiles::filesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *DeleteFiles::deleteDirectoriesPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *DeleteFiles::deleteDirectoriesPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

IECore::MurmurHash DeleteFiles::hash( const Gaffer::Context *context ) const
{
	ConstStringVectorDataPtr filesData = filesPlug()->getValue();
	if( filesData->readable().empty() )
	{
		return IECore::MurmurHash();
	}

	IECore::MurmurHash h = TaskNode::hash( context );
	filesData->hash( h );
	deleteDirectoriesPlug()->hash( h );
	return h;
}

void DeleteFiles::execute() const
{
	const bool deleteDirectories = deleteDirectoriesPlug()->getValue();
	ConstStringVectorDataPtr filesData = filesPlug()->getValue();
	for( const auto &file : filesData->readable() )
	{
		if( deleteDirectories )
		{
			filesystem::remove_all( filesystem::path( file ) );
		}
		else
		{
			filesystem::remove( filesystem::path( file ) );
		}
	}
}
