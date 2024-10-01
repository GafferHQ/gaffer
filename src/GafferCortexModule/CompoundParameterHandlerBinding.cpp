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

#include "CompoundParameterHandlerBinding.h"

#include "GafferCortex/CompoundParameterHandler.h"

#include "Gaffer/GraphComponent.h"

#include "IECorePython/RefCountedBinding.h"
#include "IECorePython/ScopedGILLock.h"

using namespace boost::python;
using namespace GafferCortex;
using namespace GafferCortexModule;

namespace
{

/// Note that we've copied parts of the ParameterHandlerWrapper here. Typically we'd template
/// the ParameterHandlerWrapper class and make it possible to wrap any of the ParameterHandler classes
/// easily (see GraphComponentBinding.h for an example). However, doing that would necessitate
/// binding every single one of the ParameterHandlers, which isn't something we want to do
/// right now.
class CompoundParameterHandlerWrapper : public IECorePython::RefCountedWrapper<CompoundParameterHandler>
{

	public :

		CompoundParameterHandlerWrapper( PyObject *self, IECore::CompoundParameterPtr parameter )
			:	 IECorePython::RefCountedWrapper<CompoundParameterHandler>( self, parameter )
		{
		}

		void restore( Gaffer::GraphComponent *plugParent ) override
		{
			IECorePython::ScopedGILLock gilLock;
			object o = methodOverride( "restore" );
			if( o )
			{
				o( Gaffer::GraphComponentPtr( plugParent ) );
			}
			else
			{
				CompoundParameterHandler::restore( plugParent );
			}
		}

		Gaffer::Plug *setupPlug( Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, unsigned flags ) override
		{
			IECorePython::ScopedGILLock gilLock;
			object o = methodOverride( "setupPlug" );
			if( o )
			{
				return extract<Gaffer::Plug *>( o( Gaffer::GraphComponentPtr( plugParent ), direction, flags ) );
			}
			else
			{
				return CompoundParameterHandler::setupPlug( plugParent, direction, flags );
			}
		}

		void setParameterValue() override
		{
			IECorePython::ScopedGILLock gilLock;
			object o = methodOverride( "setParameterValue" );
			if( o )
			{
				o();
			}
			else
			{
				CompoundParameterHandler::setParameterValue();
			}
		}

		void setPlugValue() override
		{
			IECorePython::ScopedGILLock gilLock;
			object o = methodOverride( "setPlugValue" );
			if( o )
			{
				o();
			}
			else
			{
				CompoundParameterHandler::setPlugValue();
			}
		}

		IECore::RunTimeTyped *childParameterProvider( IECore::Parameter *childParameter ) override
		{
			IECorePython::ScopedGILLock gilLock;
			object o = methodOverride( "childParameterProvider" );
			if( o )
			{
				return extract<IECore::RunTimeTyped *>( o( IECore::ParameterPtr( childParameter ) ) );
			}
			else
			{
				return CompoundParameterHandler::childParameterProvider( childParameter );
			}
		}

};

void compoundParameterHandlerRestore( CompoundParameterHandler &ph, Gaffer::GraphComponent *plugParent )
{
	return ph.CompoundParameterHandler::restore( plugParent );
}

Gaffer::PlugPtr compoundParameterHandlerSetupPlug( CompoundParameterHandler &ph, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, unsigned flags )
{
	return ph.CompoundParameterHandler::setupPlug( plugParent, direction, flags );
}

void compoundParameterHandlerSetParameterValue( CompoundParameterHandler &ph )
{
	// Setting a parameter value involves evaluating the plug - we don't want to hold the GIL while evaluating
	// the Gaffer graph.
	IECorePython::ScopedGILRelease gilRelease;
	return ph.CompoundParameterHandler::setParameterValue();
}

void compoundParameterHandlerSetPlugValue( CompoundParameterHandler &ph )
{
	return ph.CompoundParameterHandler::setPlugValue();
}

} // namespace

void GafferCortexModule::bindCompoundParameterHandler()
{

	IECorePython::RefCountedClass<CompoundParameterHandler, ParameterHandler, CompoundParameterHandlerWrapper>( "CompoundParameterHandler" )
		.def( init<IECore::CompoundParameterPtr>() )
		.def( "restore", &compoundParameterHandlerRestore, ( arg( "plugParent" ) ) )
		.def( "setupPlug", &compoundParameterHandlerSetupPlug, ( arg( "plugParent" ), arg( "direction" )=Gaffer::Plug::In, arg( "flags" )=(Gaffer::Plug::Default | Gaffer::Plug::Dynamic) ) )
		.def( "setParameterValue", &compoundParameterHandlerSetParameterValue )
		.def( "setPlugValue", &compoundParameterHandlerSetPlugValue )
		.def(
			"childParameterHandler",
			(ParameterHandler *(CompoundParameterHandler::*)( IECore::Parameter * ))&CompoundParameterHandler::childParameterHandler,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
	;

}
