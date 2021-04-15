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

#include "GafferImage/Format.h"

#include <map>

using namespace GafferImage;

namespace
{

typedef std::map<std::string, Format> FormatMap;

FormatMap &formatMap()
{
	static FormatMap map;
	return map;
}

} // namespace

std::ostream &GafferImage::operator << ( std::ostream &os, GafferImage::Format const &format )
{
	if( format.getDisplayWindow().min == Imath::V2i( 0 ) )
	{
		os << format.getDisplayWindow().max.x << "x" << format.getDisplayWindow().max.y;
	}
	else
	{
		os << format.getDisplayWindow().min << " - " << format.getDisplayWindow().max;
	}

	if( format.getPixelAspect() != 1.0 )
	{
		os << ", " << format.getPixelAspect();
	}

	return os;
}

void Format::registerFormat( const std::string &name, const Format &format )
{
	formatMap()[name] = format;
}

void Format::deregisterFormat( const std::string &name )
{
	formatMap().erase( name );
}

void Format::registeredFormats( std::vector<std::string> &names )
{
	const FormatMap &m = formatMap();

	names.clear();
	names.reserve( m.size() );

	for( FormatMap::const_iterator it = m.begin(), eIt = m.end(); it != eIt; ++it )
	{
		names.push_back( it->first );
	}
}

Format Format::format( const std::string &name )
{
	const FormatMap &m = formatMap();
	FormatMap::const_iterator it = m.find( name );
	if( it != m.end() )
	{
		return it->second;
	}
	return Format();
}

std::string Format::name( const Format &format )
{
	const FormatMap &m = formatMap();
	for( FormatMap::const_iterator it = m.begin(), eIt = m.end(); it != eIt; ++it )
	{
		if( it->second == format )
		{
			return it->first;
		}
	}
	return "";
}
