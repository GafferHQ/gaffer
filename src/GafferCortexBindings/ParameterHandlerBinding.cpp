//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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

#include "boost/python.hpp"

#include "IECorePython/RefCountedBinding.h"
#include "IECorePython/ScopedGILLock.h"
#include "IECorePython/Wrapper.h"

#include "Gaffer/Plug.h"

#include "GafferCortex/ParameterHandler.h"

#include "GafferCortexBindings/ParameterHandlerBinding.h"

using namespace boost::python;
using namespace GafferCortex;
using namespace GafferCortexBindings;

class ParameterHandlerWrapper : public ParameterHandler, public IECorePython::Wrapper<ParameterHandler>
{

	public :

		ParameterHandlerWrapper( PyObject *self )
			:	ParameterHandler(), IECorePython::Wrapper<ParameterHandler>( self, this )
		{
		}

		virtual IECore::Parameter *parameter()
		{
			IECorePython::ScopedGILLock gilLock;
			override o = this->get_override( "parameter" );
			return o();
		}

		virtual const IECore::Parameter *parameter() const
		{
			IECorePython::ScopedGILLock gilLock;
			override o = this->get_override( "parameter" );
			return o();
		}

		virtual void restore( Gaffer::GraphComponent *plugParent )
		{
			/// \todo Implement this to call through to python. We're not
			/// doing that right now to maintain compatibility with existing
			/// python-based parameter handlers in other packages.
		}

		virtual Gaffer::Plug *setupPlug( Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, unsigned flags )
		{
			IECorePython::ScopedGILLock gilLock;
			override o = this->get_override( "setupPlug" );
			return o( Gaffer::GraphComponentPtr( plugParent ), direction, flags );
		}

		virtual Gaffer::Plug *plug()
		{
			IECorePython::ScopedGILLock gilLock;
			override o = this->get_override( "plug" );
			return o();
		}

		virtual const Gaffer::Plug *plug() const
		{
			IECorePython::ScopedGILLock gilLock;
			override o = this->get_override( "plug" );
			return o();
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

struct ParameterHandlerCreator
{
	ParameterHandlerCreator( object fn )
		:	m_fn( fn )
	{
	}

	ParameterHandlerPtr operator()( IECore::ParameterPtr parameter )
	{
		IECorePython::ScopedGILLock gilLock;
		ParameterHandlerPtr result = extract<ParameterHandlerPtr>( m_fn( parameter ) );
		return result;
	}

	private :

		object m_fn;

};

static void registerParameterHandler( IECore::TypeId parameterType, object creator )
{
	ParameterHandler::registerParameterHandler( parameterType, ParameterHandlerCreator( creator ) );
}

void GafferCortexBindings::bindParameterHandler()
{

	IECorePython::RefCountedClass<ParameterHandler, IECore::RefCounted, ParameterHandlerWrapper>( "ParameterHandler" )
		.def( init<>() )
		.def(
			"parameter",
			(IECore::Parameter *(ParameterHandler::*)())&ParameterHandler::parameter,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def( "restore", &ParameterHandler::restore, ( arg( "plugParent" ) ) )
		.def(
			"setupPlug",
			&ParameterHandler::setupPlug,
			( arg( "plugParent" ), arg( "direction" )=Gaffer::Plug::In, arg( "flags" )=(Gaffer::Plug::Default | Gaffer::Plug::Dynamic) ),
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def(
			"plug",
			(Gaffer::Plug *(ParameterHandler::*)())&ParameterHandler::plug,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def( "setParameterValue", &ParameterHandler::setParameterValue )
		.def( "setPlugValue", &ParameterHandler::setPlugValue )
		.def( "create", &ParameterHandler::create ).staticmethod( "create" )
		.def( "registerParameterHandler", &registerParameterHandler ).staticmethod( "registerParameterHandler" )
	;

}
