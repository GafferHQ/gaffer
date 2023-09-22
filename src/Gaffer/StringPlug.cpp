//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2015, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/StringPlug.h"

#include "Gaffer/Context.h"
#include "Gaffer/Process.h"
#include "Gaffer/TypedObjectPlug.h"

#include "boost/algorithm/string/join.hpp"

using namespace IECore;
using namespace Gaffer;

GAFFER_PLUG_DEFINE_TYPE( StringPlug );

StringPlug::StringPlug(
	const std::string &name,
	Direction direction,
	const std::string &defaultValue,
	unsigned flags,
	unsigned substitutions
)
	:	ValuePlug( name, direction, new StringData( defaultValue ), flags ), m_substitutions( substitutions )
{
}

StringPlug::~StringPlug()
{
}

unsigned StringPlug::substitutions() const
{
	return m_substitutions;
}

bool StringPlug::acceptsInput( const Plug *input ) const
{
	if( !ValuePlug::acceptsInput( input ) )
	{
		return false;
	}
	if( input )
	{
		return input->isInstanceOf( staticTypeId() ) || input->isInstanceOf( StringVectorDataPlug::staticTypeId() );
	}
	return true;
}

PlugPtr StringPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new StringPlug( name, direction, defaultValue(), getFlags(), substitutions() );
}

const std::string &StringPlug::defaultValue() const
{
	return static_cast<const StringData *>( defaultObjectValue() )->readable();
}

void StringPlug::setValue( const std::string &value )
{
	setObjectValue( new StringData( value ) );
}

void StringPlug::setValue( const char *value )
{
	setObjectValue( new StringData( value ) );
}

void StringPlug::setValue( const std::filesystem::path &value )
{
	setValue( value.generic_string() );
}

std::string StringPlug::getValue() const
{
	ConstStringDataPtr s = getObjectValue<StringData>();

	const bool performSubstitutions =
		m_substitutions &&
		direction() == In &&
		Process::current() &&
		IECore::StringAlgo::hasSubstitutions( s->readable() )
	;

	return performSubstitutions ? Context::current()->substitute( s->readable(), m_substitutions ) : s->readable();
}

void StringPlug::setFrom( const ValuePlug *other )
{
	if( auto stringPlug = IECore::runTimeCast<const StringPlug >( other ) )
	{
		setValue( stringPlug->getValue() );
	}
	else if( auto stringVectorPlug = IECore::runTimeCast<const StringVectorDataPlug >( other ) )
	{
		ConstStringVectorDataPtr data = stringVectorPlug->getValue();
		setValue( boost::algorithm::join( data->readable(), " " ) );
	}
	else
	{
		throw IECore::Exception( "Unsupported plug type" );
	}
}

IECore::MurmurHash StringPlug::hash() const
{
	const bool performSubstitutions =
		m_substitutions &&
		direction() == In
	;

	if( performSubstitutions )
	{
		ConstStringDataPtr s = getObjectValue<StringData>();
		if( IECore::StringAlgo::hasSubstitutions( s->readable() ) )
		{
			IECore::MurmurHash result;
			result.append( Context::current()->substitute( s->readable(), m_substitutions ) );
			return result;
		}
		else
		{
			return s->Object::hash();
		}
	}

	// no substitutions
	return ValuePlug::hash();
}
