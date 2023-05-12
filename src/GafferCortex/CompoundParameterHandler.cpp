//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferCortex/CompoundParameterHandler.h"

#include "Gaffer/ValuePlug.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

#include "boost/container/flat_set.hpp"

#include "fmt/format.h"

using namespace IECore;
using namespace GafferCortex;

ParameterHandler::ParameterHandlerDescription<CompoundParameterHandler, IECore::CompoundParameter> CompoundParameterHandler::g_description;

CompoundParameterHandler::CompoundParameterHandler( IECore::CompoundParameterPtr parameter )
	:	m_parameter( parameter )
{
}

CompoundParameterHandler::~CompoundParameterHandler()
{
}

IECore::Parameter *CompoundParameterHandler::parameter()
{
	return m_parameter.get();
}

const IECore::Parameter *CompoundParameterHandler::parameter() const
{
	return m_parameter.get();
}

void CompoundParameterHandler::restore( Gaffer::GraphComponent *plugParent )
{
	Gaffer::Plug *compoundPlug = plugParent->getChild<Gaffer::Plug>( plugName() );
	if( !compoundPlug )
	{
		return;
	}

	// call restore for our child handlers

	const CompoundParameter::ParameterVector &children = m_parameter->orderedParameters();
	for( CompoundParameter::ParameterVector::const_iterator it = children.begin(); it!=children.end(); it++ )
	{
		ParameterHandler *h = handler( it->get(), true );
		if( h )
		{
			h->restore( compoundPlug );
		}
	}

}

Gaffer::Plug *CompoundParameterHandler::setupPlug( Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, unsigned flags )
{
	// decide what name our plug should have

	std::string name = plugName();

	// create the plug if necessary

	m_plug = plugParent->getChild<Gaffer::Plug>( name );
	if( !m_plug || m_plug->direction()!=direction )
	{
		m_plug = new Gaffer::Plug( name, direction );
		plugParent->setChild( name, m_plug );
	}

	setupPlugFlags( m_plug.get(), flags );

	// loop through the handlers and remove any that are not linked to a new parameter
	const CompoundParameter::ParameterVector &children = m_parameter->orderedParameters();

	// using a flat_set for fast searches
	boost::container::flat_set<IECore::ParameterPtr> searchParameters(children.begin(), children.end());

	std::vector<Gaffer::PlugPtr> toRemove;
	for( HandlerMap::iterator it = m_handlers.begin(), eIt = m_handlers.end(); it!=eIt; )
	{
		HandlerMap::iterator nextIt = it; nextIt++; // increment now because removing will invalidate iterator
		if( searchParameters.find( it->first ) == searchParameters.end() )
		{
			toRemove.push_back( it->second->plug() );
			m_handlers.erase( it );
		}
		it = nextIt;
	}

	// remove the old plugs
	for( std::vector<Gaffer::PlugPtr>::const_iterator pIt = toRemove.begin(), eIt = toRemove.end(); pIt != eIt; pIt++ )
	{
		m_plug->removeChild( *pIt );
	}

	// loop through the new parameters, adding handlers to them
	for( CompoundParameter::ParameterVector::const_iterator it = children.begin(); it!=children.end(); it++ )
	{
		ParameterHandler *h = handler( it->get(), true );
		if( h )
		{
			h->setupPlug( m_plug.get(), direction, flags );
		}
	}

	return m_plug.get();
}

Gaffer::Plug *CompoundParameterHandler::plug()
{
	return m_plug.get();
}

const Gaffer::Plug *CompoundParameterHandler::plug() const
{
	return m_plug.get();
}

void CompoundParameterHandler::setParameterValue()
{
	const CompoundParameter::ParameterVector &children = m_parameter->orderedParameters();
	for( CompoundParameter::ParameterVector::const_iterator it = children.begin(); it!=children.end(); it++ )
	{
		ParameterHandler *h = handler( it->get() );
		if( h )
		{
			h->setParameterValue();
		}
	}
}

void CompoundParameterHandler::setPlugValue()
{
	const CompoundParameter::ParameterVector &children = m_parameter->orderedParameters();
	for( CompoundParameter::ParameterVector::const_iterator it = children.begin(); it!=children.end(); it++ )
	{
		if( ParameterHandler *h = handler( it->get() ) )
		{
			if( Gaffer::ValuePlug *plug = IECore::runTimeCast<Gaffer::ValuePlug>( h->plug() ) )
			{
				if( plug->settable() )
				{
					h->setPlugValue();
				}
			}
			else
			{
				h->setPlugValue();
			}
		}
	}
}

std::string CompoundParameterHandler::plugName() const
{
	std::string result = m_parameter->name();
	if( result=="" )
	{
		// the top level compound parameter on Parameterised classes usually has an empty name.
		// there's probably a good case for forcing that name to always be "parameters" instead
		// of doing what we do here.
		result = "parameters";
	}
	return result;
}

ParameterHandler *CompoundParameterHandler::childParameterHandler( IECore::Parameter *childParameter )
{
	return handler( childParameter );
}

const ParameterHandler *CompoundParameterHandler::childParameterHandler( IECore::Parameter *childParameter ) const
{
	// cast is ok, as when passing createIfMissing==false to handler() we don't modify any member data
	return const_cast<CompoundParameterHandler *>( this )->handler( childParameter );
}

IECore::RunTimeTyped *CompoundParameterHandler::childParameterProvider( IECore::Parameter *childParameter )
{
	return nullptr;
}

ParameterHandler *CompoundParameterHandler::handler( Parameter *child, bool createIfMissing )
{
	HandlerMap::const_iterator it = m_handlers.find( child );
	if( it!=m_handlers.end() )
	{
		return it->second.get();
	}

	ParameterHandlerPtr h = nullptr;
	if( createIfMissing )
	{
		IECore::ConstBoolDataPtr noHostMapping = child->userData()->member<BoolData>( "noHostMapping" );
		if( !noHostMapping || !noHostMapping->readable() )
		{
			h = ParameterHandler::create( child );
			if( !h )
			{
				IECore::msg( IECore::Msg::Warning, "Gaffer::CompoundParameterHandler", fmt::format(  "Unable to create handler for parameter \"{}\" of type \"{}\"", child->name(), child->typeName() ) );
			}
		}
	}

	m_handlers[child] = h;
	return h.get();
}
