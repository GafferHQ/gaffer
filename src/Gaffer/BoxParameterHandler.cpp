//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "Gaffer/BoxParameterHandler.h"

using namespace Gaffer;

template<typename T>
ParameterHandler::ParameterHandlerDescription<BoxParameterHandler<T>, IECore::TypedParameter<T> > BoxParameterHandler<T>::g_description;

template<typename T>
BoxParameterHandler<T>::BoxParameterHandler( typename ParameterType::Ptr parameter, GraphComponentPtr plugParent )
	:	ParameterHandler( parameter )
{
	m_plug = plugParent->getChild<CompoundPlug>( parameter->name() );
	if( !m_plug )
	{
		m_plug = new CompoundPlug();
		plugParent->setChild( parameter->name(), m_plug );
	}
	
	typename PointPlugType::Ptr minPlug = m_plug->getChild<PointPlugType>( "min" );
	if( !minPlug )
	{
		minPlug = new PointPlugType( "min", Plug::In, parameter->typedDefaultValue().min );
		m_plug->addChild( minPlug );
	}
	
	typename PointPlugType::Ptr maxPlug = m_plug->getChild<PointPlugType>( "max" );
	if( !maxPlug )
	{
		maxPlug = new PointPlugType( "max", Plug::In, parameter->typedDefaultValue().max );
		m_plug->addChild( maxPlug );
	}
	
}

template<typename T>
BoxParameterHandler<T>::~BoxParameterHandler()
{
}

template<typename T>
Gaffer::PlugPtr BoxParameterHandler<T>::plug()
{
	return m_plug;
}

template<typename T>
Gaffer::ConstPlugPtr BoxParameterHandler<T>::plug() const
{
	return m_plug;
}
		
template<typename T>
void BoxParameterHandler<T>::setParameterValue()
{
	ParameterType *p = static_cast<ParameterType *>( parameter().get() );

	typename PointPlugType::Ptr minPlug = m_plug->getChild<PointPlugType>( "min" );
	typename PointPlugType::Ptr maxPlug = m_plug->getChild<PointPlugType>( "max" );
	
	p->setTypedValue( T( minPlug->getValue(), maxPlug->getValue() ) );
}

template<typename T>
void BoxParameterHandler<T>::setPlugValue()
{
	const ParameterType *p = static_cast<ParameterType *>( parameter().get() );
	T v = p->getTypedValue();
	
	typename PointPlugType::Ptr minPlug = m_plug->getChild<PointPlugType>( "min" );
	typename PointPlugType::Ptr maxPlug = m_plug->getChild<PointPlugType>( "max" );
	
	minPlug->setValue( v.min );
	maxPlug->setValue( v.max );
}
		
// explicit instantiations

template class BoxParameterHandler<Imath::Box2f>;
template class BoxParameterHandler<Imath::Box3f>;

template class BoxParameterHandler<Imath::Box2i>;
template class BoxParameterHandler<Imath::Box3i>;
