//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/TypedObjectPlug.h"

using namespace Gaffer;

template<class T>
const IECore::RunTimeTyped::TypeDescription<TypedObjectPlug<T> > TypedObjectPlug<T>::g_typeDescription;

template<class T>
TypedObjectPlug<T>::TypedObjectPlug(
	const std::string &name,
	Direction direction,
	ConstValuePtr defaultValue,
	unsigned flags
)
	:	ValuePlug( name, direction, defaultValue->copy(), flags ),
		m_defaultValue( defaultValue->copy() )
{
}

template<class T>
TypedObjectPlug<T>::~TypedObjectPlug()
{
}

template<class T>
bool TypedObjectPlug<T>::acceptsInput( const Plug *input ) const
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
PlugPtr TypedObjectPlug<T>::createCounterpart( const std::string &name, Direction direction ) const
{
	return new TypedObjectPlug<T>( name, direction, defaultValue(), getFlags() );
}

template<class T>
const typename TypedObjectPlug<T>::ValueType *TypedObjectPlug<T>::defaultValue() const
{
	return m_defaultValue.get();
}

template<class T>
void TypedObjectPlug<T>::setValue( ConstValuePtr value )
{
	setObjectValue( value );
}

template<class T>
typename TypedObjectPlug<T>::ConstValuePtr TypedObjectPlug<T>::getValue() const
{
	return boost::static_pointer_cast<const ValueType>( getObjectValue() );
}

template<class T>
void TypedObjectPlug<T>::setToDefault()
{
	setValue( m_defaultValue );
}

template<class T>
void TypedObjectPlug<T>::setFrom( const ValuePlug *other )
{
	const TypedObjectPlug<T> *tOther = IECore::runTimeCast<const TypedObjectPlug>( other );
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

IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::ObjectPlug, ObjectPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::BoolVectorDataPlug, BoolVectorDataPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::IntVectorDataPlug, IntVectorDataPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::FloatVectorDataPlug, FloatVectorDataPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::StringVectorDataPlug, StringVectorDataPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::InternedStringVectorDataPlug, InternedStringVectorDataPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::V3fVectorDataPlug, V3fVectorDataPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::Color3fVectorDataPlug, Color3fVectorDataPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::ObjectVectorPlug, ObjectVectorPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::CompoundObjectPlug, CompoundObjectPlugTypeId )

}

// explicit instantiation
template class TypedObjectPlug<IECore::Object>;
template class TypedObjectPlug<IECore::BoolVectorData>;
template class TypedObjectPlug<IECore::IntVectorData>;
template class TypedObjectPlug<IECore::FloatVectorData>;
template class TypedObjectPlug<IECore::StringVectorData>;
template class TypedObjectPlug<IECore::InternedStringVectorData>;
template class TypedObjectPlug<IECore::V3fVectorData>;
template class TypedObjectPlug<IECore::Color3fVectorData>;
template class TypedObjectPlug<IECore::ObjectVector>;
template class TypedObjectPlug<IECore::CompoundObject>;
