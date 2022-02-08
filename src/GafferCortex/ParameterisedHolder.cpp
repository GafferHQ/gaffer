//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

#include "GafferCortex/ParameterisedHolder.h"

#include "GafferCortex/CompoundParameterHandler.h"

#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"

#include "IECore/MessageHandler.h"
#include "IECore/ParameterisedInterface.h"

#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace boost::placeholders;
using namespace GafferCortex;

template<typename BaseType>
const IECore::RunTimeTyped::TypeDescription<ParameterisedHolder<BaseType> > ParameterisedHolder<BaseType>::g_typeDescription;

template<typename BaseType>
ParameterisedHolder<BaseType>::ParameterisedHolder( const std::string &name )
	:	BaseType( name ), m_parameterised( nullptr ), m_parameterHandler( nullptr )
{
	BaseType::addChild( new Gaffer::StringPlug( "__className" ) );
	BaseType::addChild( new Gaffer::IntPlug( "__classVersion", Gaffer::Plug::In, -1 ) );
	BaseType::addChild( new Gaffer::StringPlug( "__searchPathEnvVar" ) );

	m_plugSetConnection = BaseType::plugSetSignal().connect( boost::bind( &ParameterisedHolder::plugSet, this, ::_1 ) );
}

template<typename BaseType>
ParameterisedHolder<BaseType>::~ParameterisedHolder()
{
}

template<typename BaseType>
void ParameterisedHolder<BaseType>::setParameterised( IECore::RunTimeTypedPtr parameterised, bool keepExistingValues )
{
	Gaffer::Signals::BlockedConnection connectionBlocker( m_plugSetConnection );

	IECore::ParameterisedInterface *interface = dynamic_cast<IECore::ParameterisedInterface *>( parameterised.get() );
	if( !interface )
	{
		throw IECore::Exception( "Not a ParameterisedInterface derived type." );
	}

	m_parameterised = parameterised;
	m_parameterHandler = new CompoundParameterHandler( interface->parameters() );
	if( keepExistingValues )
	{
		m_parameterHandler->restore( this );
	}
	m_parameterHandler->setupPlug( this );
	if( !keepExistingValues )
	{
		m_parameterHandler->setPlugValue();
	}
}

template<typename BaseType>
void ParameterisedHolder<BaseType>::setParameterised( const std::string &className, int classVersion, const std::string &searchPathEnvVar, bool keepExistingValues )
{
	IECore::RunTimeTypedPtr p = loadClass( className, classVersion, searchPathEnvVar );

	Gaffer::GraphComponent::getChild<Gaffer::StringPlug>( "__className" )->setValue( className );
	Gaffer::GraphComponent::getChild<Gaffer::IntPlug>( "__classVersion" )->setValue( classVersion );
	Gaffer::GraphComponent::getChild<Gaffer::StringPlug>( "__searchPathEnvVar" )->setValue( searchPathEnvVar );

	setParameterised( p, keepExistingValues );
}

template<typename BaseType>
IECore::RunTimeTyped *ParameterisedHolder<BaseType>::getParameterised( std::string *className, int *classVersion, std::string *searchPathEnvVar ) const
{
	Gaffer::Node *node = const_cast<Gaffer::Node *>( static_cast<const Gaffer::Node *>( this ) );
	if( className )
	{
		*className = node->getChild<Gaffer::StringPlug>( "__className" )->getValue();
	}
	if( classVersion )
	{
		*classVersion = node->getChild<Gaffer::IntPlug>( "__classVersion" )->getValue();
	}
	if( searchPathEnvVar )
	{
		*searchPathEnvVar = node->getChild<Gaffer::StringPlug>( "__searchPathEnvVar" )->getValue();
	}
	return m_parameterised.get();
}

template<typename BaseType>
IECore::ParameterisedInterface *ParameterisedHolder<BaseType>::parameterisedInterface( std::string *className, int *classVersion, std::string *searchPathEnvVar )
{
	return dynamic_cast<IECore::ParameterisedInterface *>( getParameterised( className, classVersion, searchPathEnvVar ) );
}


template<typename BaseType>
CompoundParameterHandler *ParameterisedHolder<BaseType>::parameterHandler()
{
	return m_parameterHandler.get();
}

template<typename BaseType>
const CompoundParameterHandler *ParameterisedHolder<BaseType>::parameterHandler() const
{
	return m_parameterHandler.get();
}

template<typename BaseType>
void ParameterisedHolder<BaseType>::setParameterisedValues()
{
	if( m_parameterHandler )
	{
		m_parameterHandler->setParameterValue();
	}
}

template<typename BaseType>
IECore::RunTimeTypedPtr ParameterisedHolder<BaseType>::loadClass( const std::string &className, int classVersion, const std::string &searchPathEnvVar ) const
{
	throw IECore::Exception( "Cannot load classes on a ParameterisedHolder not created in Python." );
}

template<typename BaseType>
void ParameterisedHolder<BaseType>::parameterChanged( IECore::RunTimeTyped *parameterised, IECore::Parameter *parameter )
{
}

template<typename BaseType>
void ParameterisedHolder<BaseType>::plugSet( Gaffer::Plug *plug )
{
	if( !m_parameterHandler || !m_parameterHandler->plug()->isAncestorOf( plug ) )
	{
		return;
	}

	std::vector<Gaffer::Plug *> plugHierarchy;
	while( plug != m_parameterHandler->plug() )
	{
		plugHierarchy.push_back( plug );
		plug = plug->parent<Gaffer::Plug>();
	}

	IECore::RunTimeTyped *parameterProvider = getParameterised();
	ParameterHandler *parameterHandler = m_parameterHandler.get();
	for( std::vector<Gaffer::Plug *>::const_reverse_iterator it = plugHierarchy.rbegin(), eIt = plugHierarchy.rend(); it != eIt; it++ )
	{
		IECore::CompoundParameter *compoundParameter = IECore::runTimeCast<IECore::CompoundParameter>( parameterHandler->parameter() );
		if( !compoundParameter )
		{
			return;
		}

		CompoundParameterHandler *compoundParameterHandler = static_cast<CompoundParameterHandler *>( parameterHandler );

		IECore::Parameter *childParameter = compoundParameter->parameter<IECore::Parameter>( (*it)->getName() );
		parameterHandler = compoundParameterHandler->childParameterHandler( childParameter );
		IECore::RunTimeTyped *childParameterProvider = compoundParameterHandler->childParameterProvider( childParameter );
		if( childParameterProvider )
		{
			parameterProvider = childParameterProvider;
		}
	}

	if( parameterHandler )
	{
		Gaffer::Signals::BlockedConnection connectionBlocker( m_plugSetConnection );
		parameterChanged( parameterProvider, parameterHandler->parameter() );
	}
}

//////////////////////////////////////////////////////////////////////////
// ParameterModificationContext
//////////////////////////////////////////////////////////////////////////

template<typename BaseType>
ParameterisedHolder<BaseType>::ParameterModificationContext::ParameterModificationContext( Ptr parameterisedHolder )
	:	m_parameterisedHolder( parameterisedHolder )
{
}

template<typename BaseType>
ParameterisedHolder<BaseType>::ParameterModificationContext::~ParameterModificationContext()
{
	if( m_parameterisedHolder->m_parameterHandler )
	{
		// If an exception occurs in the code scoped by a ParameterModificationContext,
		// this destructor will be called as the exception unwinds the stack. If we
		// were to throw a new exception in this scenario, the program would terminate.
		// Since the operations below can throw exceptions if the parameter values have been
		// left in an invalid state, we have to catch any exceptions they throw and report
		// them as errors rather than let the program die entirely.
		std::string error;
		try
		{
			Gaffer::Signals::BlockedConnection connectionBlocker( m_parameterisedHolder->m_plugSetConnection );
			m_parameterisedHolder->m_parameterHandler->setupPlug( m_parameterisedHolder.get() );
			m_parameterisedHolder->m_parameterHandler->setPlugValue();
		}
		catch( const std::exception &e )
		{
			error = e.what();
			if( error.empty() )
			{
				error = "Undescriptive exception";
			}
		}
		catch( ... )
		{
			error = "Unknown exception";
		}

		if( !error.empty() )
		{
			// Unfortunately, we also have to guard against the possibility of the message
			// handler throwing an exception too - particularly if the handler is implemented
			// in python and the original exception came from python.
			try
			{
				IECore::msg( IECore::Msg::Error, "ParameterModificationContext", error );
			}
			catch( ... )
			{
				std::cerr << "ERROR : ParameterModificationContext : " << error << std::endl;
			}
		}
	}
}

namespace GafferCortex
{

// specialisation
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( GafferCortex::ParameterisedHolderNode, ParameterisedHolderNodeTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( GafferCortex::ParameterisedHolderDependencyNode, ParameterisedHolderDependencyNodeTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( GafferCortex::ParameterisedHolderComputeNode, ParameterisedHolderComputeNodeTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( GafferCortex::ParameterisedHolderTaskNode, ParameterisedHolderTaskNodeTypeId )

// explicit instantiation
template class ParameterisedHolder<Gaffer::Node>;
template class ParameterisedHolder<Gaffer::DependencyNode>;
template class ParameterisedHolder<Gaffer::ComputeNode>;
template class ParameterisedHolder<GafferDispatch::TaskNode>;

} // namespace GafferCortex
