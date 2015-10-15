//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#include <map>

#include "boost/format.hpp"
#include "boost/foreach.hpp"

#include "IECore/Exception.h"

#include "GafferImage/Format.h"

using namespace GafferImage;

Format::FormatMap &Format::formatMap()
{
	static Format::FormatMap map;
	return map;
}

std::ostream& GafferImage::operator<<(std::ostream& os, GafferImage::Format const& format)
{
    os << Format::formatName( format );
    return os;
}

void Format::formatNames( std::vector< std::string > &names )
{
	names.clear();
	names.reserve( formatMap().size() );

	FormatEntry entry;
	BOOST_FOREACH( entry, formatMap() )
	{
		names.push_back( entry.first );
	}
}

std::string Format::formatName( const Format &format )
{
	FormatMap::iterator it( formatMap().begin() );
	FormatMap::iterator end( formatMap().end() );

	for (; it != end; ++it)
	{
		if ( format == (*it).second )
		{
			return (*it).first;
		}
	}

	std::string name;
	generateFormatName( name, format );

	return name;
}

const Format &Format::registerFormat( const Format &format, const std::string &name )
{
	FormatMap::iterator it( formatMap().begin() );
	FormatMap::iterator end( formatMap().end() );

	for (; it != end; ++it)
	{
		if ( format == (*it).second )
		{
			return (*it).second;
		}
	}

	formatMap().insert( FormatEntry( name, format ) );
	formatAddedSignal()( name );

	return format;
}

const Format &Format::registerFormat( const Format &format )
{
	std::string name;
	generateFormatName( name, format );
	return registerFormat( format, name );
}

void Format::removeFormat( const Format &format )
{
	FormatMap::iterator it( formatMap().begin() );
	FormatMap::iterator end( formatMap().end() );
	for (; it != end; ++it)
	{
		if ( format == (*it).second )
		{
			formatRemovedSignal()( (*it).first );
			formatMap().erase( it );
			return;
		}
	}
}

void Format::removeFormat( const std::string &name )
{
	formatMap().erase( name );
}

Format::UnaryFormatSignal &Format::formatAddedSignal()
{
	static Format::UnaryFormatSignal formatAddedSignalSignal;
	return formatAddedSignalSignal;
}

Format::UnaryFormatSignal &Format::formatRemovedSignal()
{
	static Format::UnaryFormatSignal formatRemovedSignalSignal;
	return formatRemovedSignalSignal;
}

const Format &Format::getFormat( const std::string &name )
{
	FormatMap::iterator it( formatMap().find( name ) );

	if ( it == formatMap().end() )
	{
		std::string err( boost::str( boost::format( "Failed to find format %s" ) % name ) );
		throw IECore::Exception( err );
	}

	return (*it).second;
}

void Format::generateFormatName( std::string &name, const Format &format)
{
	name = boost::str( boost::format( "%dx%d %.3f" ) % format.width() % format.height() % format.getPixelAspect() );
}

void Format::removeAllFormats()
{
	formatMap().clear();
}

int Format::formatCount()
{
	return formatMap().size();
}
