//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/NumericPlug.h"

#include "GafferCortex/TimeCodeParameterHandler.h"

using namespace GafferCortex;

ParameterHandler::ParameterHandlerDescription<TimeCodeParameterHandler, IECore::TimeCodeParameter> TimeCodeParameterHandler::g_description;


TimeCodeParameterHandler::TimeCodeParameterHandler( IECore::TimeCodeParameterPtr parameter )
	:	m_parameter( parameter )
{
}

TimeCodeParameterHandler::~TimeCodeParameterHandler()
{
}

IECore::Parameter *TimeCodeParameterHandler::parameter()
{
	return m_parameter.get();
}

const IECore::Parameter *TimeCodeParameterHandler::parameter() const
{
	return m_parameter.get();
}

void TimeCodeParameterHandler::restore( Gaffer::GraphComponent *plugParent )
{
}

Gaffer::Plug *TimeCodeParameterHandler::setupPlug( Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, unsigned flags )
{
	m_plug = plugParent->getChild<Gaffer::CompoundPlug>( m_parameter->name() );
	if( !m_plug || m_plug->direction()!=direction )
	{
		m_plug = new Gaffer::CompoundPlug( m_parameter->name(), direction );
		plugParent->setChild( m_parameter->name(), m_plug );
	}

	setupPlugFlags( m_plug.get(), flags );
	setupPlugMetadata( m_plug.get(), m_parameter.get() );

	Gaffer::IntPlugPtr hoursPlug = m_plug->getChild<Gaffer::IntPlug>( "hours" );
	if( !hoursPlug || hoursPlug->direction() != direction )
	{
		hoursPlug = new Gaffer::IntPlug( "hours", direction, m_parameter->typedDefaultValue().hours(), 0, 23 );
		m_plug->setChild( "hours", hoursPlug );
	}

	Gaffer::IntPlugPtr minutesPlug = m_plug->getChild<Gaffer::IntPlug>( "minutes" );
	if( !minutesPlug || minutesPlug->direction() != direction )
	{
		minutesPlug = new Gaffer::IntPlug( "minutes", direction, m_parameter->typedDefaultValue().minutes(), 0, 59 );
		m_plug->setChild( "minutes", minutesPlug );
	}

	Gaffer::IntPlugPtr secondsPlug = m_plug->getChild<Gaffer::IntPlug>( "seconds" );
	if( !secondsPlug || secondsPlug->direction() != direction )
	{
		secondsPlug = new Gaffer::IntPlug( "seconds", direction, m_parameter->typedDefaultValue().seconds(), 0, 59 );
		m_plug->setChild( "seconds", secondsPlug );
	}

	Gaffer::IntPlugPtr framePlug = m_plug->getChild<Gaffer::IntPlug>( "frame" );
	if( !framePlug || framePlug->direction() != direction )
	{
		framePlug = new Gaffer::IntPlug( "frame", direction, m_parameter->typedDefaultValue().frame(), 0, 29 );
		m_plug->setChild( "frame", framePlug );
	}

	return m_plug.get();
}

Gaffer::Plug *TimeCodeParameterHandler::plug()
{
	return m_plug.get();
}

const Gaffer::Plug *TimeCodeParameterHandler::plug() const
{
	return m_plug.get();
}

void TimeCodeParameterHandler::setParameterValue()
{
	// start with parameter value to preserve information we don't put in plugs
	Imf::TimeCode tc = m_parameter->getTypedValue();
	tc.setHours( m_plug->getChild<Gaffer::IntPlug>( "hours" )->getValue() );
	tc.setMinutes( m_plug->getChild<Gaffer::IntPlug>( "minutes" )->getValue() );
	tc.setSeconds( m_plug->getChild<Gaffer::IntPlug>( "seconds" )->getValue() );
	tc.setFrame( m_plug->getChild<Gaffer::IntPlug>( "frame" )->getValue() );
	m_parameter->setTypedValue( tc );
}

void TimeCodeParameterHandler::setPlugValue()
{
	Imf::TimeCode tc = m_parameter->getTypedValue();
	m_plug->getChild<Gaffer::IntPlug>( "hours" )->setValue( tc.hours() );
	m_plug->getChild<Gaffer::IntPlug>( "minutes" )->setValue( tc.minutes() );
	m_plug->getChild<Gaffer::IntPlug>( "seconds" )->setValue( tc.seconds() );
	m_plug->getChild<Gaffer::IntPlug>( "frame" )->setValue( tc.frame() );
}
