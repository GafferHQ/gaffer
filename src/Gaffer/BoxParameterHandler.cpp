//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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
IECore::Parameter *BoxParameterHandler<T>::parameter()
{
	return m_parameter.get();
}

template<typename T>
const IECore::Parameter *BoxParameterHandler<T>::parameter() const
{
	return m_parameter.get();
}

template<typename T>
void BoxParameterHandler<T>::restore( GraphComponent *plugParent )
{
}

template<typename T>
Gaffer::Plug *BoxParameterHandler<T>::setupPlug( GraphComponent *plugParent, Plug::Direction direction, unsigned flags )
{
	m_plug = plugParent->getChild<PlugType>( m_parameter->name() );
	if( !m_plug || m_plug->direction()!=direction )
	{
		m_plug = new PlugType( m_parameter->name(), direction, m_parameter->typedDefaultValue() );
		plugParent->setChild( m_parameter->name(), m_plug );
	}

	setupPlugFlags( m_plug.get(), flags );

	return m_plug.get();
}

template<typename T>
Gaffer::Plug *BoxParameterHandler<T>::plug()
{
	return m_plug.get();
}

template<typename T>
const Gaffer::Plug *BoxParameterHandler<T>::plug() const
{
	return m_plug.get();
}

template<typename T>
void BoxParameterHandler<T>::setParameterValue()
{
	m_parameter->setTypedValue( m_plug->getValue() );
}

template<typename T>
void BoxParameterHandler<T>::setPlugValue()
{
	m_plug->setValue( m_parameter->getTypedValue() );
}

// explicit instantiations

template class BoxParameterHandler<Imath::Box2f>;
template class BoxParameterHandler<Imath::Box3f>;

template class BoxParameterHandler<Imath::Box2i>;
template class BoxParameterHandler<Imath::Box3i>;
