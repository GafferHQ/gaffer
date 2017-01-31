//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "IECorePython/Wrapper.h"
#include "IECorePython/ScopedGILLock.h"

#include "Gaffer/Plug.h"
#include "GafferBindings/ExceptionAlgo.h"
#include "GafferBindings/SignalBinding.h"

#include "GafferUI/PlugAdder.h"
#include "GafferUIBindings/PlugAdderBinding.h"
#include "GafferUIBindings/GadgetBinding.h"

using namespace boost::python;
using namespace std;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferUI;
using namespace GafferUIBindings;

namespace
{

struct PlugMenuSignalCaller
{

	PlugPtr call( PlugAdder::PlugMenuSignal &s, const std::string &title, const vector<Plug *> &plugs )
	{
		return s( title, plugs );
	}

};

struct PlugMenuSlotCaller
{

	Plug *operator()( boost::python::object slot, const std::string &title, const vector<Plug *> &plugs )
	{
		try
		{
			boost::python::list pythonPlugs;
			for( vector<Plug *>::const_iterator it = plugs.begin(), eIt = plugs.end(); it != eIt; ++it )
			{
				pythonPlugs.append( PlugPtr( *it ) );
			}
			object r = slot( title, pythonPlugs );

			return extract<Plug *>( r );
		}
		catch( const error_already_set &e )
		{
			translatePythonException();
		}
		return NULL;
	}

};

struct PlugAdderWrapper : public GadgetWrapper<PlugAdder>
{

	PlugAdderWrapper(PyObject *self, StandardNodeGadget::Edge edge )
		: GadgetWrapper<PlugAdder>( self, edge )
	{
	}

	virtual bool acceptsPlug( const Gaffer::Plug *connectionEndPoint ) const
	{
		if( this->isSubclassed() )
		{
			IECorePython::ScopedGILLock gilLock;
			boost::python::object f = this->methodOverride( "acceptsPlug" );
			if( f )
			{
				try
				{
					return f( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( connectionEndPoint ) ) );
				}
				catch( const error_already_set &e )
				{
					translatePythonException();
				}
			}
		}
		throw IECore::Exception( "No acceptsPlug method defined in Python." );
	}

	virtual void addPlug( Gaffer::Plug *connectionEndPoint )
	{
		if( this->isSubclassed() )
		{
			IECorePython::ScopedGILLock gilLock;
			boost::python::object f = this->methodOverride( "addPlug" );
			if( f )
			{
				try
				{
					f( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( connectionEndPoint ) ) );
					return;
				}
				catch( const error_already_set &e )
				{
					translatePythonException();
				}
			}
		}
		throw IECore::Exception( "No addPlug method defined in Python." );
	}
};

} // namespace

void GafferUIBindings::bindPlugAdder()
{
	scope s = GadgetClass<PlugAdder, PlugAdderWrapper>( "PlugAdder" )
		.def( init<StandardNodeGadget::Edge>() )
		.def( "plugMenuSignal", &PlugAdder::plugMenuSignal, return_value_policy<reference_existing_object>() )
		.staticmethod( "plugMenuSignal" )
		.def( "acceptsPlug", &PlugAdderWrapper::acceptsPlug )
		.def( "addPlug", &PlugAdderWrapper::addPlug )
	;

	SignalClass<PlugAdder::PlugMenuSignal, PlugMenuSignalCaller, PlugMenuSlotCaller>( "PlugMenuSignal" );
}
