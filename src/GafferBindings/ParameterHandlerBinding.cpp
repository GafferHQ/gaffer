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

#include "IECorePython/RefCountedBinding.h"
#include "IECorePython/ScopedGILLock.h"
#include "IECorePython/Wrapper.h"

#include "Gaffer/ParameterHandler.h"
#include "Gaffer/GraphComponent.h"
#include "GafferBindings/ParameterHandlerBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

class ParameterHandlerWrapper : public ParameterHandler, public IECorePython::Wrapper<ParameterHandler>
{

	public :
	
		ParameterHandlerWrapper( PyObject *self, IECore::ParameterPtr parameter )
			:	ParameterHandler( parameter ), IECorePython::Wrapper<ParameterHandler>( self, this )
		{
		}

		virtual void setParameterValue()
		{
			IECorePython::ScopedGILLock gilLock;
			override o = this->get_override( "setParameterValue" );
			o();
		}
		
		virtual void setPlugValue()
		{
			IECorePython::ScopedGILLock gilLock;
			override o = this->get_override( "setPlugValue" );
			o();
		}

};

IE_CORE_DECLAREPTR( ParameterHandlerWrapper )

struct ParameterHandlerCreator
{
	ParameterHandlerCreator( object fn )
		:	m_fn( fn )
	{
	}
	
	ParameterHandlerPtr operator()( IECore::ParameterPtr parameter, GraphComponentPtr plugParent )
	{
		IECorePython::ScopedGILLock gilLock;
		ParameterHandlerPtr result = extract<ParameterHandlerPtr>( m_fn( parameter, plugParent ) );
		return result;
	}
	
	private :
	
		object m_fn;

};

static void registerParameterHandler( IECore::TypeId parameterType, object creator )
{
	ParameterHandler::registerParameterHandler( parameterType, ParameterHandlerCreator( creator ) );
}

void GafferBindings::bindParameterHandler()
{
	
	IECorePython::RefCountedClass<ParameterHandler, IECore::RefCounted, ParameterHandlerWrapperPtr>( "ParameterHandler" )
		.def( init<IECore::ParameterPtr>() )
		.def( "parameter", (IECore::ParameterPtr (ParameterHandler::*)())&ParameterHandler::parameter )
		.def( "setParameterValue", &ParameterHandler::setParameterValue )
		.def( "setPlugValue", &ParameterHandler::setPlugValue )
		.def( "create", &ParameterHandler::create ).staticmethod( "create" )
		.def( "registerParameterHandler", &registerParameterHandler ).staticmethod( "registerParameterHandler" )
	;
		
}
