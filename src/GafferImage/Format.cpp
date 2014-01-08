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
#include "boost/bind.hpp"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/ApplicationRoot.h"

#include "GafferImage/Format.h"
#include "GafferImage/FormatPlug.h"

using namespace Gaffer;
using namespace GafferImage;

const IECore::InternedString Format::defaultFormatPlugName = "defaultFormat";
const IECore::InternedString Format::defaultFormatContextName = "image:defaultFormat";

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

const Format Format::getDefaultFormat( ScriptNode *scriptNode )
{
	if (!scriptNode)
	{
		throw IECore::Exception("ScriptNode *is NULL");
	}
	const FormatPlug *plug( scriptNode->getChild<FormatPlug>( defaultFormatPlugName ) );
	if (!plug)
	{
		addDefaultFormatPlug( scriptNode );
		plug = scriptNode->getChild<FormatPlug>( defaultFormatPlugName );
	}
	return plug->getValue();
}

void Format::removeAllFormats()
{
	formatMap().clear();
}

int Format::formatCount()
{
	return formatMap().size();
}

void Format::addFormatToContext( Gaffer::Plug *defaultFormatPlug )
{
	Gaffer::Node *n( defaultFormatPlug->node() );
	if ( !n )
	{
		throw IECore::Exception("Plug.node() is NULL");
	}

	if ( n->typeId() == static_cast<IECore::TypeId>( Gaffer::ScriptNodeTypeId )
	     && defaultFormatPlug->typeId() == static_cast<IECore::TypeId>( GafferImage::FormatPlugTypeId )
	)
	{
		Gaffer::ScriptNode *s = static_cast<Gaffer::ScriptNode*>( n );
		GafferImage::FormatPlug *p = static_cast<GafferImage::FormatPlug*>( defaultFormatPlug );
		if ( !p )
		{
			throw IECore::Exception("Plug is not a FormatPlug");
		}
		
		Format f = p->getValue();
		s->context()->set( defaultFormatContextName, f );
	}
}

void Format::addDefaultFormatPlug( ScriptNode *scriptNode )
{
	if (!scriptNode)
	{
		throw IECore::Exception("ScriptNode pointer is NULL");
	}
	
	FormatPlug* plug( scriptNode->getChild<FormatPlug>( defaultFormatPlugName ) );
	
	Format initialFormatValue( 1920, 1080, 1. ); // The initial value that the default format will start with when gaffer is opened.
	
	// If the plug hasn't been created already then it is likely that this script wasn't loaded. We deduce this because the
	// default format plug on the script node is dynamic and therefore if we loaded the script, it would have been created.
	if (!plug)
	{
		registerFormat( initialFormatValue, "HD 1080p 1920x1080 1" );
		
		// Add a new plug to the script node to hold the default format and connect up the valueSet signal to our slot that will add the value to the context.
		FormatPlug *defaultFormatPlug( new FormatPlug( defaultFormatPlugName, Gaffer::Plug::In, Format(), Gaffer::Plug::Dynamic | Gaffer::Plug::Default | Gaffer::Plug::Serialisable ) );
		scriptNode->addChild( defaultFormatPlug );
		scriptNode->plugSetSignal().connect( boost::bind( &Format::addFormatToContext, ::_1 ) );
		defaultFormatPlug->setValue( initialFormatValue );
	}
	// As the plug exists then this could either mean that we have already set up the script node or that the script has been loaded and therefore
	// the plug exists but has not been setup. We can test for the second case by checking to see if the context has the defaultFormat value on it.
	// If we don't find the defaultFormat value on the context then we have to connect up the script node's defaultFormat plug to the addFormatToContext()
	// slot. We also check to see if it has a value other than a NULL format and if it does, we also register it in the format registry.
	else
	{
		if ( scriptNode->context()->get<Format>( Format::defaultFormatContextName, Format() ).getDisplayWindow().isEmpty() ) // Check if the context has a defaultFormat value.
		{
			// It doesn't so pull the one off the script node.
			Format defaultFormatValue( plug->getValue() );
			if ( defaultFormatValue.getDisplayWindow().isEmpty() )
			{
				plug->setValue( initialFormatValue );
			}
			else
			{
				registerFormat( defaultFormatValue );
			}
			
			// Update the context directly to save us the overhead of calling the addFormatToContext() slot via the setValue signal...
			scriptNode->context()->set( defaultFormatContextName, defaultFormatValue );
			scriptNode->plugSetSignal().connect( boost::bind( &Format::addFormatToContext, ::_1 ) );
		}
	}
}

void Format::setDefaultFormat( ScriptNode *scriptNode, const Format &format )
{
	registerFormat( format );
	
	if (!scriptNode)
	{
		throw IECore::Exception("ScriptNode *is NULL");
	}
	
	FormatPlug* plug( scriptNode->getChild<FormatPlug>( defaultFormatPlugName ) );
	if (!plug)
	{
		addDefaultFormatPlug( scriptNode );
		plug = scriptNode->getChild<FormatPlug>( defaultFormatPlugName );
	}
	
	plug->setValue( format );
}

void Format::setDefaultFormat( ScriptNode *scriptNode, const std::string &name )
{
	if (!scriptNode)
	{
		throw IECore::Exception("ScriptNode *is NULL");
	}
	
	FormatPlug* plug( scriptNode->getChild<FormatPlug>( defaultFormatPlugName ) );
	if (!plug)
	{
		addDefaultFormatPlug( scriptNode );
		plug = scriptNode->getChild<FormatPlug>( defaultFormatPlugName );
	}
	
	Format format( getFormat( name ) );
	plug->setValue( format );
}

