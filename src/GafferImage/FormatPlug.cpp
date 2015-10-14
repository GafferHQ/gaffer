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

#include "GafferImage/FormatPlug.h"

using namespace Gaffer;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( FormatPlug );

FormatPlug::FormatPlug( const std::string &name, Direction direction, Format defaultValue, unsigned flags )
	:	ValuePlug( name, direction, flags ), m_defaultValue( defaultValue )
{
	const unsigned childFlags = flags & ~Dynamic;
	addChild( new Box2iPlug( "displayWindow", direction, defaultValue.getDisplayWindow(), childFlags ) );
	addChild( new FloatPlug( "pixelAspect", direction, defaultValue.getPixelAspect(), Imath::limits<float>::min(), Imath::limits<float>::max(), childFlags ) );
}

FormatPlug::~FormatPlug()
{
}

bool FormatPlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	return children().size() < 2;
}

Gaffer::PlugPtr FormatPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new FormatPlug( name, direction, defaultValue(), getFlags() );
}

Gaffer::Box2iPlug *FormatPlug::displayWindowPlug()
{
	return getChild<Box2iPlug>( 0 );
}

const Gaffer::Box2iPlug *FormatPlug::displayWindowPlug() const
{
	return getChild<Box2iPlug>( 0 );
}

Gaffer::FloatPlug *FormatPlug::pixelAspectPlug()
{
	return getChild<FloatPlug>( 1 );
}

const Gaffer::FloatPlug *FormatPlug::pixelAspectPlug() const
{
	return getChild<FloatPlug>( 1 );
}

const Format &FormatPlug::defaultValue() const
{
	return m_defaultValue;
}

void FormatPlug::setValue( const Format &value )
{
	displayWindowPlug()->setValue( value.getDisplayWindow() );
	pixelAspectPlug()->setValue( value.getPixelAspect() );
}

Format FormatPlug::getValue() const
{
	return Format( displayWindowPlug()->getValue(), pixelAspectPlug()->getValue() );
}
