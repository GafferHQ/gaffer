//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Hypothetical Inc. All rights reserved.
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
#include "Gaffer/HiddenFilePathFilter.h"

#include "Gaffer/Path.h"

#ifdef _MSC_VER

#include <windows.h>

#endif

using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( HiddenFilePathFilter );

HiddenFilePathFilter::HiddenFilePathFilter( IECore::CompoundDataPtr userData )
	:	PathFilter( userData ), m_inverted( false )
{
}

HiddenFilePathFilter::~HiddenFilePathFilter()
{
}

void HiddenFilePathFilter::setInverted( bool inverted )
{
	if( inverted == m_inverted )
	{
		return;
	}
	m_inverted = inverted;
	changedSignal()( this );
}

bool HiddenFilePathFilter::getInverted() const
{
	return m_inverted;
}

void HiddenFilePathFilter::doFilter( std::vector<PathPtr> &paths, const IECore::Canceller *canceller ) const
{
	paths.erase(
		std::remove_if(
			paths.begin(),
			paths.end(),
			[this] ( const PathPtr &path ) { return remove( path ); }
		),
		paths.end()
	);
}

bool HiddenFilePathFilter::invert( bool b ) const
{
	return b != m_inverted;
}

bool HiddenFilePathFilter::remove( PathPtr path ) const
{
#ifndef _MSC_VER
	if( !path->names().size() )
	{
		return invert( true );
	}

	const std::string &s = path->names().back().string();
	if( s.size() && s[0] == '.' )
	{
		return invert( false );
	}
	return invert( true );
#else
	DWORD fileAttributes = GetFileAttributes( path->string().c_str() );
	if( fileAttributes & FILE_ATTRIBUTE_HIDDEN )
	{
		return invert( false );
	}
	return invert( true );
#endif
}
