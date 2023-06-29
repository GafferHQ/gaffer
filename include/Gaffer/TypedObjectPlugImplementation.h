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

/// This file contains the implementation of TypedObjectPlug. Rather than include it
/// in a public header it is #included in TypedObjectPlug.cpp, and the relevant template
/// classes are explicitly instantiated there. This prevents a host of problems to do with
/// the definition of the same symbols in multiple object files. Additional TypedObjectPlug
/// instantations may be created in similar .cpp files in other libraries.

namespace Gaffer
{

template<class T>
const IECore::RunTimeTyped::TypeDescription<TypedObjectPlug<T> > TypedObjectPlug<T>::g_typeDescription;

template<class T>
TypedObjectPlug<T>::TypedObjectPlug(
	const std::string &name,
	Direction direction,
	ConstValuePtr defaultValue,
	unsigned flags
)
	:	ValuePlug( name, direction, defaultValue->copy(), flags )
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
	return static_cast<const ValueType *>( defaultObjectValue() );
}

template<class T>
void TypedObjectPlug<T>::setValue( ConstValuePtr value )
{
	setObjectValue( value );
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

} // namespace Gaffer
