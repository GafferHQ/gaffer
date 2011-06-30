//////////////////////////////////////////////////////////////////////////
//  
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

#include "Gaffer/CompoundNumericParameterHandler.h"

using namespace Gaffer;

template<typename T>
ParameterHandler::ParameterHandlerDescription<CompoundNumericParameterHandler<T>, IECore::TypedParameter<T> > CompoundNumericParameterHandler<T>::g_description;

template<typename T>
CompoundNumericParameterHandler<T>::CompoundNumericParameterHandler( typename ParameterType::Ptr parameter, GraphComponentPtr plugParent )
	:	ParameterHandler( parameter )
{
	m_plug = plugParent->getChild<PlugType>( parameter->name() );
	if( !m_plug )
	{
		m_plug = new PlugType( parameter->name(), Plug::In, parameter->typedDefaultValue() );
	}
	plugParent->addChild( m_plug );
}

template<typename T>
CompoundNumericParameterHandler<T>::~CompoundNumericParameterHandler()
{
}

template<typename T>
Gaffer::PlugPtr CompoundNumericParameterHandler<T>::plug()
{
	return m_plug;
}

template<typename T>
Gaffer::ConstPlugPtr CompoundNumericParameterHandler<T>::plug() const
{
	return m_plug;
}
		
template<typename T>
void CompoundNumericParameterHandler<T>::setParameterValue()
{
	ParameterType *p = static_cast<ParameterType *>( parameter().get() );
	p->setTypedValue( m_plug->getValue() );
}

template<typename T>
void CompoundNumericParameterHandler<T>::setPlugValue()
{
	const ParameterType *p = static_cast<ParameterType *>( parameter().get() );
	m_plug->setValue( p->getTypedValue() );
}
		
// explicit instantiations

template class CompoundNumericParameterHandler<Imath::V2f>;
template class CompoundNumericParameterHandler<Imath::V3f>;

template class CompoundNumericParameterHandler<Imath::V2i>;
template class CompoundNumericParameterHandler<Imath::V3i>;

template class CompoundNumericParameterHandler<Imath::Color3f>;
template class CompoundNumericParameterHandler<Imath::Color4f>;
