//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/NameValuePlug.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/StringPlug.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( NameValuePlug );

NameValuePlug::NameValuePlug( const std::string &name, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags )
{
}

NameValuePlug::NameValuePlug( const std::string &nameDefault, const IECore::Data *valueDefault, const std::string &name, Direction direction, unsigned flags )
	:	NameValuePlug( nameDefault, PlugAlgo::createPlugFromData( "value", direction, flags, valueDefault ).get(), name )
{
}

NameValuePlug::NameValuePlug( const std::string &nameDefault, Gaffer::ValuePlugPtr valuePlug, const std::string &name )
	:	NameValuePlug( name, valuePlug->direction(), valuePlug->getFlags() )
{
	addChild( new StringPlug( "name", valuePlug->direction(), nameDefault, valuePlug->getFlags() ) );

	valuePlug->setName( "value" );
	addChild( valuePlug );
}

NameValuePlug::NameValuePlug( const std::string &nameDefault, const IECore::Data *valueDefault, bool enabled, const std::string &name, Direction direction, unsigned flags )
	:	NameValuePlug( nameDefault, valueDefault, name, direction, flags )
{
	addChild( new BoolPlug( "enabled", direction, enabled ) );
}

NameValuePlug::NameValuePlug( const std::string &nameDefault, Gaffer::ValuePlugPtr valuePlug, bool enabled, const std::string &name )
	:	NameValuePlug( nameDefault, valuePlug, name )
{
	addChild( new BoolPlug( "enabled", valuePlug->direction(), enabled, valuePlug->getFlags() ) );
}

// We need to check if the namePlug exists because we offer a bare constructor that leaves the child plugs
// uninitialized, for backwards compatibility with the deprecated CompoundDataPlug.MemberPlug
StringPlug *NameValuePlug::namePlug()
{
	return children().size() > 0 ? getChild<StringPlug>( 0 ) : nullptr;
}

const StringPlug *NameValuePlug::namePlug() const
{
	return children().size() > 0 ? getChild<StringPlug>( 0 ) : nullptr;
}

BoolPlug *NameValuePlug::enabledPlug()
{
	return children().size() > 2 ? getChild<BoolPlug>( 2 ) : nullptr;
}

const BoolPlug *NameValuePlug::enabledPlug() const
{
	return children().size() > 2 ? getChild<BoolPlug>( 2 ) : nullptr;
}

bool NameValuePlug::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	if( !ValuePlug::acceptsChild( potentialChild ) )
	{
		return false;
	}

	if(
		
		potentialChild->isInstanceOf( StringPlug::staticTypeId() ) &&
		potentialChild->getName() == "name" &&
		( children().size() == 0 )
	)
	{
		return true;
	}
	else if(
		potentialChild->getName() == "value" &&
		( children().size() == 1 ) &&
		namePlug()
	)
	{
		return true;
	}
	else if(
		potentialChild->isInstanceOf( BoolPlug::staticTypeId() ) &&
		potentialChild->getName() == "enabled" &&
		( children().size() == 2 ) &&
		namePlug() &&
		valuePlug()
	)
	{
		return true;
	}

	return false;
}

PlugPtr NameValuePlug::createCounterpart( const std::string &name, Direction direction ) const
{
	if( !namePlug() || !valuePlug() )
	{
		throw IECore::Exception( "Cannot create counterpart for : " + fullName() + " - NameValuePlug must have name and value." );
	}

	ValuePlugPtr valueCounterpart = IECore::runTimeCast<ValuePlug>(
		valuePlug()->createCounterpart( "value", direction ).get()
	);

	if( enabledPlug() )
	{
		return new NameValuePlug(
			namePlug()->defaultValue(), valueCounterpart, enabledPlug()->defaultValue(), name
		);
	}
	else
	{
		return new NameValuePlug(
			namePlug()->defaultValue(), valueCounterpart, name
		);
	}
}
