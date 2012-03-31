//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/TypedPlug.h"

#include "OpenEXR/ImathFun.h"

using namespace Gaffer;

template<class T>
const IECore::RunTimeTyped::TypeDescription<TypedPlug<T> > TypedPlug<T>::g_typeDescription;

template<class T>
TypedPlug<T>::TypedPlug(
	const std::string &name,
	Direction direction,
	const T &defaultValue,
	unsigned flags
)
	:	ValuePlug( name, direction, flags ),
		m_defaultValue( defaultValue )
{
}

template<class T>
TypedPlug<T>::~TypedPlug()
{
}

template<class T>
bool TypedPlug<T>::acceptsInput( ConstPlugPtr input ) const
{
	if( !ValuePlug::acceptsInput( input ) )
	{
		return false;
	}
	if( input )
	{
		return input->isInstanceOf( staticTypeId() );
	}
	return true;
}

template<class T>
const T &TypedPlug<T>::defaultValue() const
{
	return m_defaultValue;
}
		
template<class T>
void TypedPlug<T>::setValue( const T &value )
{
	setObjectValue( new DataType( value ) );
}

template<class T>
T TypedPlug<T>::getValue() const
{
	IECore::ConstObjectPtr o = getObjectValue();
	if( o )
	{
		return static_cast<const DataType *>( o.get() )->readable();
	}
	return m_defaultValue;
}

template<class T>
void TypedPlug<T>::setFrom( const ValuePlug *other )
{
	const TypedPlug<T> *tOther = IECore::runTimeCast<const TypedPlug<T> >( other );
	if( tOther )
	{
		setValue( tOther->getValue() );
	}
	else
	{
		throw IECore::Exception( "Unsupported plug type" );
	}
}

namespace Gaffer
{

IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( BoolPlug, BoolPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( StringPlug, StringPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( M33fPlug, M33fPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( M44fPlug, M44fPlugTypeId )

}

// explicit instantiation
template class TypedPlug<bool>;
template class TypedPlug<std::string>;
template class TypedPlug<Imath::M33f>;
template class TypedPlug<Imath::M44f>;
