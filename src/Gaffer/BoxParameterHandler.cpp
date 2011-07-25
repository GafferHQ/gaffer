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
BoxParameterHandler<T>::BoxParameterHandler( typename ParameterType::Ptr parameter )
	:	m_parameter( parameter )
{
}

template<typename T>
BoxParameterHandler<T>::~BoxParameterHandler()
{
}

template<typename T>
IECore::ParameterPtr BoxParameterHandler<T>::parameter()
{
	return m_parameter;
}

template<typename T>
IECore::ConstParameterPtr BoxParameterHandler<T>::parameter() const
{
	return m_parameter;
}

template<typename T>
Gaffer::PlugPtr BoxParameterHandler<T>::setupPlug( GraphComponentPtr plugParent, Plug::Direction direction )
{
	m_plug = plugParent->getChild<CompoundPlug>( m_parameter->name() );
	if( !m_plug || m_plug->direction()!=direction )
	{
		m_plug = new CompoundPlug( m_parameter->name(), direction );
		plugParent->setChild( m_parameter->name(), m_plug );
	}
	
	typename PointPlugType::Ptr minPlug = m_plug->getChild<PointPlugType>( "min" );
	if( !minPlug || minPlug->direction()!=direction )
	{
		minPlug = new PointPlugType( "min", direction, m_parameter->typedDefaultValue().min );
		m_plug->addChild( minPlug );
	}
	
	typename PointPlugType::Ptr maxPlug = m_plug->getChild<PointPlugType>( "max" );
	if( !maxPlug || maxPlug->direction()!=direction )
	{
		maxPlug = new PointPlugType( "max", direction, m_parameter->typedDefaultValue().max );
		m_plug->addChild( maxPlug );
	}
	
	return m_plug;
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
	typename PointPlugType::Ptr minPlug = m_plug->getChild<PointPlugType>( "min" );
	typename PointPlugType::Ptr maxPlug = m_plug->getChild<PointPlugType>( "max" );
	
	m_parameter->setTypedValue( T( minPlug->getValue(), maxPlug->getValue() ) );
}

template<typename T>
void BoxParameterHandler<T>::setPlugValue()
{
	T v = m_parameter->getTypedValue();
	
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
