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

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

#include "IECore/ParameterisedInterface.h"
#include "IECore/MessageHandler.h"

#include "Gaffer/ParameterisedHolder.h"
#include "Gaffer/CompoundParameterHandler.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/BlockedConnection.h"

using namespace Gaffer;

template<typename BaseType>
const IECore::RunTimeTyped::TypeDescription<ParameterisedHolder<BaseType> > ParameterisedHolder<BaseType>::g_typeDescription;

template<typename BaseType>
ParameterisedHolder<BaseType>::ParameterisedHolder( const std::string &name )
	:	BaseType( name ), m_parameterised( 0 ), m_parameterHandler( 0 )
{
	BaseType::addChild( new StringPlug( "__className" ) );
	BaseType::addChild( new IntPlug( "__classVersion", Plug::In, -1 ) );
	BaseType::addChild( new StringPlug( "__searchPathEnvVar" ) );

	m_plugSetConnection = BaseType::plugSetSignal().connect( boost::bind( &ParameterisedHolder::plugSet, this, ::_1 ) );
}

template<typename BaseType>
ParameterisedHolder<BaseType>::~ParameterisedHolder()
{
}

template<typename BaseType>
void ParameterisedHolder<BaseType>::setParameterised( IECore::RunTimeTypedPtr parameterised, bool keepExistingValues )
{
	BlockedConnection connectionBlocker( m_plugSetConnection );

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

	GraphComponent::getChild<StringPlug>( "__className" )->setValue( className );
	GraphComponent::getChild<IntPlug>( "__classVersion" )->setValue( classVersion );
	GraphComponent::getChild<StringPlug>( "__searchPathEnvVar" )->setValue( searchPathEnvVar );

	setParameterised( p, keepExistingValues );
}

template<typename BaseType>
IECore::RunTimeTypedPtr ParameterisedHolder<BaseType>::getParameterised( std::string *className, int *classVersion, std::string *searchPathEnvVar ) const
{
	Node *node = const_cast<Node *>( static_cast<const Node *>( this ) );
	if( className )
	{
		*className = node->getChild<StringPlug>( "__className" )->getValue();
	}
	if( classVersion )
	{
		*classVersion = node->getChild<IntPlug>( "__classVersion" )->getValue();
	}
	if( searchPathEnvVar )
	{
		*searchPathEnvVar = node->getChild<StringPlug>( "__searchPathEnvVar" )->getValue();
	}
	return m_parameterised;
}

template<typename BaseType>
IECore::ParameterisedInterface *ParameterisedHolder<BaseType>::parameterisedInterface( std::string *className, int *classVersion, std::string *searchPathEnvVar )
{
	return dynamic_cast<IECore::ParameterisedInterface *>( getParameterised( className, classVersion, searchPathEnvVar ).get() );
}


template<typename BaseType>
CompoundParameterHandlerPtr ParameterisedHolder<BaseType>::parameterHandler()
{
	return m_parameterHandler;
}

template<typename BaseType>
ConstCompoundParameterHandlerPtr ParameterisedHolder<BaseType>::parameterHandler() const
{
	return m_parameterHandler;
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
void ParameterisedHolder<BaseType>::plugSet( PlugPtr plug )
{
	if( !m_parameterHandler || !m_parameterHandler->plug()->isAncestorOf( plug ) )
	{
		return;
	}
		
	std::vector<Plug *> plugHierarchy;
	while( plug != m_parameterHandler->plug() )
	{
		plugHierarchy.push_back( plug );
		plug = plug->parent<Plug>();
	}
	
	IECore::RunTimeTyped *parameterProvider = getParameterised();
	ParameterHandler *parameterHandler = m_parameterHandler;
	for( std::vector<Plug *>::const_reverse_iterator it = plugHierarchy.rbegin(), eIt = plugHierarchy.rend(); it != eIt; it++ )
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
		BlockedConnection connectionBlocker( m_plugSetConnection );
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
			BlockedConnection connectionBlocker( m_parameterisedHolder->m_plugSetConnection );
			m_parameterisedHolder->m_parameterHandler->setupPlug( m_parameterisedHolder );
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

// specialisation

namespace Gaffer
{

IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::ParameterisedHolderNode, ParameterisedHolderNodeTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::ParameterisedHolderDependencyNode, ParameterisedHolderDependencyNodeTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::ParameterisedHolderComputeNode, ParameterisedHolderComputeNodeTypeId )
IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( Gaffer::ParameterisedHolderExecutableNode, ParameterisedHolderExecutableNodeTypeId )

}

// explicit instantiation
template class ParameterisedHolder<Node>;
template class ParameterisedHolder<DependencyNode>;
template class ParameterisedHolder<ComputeNode>;
template class ParameterisedHolder<ExecutableNode>;
