//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "GafferCortex/ObjectParameterHandler.h"

#include "IECore/ObjectParameter.h"

using namespace GafferCortex;

ParameterHandler::ParameterHandlerDescription<ObjectParameterHandler, IECore::ObjectParameter> ObjectParameterHandler::g_description;

ObjectParameterHandler::ObjectParameterHandler( IECore::ObjectParameterPtr parameter )
	:	m_parameter( parameter )
{
}

ObjectParameterHandler::~ObjectParameterHandler()
{
}

IECore::Parameter *ObjectParameterHandler::parameter()
{
	return m_parameter.get();
}

const IECore::Parameter *ObjectParameterHandler::parameter() const
{
	return m_parameter.get();
}

void ObjectParameterHandler::restore( Gaffer::GraphComponent *plugParent )
{
}

Gaffer::Plug *ObjectParameterHandler::setupPlug( Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, unsigned flags )
{
	m_plug = plugParent->getChild<Gaffer::ObjectPlug>( m_parameter->name() );
	if( !m_plug || m_plug->direction()!=direction )
	{
		m_plug = new Gaffer::ObjectPlug( m_parameter->name(), direction, m_parameter->defaultValue() );
		plugParent->setChild( m_parameter->name(), m_plug );
	}

	setupPlugFlags( m_plug.get(), flags );

	return m_plug.get();
}

Gaffer::Plug *ObjectParameterHandler::plug()
{
	return m_plug.get();
}

const Gaffer::Plug *ObjectParameterHandler::plug() const
{
	return m_plug.get();
}

void ObjectParameterHandler::setParameterValue()
{
	IECore::ConstObjectPtr o = m_plug->getValue();
	m_parameter->setValue( o->copy() );
}

void ObjectParameterHandler::setPlugValue()
{
	m_plug->setValue( m_parameter->getValue() );
}
