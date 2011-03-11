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

#include "IECore/MessageHandler.h"

#include "Gaffer/CompoundParameterHandler.h"
#include "Gaffer/CompoundPlug.h"

using namespace Gaffer;
using namespace IECore;

ParameterHandler::ParameterHandlerDescription<CompoundParameterHandler, IECore::CompoundParameter> CompoundParameterHandler::g_description;

CompoundParameterHandler::CompoundParameterHandler( IECore::CompoundParameterPtr parameter, GraphComponentPtr plugParent )
	:	ParameterHandler( parameter )
{
	
	std::string plugName = parameter->name();
	if( plugName=="" )
	{
		// the top level compound parameter on Parameterised classes usually has an empty name.
		// there's probably a good case for forcing that name to always be "parameters" instead
		// of doing what we do here.
		plugName = "parameters";
	}
	
	m_plug = plugParent->getChild<CompoundPlug>( plugName );
	if( !m_plug )
	{
		m_plug = new CompoundPlug( plugName );
		plugParent->addChild( m_plug ); /// \todo need to be able to replace what's already there
	}
	
	const CompoundParameter::ParameterVector &children = parameter->orderedParameters();
	for( CompoundParameter::ParameterVector::const_iterator it = children.begin(); it!=children.end(); it++ )
	{
		handler( *it );
	}
	
}

CompoundParameterHandler::~CompoundParameterHandler()
{
}

void CompoundParameterHandler::setParameterValue()
{
	const CompoundParameter *p = static_cast<const CompoundParameter *>( parameter().get() );
	const CompoundParameter::ParameterVector &children = p->orderedParameters();
	for( CompoundParameter::ParameterVector::const_iterator it = children.begin(); it!=children.end(); it++ )
	{
		ParameterHandlerPtr h = handler( *it );
		h->setParameterValue();
	}
}

void CompoundParameterHandler::setPlugValue()
{
	const CompoundParameter *p = static_cast<const CompoundParameter *>( parameter().get() );
	const CompoundParameter::ParameterVector &children = p->orderedParameters();
	for( CompoundParameter::ParameterVector::const_iterator it = children.begin(); it!=children.end(); it++ )
	{
		ParameterHandlerPtr h = handler( *it );
		h->setPlugValue();
	}
}

ParameterHandlerPtr CompoundParameterHandler::handler( const ParameterPtr child  )
{
	HandlerMap::const_iterator it = m_handlers.find( child->internedName() );
	if( it!=m_handlers.end() )
	{
		return it->second;
	}
	
	ParameterHandlerPtr h = ParameterHandler::create( child, m_plug );
	if( !h )
	{
		IECore::msg( IECore::Msg::Warning, "Gaffer::CompoundParameterHandler", boost::format(  "Unable to create handler for parameter \"%s\" of type \"%s\"" ) % child->name() % child->typeName() );
	}
	
	m_handlers[child->internedName()] = h;
	return h;
}
