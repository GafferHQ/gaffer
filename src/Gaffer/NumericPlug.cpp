//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/NumericPlug.h"

#include "Gaffer/TypedPlug.h"

#include "OpenEXR/ImathFun.h"

using namespace IECore;
using namespace Gaffer;

template<typename T>
const IECore::RunTimeTyped::TypeDescription<NumericPlug<T> > NumericPlug<T>::g_typeDescription;

namespace Gaffer
{

// RunTimeTyped specialisation
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::IntPlug, IntPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::FloatPlug, FloatPlugTypeId )

}

template<class T>
NumericPlug<T>::NumericPlug(
	const std::string &name,
	Direction direction,
	T defaultValue,
	T minValue,
	T maxValue,
	unsigned flags
)
	:	ValuePlug( name, direction, new DataType( defaultValue ), flags ),
		m_minValue( minValue ),
		m_maxValue( maxValue )
{
}

template<class T>
NumericPlug<T>::~NumericPlug()
{
}

template<class T>
bool NumericPlug<T>::acceptsInput( const Plug *input ) const
{
	if( !ValuePlug::acceptsInput( input ) )
	{
		return false;
	}
	if( input )
	{
		return
			input->isInstanceOf( FloatPlug::staticTypeId() ) ||
			input->isInstanceOf( IntPlug::staticTypeId() ) ||
			input->isInstanceOf( BoolPlug::staticTypeId() )
		;
	}
	return true;
}

template<class T>
PlugPtr NumericPlug<T>::createCounterpart( const std::string &name, Direction direction ) const
{
	return new NumericPlug<T>( name, direction, defaultValue(), minValue(), maxValue(), getFlags() );
}

template<class T>
T NumericPlug<T>::defaultValue() const
{
	return static_cast<const DataType *>( defaultObjectValue() )->readable();
}

template<class T>
bool NumericPlug<T>::hasMinValue() const
{
	return m_minValue!=std::numeric_limits<T>::lowest();
}

template<class T>
bool NumericPlug<T>::hasMaxValue() const
{
	return m_maxValue!=std::numeric_limits<T>::max();
}

template<class T>
T NumericPlug<T>::minValue() const
{
	return m_minValue;
}

template<class T>
T NumericPlug<T>::maxValue() const
{
	return m_maxValue;
}

template<class T>
void NumericPlug<T>::setValue( T value )
{
	value = Imath::clamp( value, m_minValue, m_maxValue );
	setObjectValue( new DataType( value ) );
}

template<class T>
T NumericPlug<T>::getValue( const IECore::MurmurHash *precomputedHash ) const
{
	return getObjectValue<DataType>( precomputedHash )->readable();
}

template<class T>
void NumericPlug<T>::setFrom( const ValuePlug *other )
{
	if( const FloatPlug *p = runTimeCast<const FloatPlug>( other ) )
	{
		setValue( static_cast<T>( p->getValue() ) );
	}
	else if( const IntPlug *p = runTimeCast<const IntPlug>( other ) )
	{
		setValue( static_cast<T>( p->getValue() ) );
	}
	else if( const BoolPlug *p = runTimeCast<const BoolPlug>( other ) )
	{
		setValue( static_cast<T>( p->getValue() ) );
	}
	else
	{
		throw IECore::Exception( "Unsupported plug type" );
	}
}

// explicit instantiation
template class Gaffer::NumericPlug<float>;
template class Gaffer::NumericPlug<int>;
