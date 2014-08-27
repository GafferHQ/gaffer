//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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
#include "IECorePython/Wrapper.h"
#include "IECorePython/ScopedGILLock.h"

#include "Gaffer/CompoundParameterHandler.h"
#include "Gaffer/GraphComponent.h"

#include "GafferBindings/CompoundParameterHandlerBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

/// Note that we've copied parts of the ParameterHandlerWrapper here. Typically we'd macroise
/// the repeated parts and make it possible to wrap any of the ParameterHandler classes
/// easily (see GraphComponentBinding.h for an example). However, doing that would necessitate
/// binding every single one of the ParameterHandlers, which isn't something we want to do
/// right now.
class CompoundParameterHandlerWrapper : public CompoundParameterHandler, public IECorePython::Wrapper<ParameterHandler>
{

	public :

		CompoundParameterHandlerWrapper( PyObject *self, IECore::CompoundParameterPtr parameter )
			:	CompoundParameterHandler( parameter ), IECorePython::Wrapper<ParameterHandler>( self, this )
		{
		}

		virtual void restore( GraphComponent *plugParent )
		{
			IECorePython::ScopedGILLock gilLock;
			override o = this->get_override( "restore" );
			if( o )
			{
				o( GraphComponentPtr( plugParent ) );
			}
			else
			{
				CompoundParameterHandler::restore( plugParent );
			}
		}

		virtual Plug *setupPlug( GraphComponent *plugParent, Plug::Direction direction, unsigned flags )
		{
			IECorePython::ScopedGILLock gilLock;
			override o = this->get_override( "setupPlug" );
			if( o )
			{
				return o( GraphComponentPtr( plugParent ), direction, flags );
			}
			else
			{
				return CompoundParameterHandler::setupPlug( plugParent, direction, flags );
			}
		}

		virtual void setParameterValue()
		{
			IECorePython::ScopedGILLock gilLock;
			override o = this->get_override( "setParameterValue" );
			if( o )
			{
				o();
			}
			else
			{
				CompoundParameterHandler::setParameterValue();
			}
		}

		virtual void setPlugValue()
		{
			IECorePython::ScopedGILLock gilLock;
			override o = this->get_override( "setPlugValue" );
			if( o )
			{
				o();
			}
			else
			{
				CompoundParameterHandler::setPlugValue();
			}
		}

		virtual IECore::RunTimeTyped *childParameterProvider( IECore::Parameter *childParameter )
		{
			IECorePython::ScopedGILLock gilLock;
			override o = this->get_override( "childParameterProvider" );
			if( o )
			{
				return o( IECore::ParameterPtr( childParameter ) );
			}
			else
			{
				return CompoundParameterHandler::childParameterProvider( childParameter );
			}
		}

};

static void compoundParameterHandlerRestore( CompoundParameterHandler &ph, GraphComponent *plugParent )
{
	return ph.CompoundParameterHandler::restore( plugParent );
}

static PlugPtr compoundParameterHandlerSetupPlug( CompoundParameterHandler &ph, GraphComponent *plugParent, Plug::Direction direction, unsigned flags )
{
	return ph.CompoundParameterHandler::setupPlug( plugParent, direction, flags );
}

static void compoundParameterHandlerSetParameterValue( CompoundParameterHandler &ph )
{
	return ph.CompoundParameterHandler::setParameterValue();
}

static void compoundParameterHandlerSetPlugValue( CompoundParameterHandler &ph )
{
	return ph.CompoundParameterHandler::setPlugValue();
}

void GafferBindings::bindCompoundParameterHandler()
{

	IECorePython::RefCountedClass<CompoundParameterHandler, ParameterHandler, CompoundParameterHandlerWrapper>( "CompoundParameterHandler" )
		.def( init<IECore::CompoundParameterPtr>() )
		.def( "restore", &compoundParameterHandlerRestore, ( arg( "plugParent" ) ) )
		.def( "setupPlug", &compoundParameterHandlerSetupPlug, ( arg( "plugParent" ), arg( "direction" )=Plug::In, arg( "flags" )=(Plug::Default | Plug::Dynamic) ) )
		.def( "setParameterValue", &compoundParameterHandlerSetParameterValue )
		.def( "setPlugValue", &compoundParameterHandlerSetPlugValue )
		.def(
			"childParameterHandler",
			(ParameterHandler *(CompoundParameterHandler::*)( IECore::Parameter * ))&CompoundParameterHandler::childParameterHandler,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
	;

}
