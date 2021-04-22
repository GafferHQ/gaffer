//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/CompoundNumericPlug.h"

using namespace Gaffer;

template<typename T>
const IECore::RunTimeTyped::TypeDescription<CompoundNumericPlug<T> > CompoundNumericPlug<T>::g_typeDescription;

template<typename T>
CompoundNumericPlug<T>::CompoundNumericPlug(
	const std::string &name,
	Direction direction,
	T defaultValue,
	T minValue,
	T maxValue,
	unsigned flags,
	IECore::GeometricData::Interpretation interpretation
)
	:	ValuePlug( name, direction, flags ), m_interpretation( interpretation )
{
	const char **n = childNames();
	unsigned childFlags = flags & ~Dynamic;
	for( unsigned i=0; i<T::dimensions(); i++ )
	{
		typename ChildType::Ptr p = new ChildType( *n++, direction, defaultValue[i], minValue[i], maxValue[i], childFlags );
		addChild( p );
	}
}

template<typename T>
CompoundNumericPlug<T>::~CompoundNumericPlug()
{
}

template<typename T>
bool CompoundNumericPlug<T>::acceptsChild( const GraphComponent *potentialChild ) const
{
	return children().size() != T::dimensions();
}

template<class T>
PlugPtr CompoundNumericPlug<T>::createCounterpart( const std::string &name, Direction direction ) const
{
	return new CompoundNumericPlug<T>( name, direction, defaultValue(), minValue(), maxValue(), getFlags(), interpretation() );
}

template<typename T>
typename CompoundNumericPlug<T>::ChildType *CompoundNumericPlug<T>::getChild( size_t index )
{
	return GraphComponent::getChild<ChildType>( index );
}

template<typename T>
const typename CompoundNumericPlug<T>::ChildType *CompoundNumericPlug<T>::getChild( size_t index ) const
{
	return GraphComponent::getChild<ChildType>( index );
}

template<typename T>
T CompoundNumericPlug<T>::defaultValue() const
{
	T result;
	for( unsigned i=0; i<T::dimensions(); i++ )
	{
		result[i] = getChild( i )->defaultValue();
	}
	return result;
}

template<typename T>
bool CompoundNumericPlug<T>::hasMinValue() const
{
	for( unsigned i=0; i<T::dimensions(); i++ )
	{
		if( getChild( i )->hasMinValue() )
		{
			return true;
		}
	}
	return false;
}

template<typename T>
bool CompoundNumericPlug<T>::hasMaxValue() const
{
	for( unsigned i=0; i<T::dimensions(); i++ )
	{
		if( getChild( i )->hasMaxValue() )
		{
			return true;
		}
	}
	return false;
}

template<typename T>
T CompoundNumericPlug<T>::minValue() const
{
	T result;
	for( unsigned i=0; i<T::dimensions(); i++ )
	{
		result[i] = getChild( i )->minValue();
	}
	return result;
}

template<typename T>
T CompoundNumericPlug<T>::maxValue() const
{
	T result;
	for( unsigned i=0; i<T::dimensions(); i++ )
	{
		result[i] = getChild( i )->maxValue();
	}
	return result;
}

template<typename T>
void CompoundNumericPlug<T>::setValue( const T &value )
{
	for( unsigned i=0; i<T::dimensions(); i++ )
	{
		getChild( i )->setValue( value[i] );
	}
}

template<typename T>
T CompoundNumericPlug<T>::getValue() const
{
	T result;
	for( unsigned i=0; i<T::dimensions(); i++ )
	{
		result[i] = getChild( i )->getValue();
	}
	return result;
}

template<typename T>
IECore::GeometricData::Interpretation CompoundNumericPlug<T>::interpretation() const
{
	return m_interpretation;
}

template<typename T>
IECore::MurmurHash CompoundNumericPlug<T>::hash() const
{
	IECore::MurmurHash result = ValuePlug::hash();

	if( m_interpretation != IECore::GeometricData::None )
	{
		result.append( m_interpretation );
	}

	return result;
}

template<typename T>
void CompoundNumericPlug<T>::hash( IECore::MurmurHash &h ) const
{
	h.append( hash() );
}

template<typename T>
const char **CompoundNumericPlug<T>::childNames()
{
	static const char *names[] = { "x", "y", "z", "w" };
	return names;
}

template<typename T>
bool CompoundNumericPlug<T>::canGang() const
{
	for( size_t i = 1, e = std::min( (size_t)3, children().size() ); i < e; ++i )
	{
		if( !getChild( i )->acceptsInput( getChild( 0 ) ) )
		{
			return false;
		}
	}
	return true;
}

template<typename T>
void CompoundNumericPlug<T>::gang()
{
	// ignore any 4th children - these are alpha values and ganging them
	// doesn't really make any sense.
	for( size_t i = 1, e = std::min( (size_t)3, children().size() ); i < e; ++i )
	{
		getChild( i )->setInput( getChild( 0 ) );
	}
}

template<typename T>
bool CompoundNumericPlug<T>::isGanged() const
{
	for( size_t i = 1, e = children().size(); i < e; ++i )
	{
		if( const Plug *input = getChild( i )->getInput() )
		{
			if( input->parent<Plug>() == this )
			{
				return true;
			}
		}
	}
	return false;
}

template<typename T>
void CompoundNumericPlug<T>::ungang()
{
	for( size_t i = 1, e = children().size(); i < e; ++i )
	{
		Plug *child = getChild( i );
		if( const Plug *input = child->getInput() )
		{
			if( input->parent<Plug>() == this )
			{
				child->setInput( nullptr );
			}
		}
	}
}

// specialisations

namespace Gaffer
{

template<>
const char **Color3fPlug::childNames()
{
	static const char *names[] = { "r", "g", "b" };
	return names;
}

template<>
const char **Color4fPlug::childNames()
{
	static const char *names[] = { "r", "g", "b", "a" };
	return names;
}

GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::V2fPlug, V2fPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::V3fPlug, V3fPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::V2iPlug, V2iPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::V3iPlug, V3iPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::Color3fPlug, Color3fPlugTypeId )
GAFFER_PLUG_DEFINE_TEMPLATE_TYPE( Gaffer::Color4fPlug, Color4fPlugTypeId )

// explicit instantiations

template class CompoundNumericPlug<Imath::V2f>;
template class CompoundNumericPlug<Imath::V3f>;
template class CompoundNumericPlug<Imath::V2i>;
template class CompoundNumericPlug<Imath::V3i>;
template class CompoundNumericPlug<Imath::Color3f>;
template class CompoundNumericPlug<Imath::Color4f>;

}
