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

#include "boost/python.hpp"

#include "GafferBindings/ParameterisedHolderBinding.h"
#include "GafferBindings/NodeBinding.h"
#include "Gaffer/ParameterisedHolder.h"
#include "Gaffer/CompoundParameterHandler.h"

#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/Wrapper.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

class ParameterisedHolderNodeWrapper : public ParameterisedHolderNode, public IECorePython::Wrapper<ParameterisedHolderNode>
{

	public :
		
		ParameterisedHolderNodeWrapper( PyObject *self, const std::string &name, const dict &inputs, const tuple &dynamicPlugs )
			:	ParameterisedHolderNode( name ), IECorePython::Wrapper<ParameterisedHolderNode>( self, this )
		{
			initNode( this, inputs, dynamicPlugs );
		}		
		
		GAFFERBINDINGS_NODEWRAPPERFNS( ParameterisedHolderNode )

};

IE_CORE_DECLAREPTR( ParameterisedHolderNodeWrapper )

static boost::python::tuple getParameterised( ParameterisedHolderNode &n )
{
	std::string className;
	int classVersion;
	std::string searchPathEnvVar;
	IECore::RunTimeTypedPtr p = n.getParameterised( &className, &classVersion, &searchPathEnvVar );
	return boost::python::make_tuple( p, className, classVersion, searchPathEnvVar );
}

class ParameterModificationContextWrapper
{

	public :
	
		ParameterModificationContextWrapper( ParameterisedHolderNodePtr parameterisedHolder )
			:	m_parameterisedHolder( parameterisedHolder ), m_context()
		{
		}
		
		IECore::RunTimeTypedPtr enter()
		{
			m_context.reset( new ParameterisedHolderNode::ParameterModificationContext( m_parameterisedHolder ) );
			return m_parameterisedHolder->getParameterised();
		}
		
		bool exit( object excType, object excValue, object excTraceBack )
		{
			m_context.reset();
			return false; // don't suppress exceptions
		}
		
	private :
	
		ParameterisedHolderNodePtr m_parameterisedHolder;
		boost::shared_ptr<ParameterisedHolderNode::ParameterModificationContext> m_context;

};

static ParameterModificationContextWrapper *parameterModificationContext( ParameterisedHolderNodePtr parameterisedHolder )
{
	return new ParameterModificationContextWrapper( parameterisedHolder );
}

void GafferBindings::bindParameterisedHolder()
{
	scope s = IECorePython::RunTimeTypedClass<ParameterisedHolderNode, ParameterisedHolderNodeWrapperPtr>()
		.def( 	init< const std::string &, const dict &, const tuple & >
				(
					(
						arg( "name" ) = ParameterisedHolderNode::staticTypeName(),
						arg( "inputs" ) = dict(),
						arg( "dynamicPlugs" ) = tuple()
					)
				)
		)
		.GAFFERBINDINGS_DEFGRAPHCOMPONENTWRAPPERFNS( ParameterisedHolderNode )
		.def( "setParameterised", (void (ParameterisedHolderNode::*)( IECore::RunTimeTypedPtr ))&ParameterisedHolderNode::setParameterised )
		.def( "setParameterised", (void (ParameterisedHolderNode::*)( const std::string &, int, const std::string & ))&ParameterisedHolderNode::setParameterised )
		.def( "getParameterised", getParameterised )
		.def( "parameterHandler", (CompoundParameterHandlerPtr (ParameterisedHolderNode::*)())&ParameterisedHolderNode::parameterHandler )
		.def( "parameterModificationContext", &parameterModificationContext, return_value_policy<manage_new_object>() )
		.def( "setParameterisedValues", &ParameterisedHolderNode::setParameterisedValues )
	;
	
	class_<ParameterModificationContextWrapper>( "ParameterModificationContext", init<ParameterisedHolderNodePtr>() )
		.def( "__enter__", &ParameterModificationContextWrapper::enter )
		.def( "__exit__", &ParameterModificationContextWrapper::exit )
	;
}
