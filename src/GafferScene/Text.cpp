//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, John Haddon. All rights reserved.
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

#include "GafferScene/Text.h"

#include "Gaffer/StringPlug.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECoreScene/Font.h"
#include "IECoreScene/MeshPrimitive.h"

#include "IECore/SearchPath.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;

//////////////////////////////////////////////////////////////////////////
// Implementation of an LRUCache of Fonts.
//////////////////////////////////////////////////////////////////////////

namespace GafferScene
{

namespace Detail
{

FontPtr fontGetter( const std::string &fileName, size_t &cost )
{
	const char *e = getenv( "IECORE_FONT_PATHS" );
	IECore::SearchPath sp( e ? e : "" );

	std::string resolvedFileName = sp.find( fileName ).string();
	if( !resolvedFileName.size() )
	{
		throw Exception( "Unable to find font" );
	}

	cost = 1;
	return new Font( resolvedFileName );
}

typedef IECorePreview::LRUCache<std::string, FontPtr> FontCache;

FontCache *fontCache()
{
	static FontCache *c = new FontCache( fontGetter, 200 );
	return c;
}

} // namespace Detail

} // namespace GafferScene

//////////////////////////////////////////////////////////////////////////
// Text implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Text );

size_t Text::g_firstPlugIndex = 0;

Text::Text( const std::string &name )
	:	ObjectSource( name, "text" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "text", Plug::In, "Hello World" ) );
	addChild( new StringPlug( "font", Plug::In, "Vera.ttf" ) );
}

Text::~Text()
{
}

Gaffer::StringPlug *Text::textPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Text::textPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *Text::fontPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *Text::fontPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

void Text::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if( input == textPlug() || input == fontPlug() )
	{
		outputs.push_back( sourcePlug() );
	}
}

void Text::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	textPlug()->hash( h );
	fontPlug()->hash( h );
}

IECore::ConstObjectPtr Text::computeSource( const Context *context ) const
{
	std::string fontFileName = fontPlug()->getValue();
	std::string text = textPlug()->getValue();
	if( !text.size() || !fontFileName.size() )
	{
		return outPlug()->objectPlug()->defaultValue();
	}

	FontPtr font = Detail::fontCache()->get( fontFileName );
	return font->mesh( text );
}
