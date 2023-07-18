//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "Gaffer/OptionalValuePlug.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;

GAFFER_PLUG_DEFINE_TYPE( OptionalValuePlug );

OptionalValuePlug::OptionalValuePlug( IECore::InternedString name, const Gaffer::ValuePlugPtr &valuePlug, bool enabledPlugDefaultValue, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags )
{
	addChild( new BoolPlug( "enabled", direction, enabledPlugDefaultValue ) );
	setChild( "value", valuePlug );
}

Gaffer::BoolPlug *OptionalValuePlug::enabledPlug()
{
	return getChild<BoolPlug>( 0 );
}

const Gaffer::BoolPlug *OptionalValuePlug::enabledPlug() const
{
	return getChild<BoolPlug>( 0 );
}

bool OptionalValuePlug::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	return ValuePlug::acceptsChild( potentialChild ) && children().size() < 2;
}

PlugPtr OptionalValuePlug::createCounterpart( const std::string &name, Direction direction ) const
{
	ValuePlugPtr valueCounterpart = boost::static_pointer_cast<ValuePlug>(
		valuePlug()->createCounterpart( "value", direction )
	);
	return new OptionalValuePlug(
		name, valueCounterpart, enabledPlug()->defaultValue(), direction, getFlags()
	);
}
