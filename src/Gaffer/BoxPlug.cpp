//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "Gaffer/BoxPlug.h"

using namespace Gaffer;

template<typename T>
const IECore::RunTimeTyped::TypeDescription<BoxPlug<T> > BoxPlug<T>::g_typeDescription;

template<typename T>
BoxPlug<T>::BoxPlug(
	const std::string &name,
	Direction direction,
	T defaultValue,
	unsigned flags
)
	:	CompoundPlug( name, direction, flags )
{
	const unsigned childFlags = flags & ~Dynamic;
	addChild(
		new ChildType(
			"min", direction,
			defaultValue.min,
			typename ChildType::ValueType( Imath::limits<typename ChildType::ValueType::BaseType>::min() ),
			typename ChildType::ValueType( Imath::limits<typename ChildType::ValueType::BaseType>::max() ),
			childFlags
		)
	);
	
	addChild(
		new ChildType(
			"max", direction,
			defaultValue.max,
			typename ChildType::ValueType( Imath::limits<typename ChildType::ValueType::BaseType>::min() ),
			typename ChildType::ValueType( Imath::limits<typename ChildType::ValueType::BaseType>::max() ),
			childFlags
		)
	);
}

template<typename T>
BoxPlug<T>::~BoxPlug()
{
}

template<typename T>
bool BoxPlug<T>::acceptsChild( const GraphComponent *potentialChild ) const
{
	return children().size() != 2;
}

template<typename T>
PlugPtr BoxPlug<T>::createCounterpart( const std::string &name, Direction direction ) const
{
	return new BoxPlug<T>( name, direction, defaultValue(), getFlags() );
}

template<typename T>
typename BoxPlug<T>::ChildType *BoxPlug<T>::min()
{
	return getChild<ChildType>( 0 );
}

template<typename T>
const typename BoxPlug<T>::ChildType *BoxPlug<T>::min() const
{
	return getChild<ChildType>( 0 );
}

template<typename T>
typename BoxPlug<T>::ChildType *BoxPlug<T>::max()
{
	return getChild<ChildType>( 1 );
}

template<typename T>
const typename BoxPlug<T>::ChildType *BoxPlug<T>::max() const
{
	return getChild<ChildType>( 1 );
}

template<typename T>
T BoxPlug<T>::defaultValue() const
{
	return T( this->min()->defaultValue(), this->max()->defaultValue() );
}

template<typename T>
void BoxPlug<T>::setValue( const T &value )
{
	this->min()->setValue( value.min );
	this->max()->setValue( value.max );	
}

template<typename T>
T BoxPlug<T>::getValue() const
{
	return T( this->min()->getValue(), this->max()->getValue() );
}

// specialisations

namespace Gaffer
{

IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::Box2iPlug, Box2iPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::Box3iPlug, Box3iPlugTypeId )

IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::Box2fPlug, Box2fPlugTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::Box3fPlug, Box3fPlugTypeId )

}

// explicit instantiations

template class BoxPlug<Imath::Box2i>;
template class BoxPlug<Imath::Box3i>;
template class BoxPlug<Imath::Box2f>;
template class BoxPlug<Imath::Box3f>;
