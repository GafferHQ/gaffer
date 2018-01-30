//////////////////////////////////////////////////////////////////////////
//
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

#include "GafferCortex/DateTimeParameterHandler.h"

#include "Gaffer/StringPlug.h"

#include "IECore/Export.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "boost/date_time/posix_time/posix_time.hpp"
IECORE_POP_DEFAULT_VISIBILITY

using namespace GafferCortex;

ParameterHandler::ParameterHandlerDescription<DateTimeParameterHandler, IECore::DateTimeParameter> DateTimeParameterHandler::g_description;

DateTimeParameterHandler::DateTimeParameterHandler( IECore::DateTimeParameterPtr parameter )
	:	m_parameter( parameter )
{
}

DateTimeParameterHandler::~DateTimeParameterHandler()
{
}

IECore::Parameter *DateTimeParameterHandler::parameter()
{
	return m_parameter.get();
}

const IECore::Parameter *DateTimeParameterHandler::parameter() const
{
	return m_parameter.get();
}

void DateTimeParameterHandler::restore( Gaffer::GraphComponent *plugParent )
{
}

Gaffer::Plug *DateTimeParameterHandler::setupPlug( Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, unsigned flags )
{
	m_plug = plugParent->getChild<Gaffer::StringPlug>( m_parameter->name() );
	if( !m_plug || m_plug->direction()!=direction )
	{
		m_plug = new Gaffer::StringPlug( m_parameter->name(), direction, boost::posix_time::to_iso_string( m_parameter->typedDefaultValue() ) );
		plugParent->setChild( m_parameter->name(), m_plug );
	}

	setupPlugFlags( m_plug.get(), flags );

	return m_plug.get();
}

Gaffer::Plug *DateTimeParameterHandler::plug()
{
	return m_plug.get();
}

const Gaffer::Plug *DateTimeParameterHandler::plug() const
{
	return m_plug.get();
}

void DateTimeParameterHandler::setParameterValue()
{
	m_parameter->setTypedValue( boost::posix_time::from_iso_string( m_plug->getValue() ) );
}

void DateTimeParameterHandler::setPlugValue()
{
	m_plug->setValue( boost::posix_time::to_iso_string( m_parameter->getTypedValue() ) );
}
