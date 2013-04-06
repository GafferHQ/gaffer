//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "IECore/VectorTypedParameter.h"

#include "Gaffer/VectorTypedParameterHandler.h"

using namespace Gaffer;

template<typename ParameterType>
ParameterHandler::ParameterHandlerDescription<VectorTypedParameterHandler<ParameterType>, ParameterType> VectorTypedParameterHandler<ParameterType>::g_description;

template<typename ParameterType>
VectorTypedParameterHandler<ParameterType>::VectorTypedParameterHandler( typename ParameterType::Ptr parameter )
	:	m_parameter( parameter )
{
}

template<typename ParameterType>
VectorTypedParameterHandler<ParameterType>::~VectorTypedParameterHandler()
{
}

template<typename ParameterType>
IECore::ParameterPtr VectorTypedParameterHandler<ParameterType>::parameter()
{
	return m_parameter;
}

template<typename ParameterType>
IECore::ConstParameterPtr VectorTypedParameterHandler<ParameterType>::parameter() const
{
	return m_parameter;
}

template<typename ParameterType>
void VectorTypedParameterHandler<ParameterType>::restore( GraphComponent *plugParent )
{
}

template<typename ParameterType>
Gaffer::PlugPtr VectorTypedParameterHandler<ParameterType>::setupPlug( GraphComponent *plugParent, Plug::Direction direction )
{
	m_plug = plugParent->getChild<PlugType>( m_parameter->name() );
	if( !m_plug || m_plug->direction()!=direction )
	{
		m_plug = new PlugType( m_parameter->name(), direction, static_cast<const DataType *>( m_parameter->defaultValue() ) );
		plugParent->setChild( m_parameter->name(), m_plug );
	}
	
	setupPlugFlags( m_plug );
	
	return m_plug;
}

template<typename ParameterType>
Gaffer::PlugPtr VectorTypedParameterHandler<ParameterType>::plug()
{
	return m_plug;
}

template<typename ParameterType>
Gaffer::ConstPlugPtr VectorTypedParameterHandler<ParameterType>::plug() const
{
	return m_plug;
}
		
template<typename ParameterType>
void VectorTypedParameterHandler<ParameterType>::setParameterValue()
{
	IECore::ConstObjectPtr o = m_plug->getValue();
	if( o )
	{
		m_parameter->setValue( o->copy() );
	}
	else
	{
		m_parameter->setValue( m_parameter->defaultValue()->copy() );
	}
}

template<typename ParameterType>
void VectorTypedParameterHandler<ParameterType>::setPlugValue()
{
	m_plug->setValue( static_cast<const DataType *>( m_parameter->getValue() ) );
}
		
// explicit instantiations

template class VectorTypedParameterHandler<IECore::BoolVectorParameter>;
template class VectorTypedParameterHandler<IECore::IntVectorParameter>;
template class VectorTypedParameterHandler<IECore::FloatVectorParameter>;
template class VectorTypedParameterHandler<IECore::StringVectorParameter>;
template class VectorTypedParameterHandler<IECore::V3fVectorParameter>;
