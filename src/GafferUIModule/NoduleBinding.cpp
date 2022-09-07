//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "NoduleBinding.h"

#include "ConnectionCreatorBinding.h"

#include "GafferUI/CompoundNodule.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/NoduleLayout.h"
#include "GafferUI/StandardNodule.h"
#include "GafferUI/CompoundNumericNodule.h"

#include "Gaffer/Plug.h"

#include "IECorePython/ExceptionAlgo.h"

using namespace boost::python;
using namespace IECorePython;
using namespace GafferUIBindings;
using namespace Gaffer;
using namespace GafferUI;

namespace
{

struct NoduleCreator
{
	NoduleCreator( object fn )
		:	m_fn( fn )
	{
	}

	NodulePtr operator()( Gaffer::PlugPtr plug )
	{
		IECorePython::ScopedGILLock gilLock;
		NodulePtr result = extract<NodulePtr>( m_fn( plug ) );
		return result;
	}

	private :

		object m_fn;

};

static void registerNodule( const std::string &noduleTypeName, object creator, IECore::TypeId plugType )
{
	Nodule::registerNodule( noduleTypeName, NoduleCreator( creator ), plugType );
}

void registerCustomGadget( const std::string &gadgetName, object creator )
{
	NoduleLayout::registerCustomGadget(
		gadgetName,
		// Deliberately "leaking" `creator` since it will be stored in a
		// static map that will be destroyed _after_ Python has shut down,
		// and deleting the PyObject at that point could cause a crash.
		[creator = new object( creator )] ( Gaffer::GraphComponentPtr parent ) -> GadgetPtr {
			IECorePython::ScopedGILLock gilLock;
			try
			{
				return extract<GadgetPtr>( (*creator)( parent ) );
			}
			catch( const error_already_set & )
			{
				ExceptionAlgo::translatePythonException();
			}
		}
	);
}

} // namespace

void GafferUIModule::bindNodule()
{

	ConnectionCreatorClass<ConnectionCreator, ConnectionCreatorWrapper<ConnectionCreator>>( "ConnectionCreator" )
		.def( init<>() )
	;

	ConnectionCreatorClass<Nodule>()
		.def(
			"plug",
			(Gaffer::Plug *(Nodule::*)())&Nodule::plug,
			return_value_policy<IECorePython::CastToIntrusivePtr>()
		)
		.def( "create", &Nodule::create ).staticmethod( "create" )
		.def( "registerNodule", &registerNodule, ( arg( "noduleTypeName" ), arg( "creator" ), arg( "plugType" ) = IECore::InvalidTypeId ) )
		.staticmethod( "registerNodule" )
	;

	ConnectionCreatorClass<StandardNodule>()
		.def( init<Gaffer::PlugPtr>() )
		.def( "setLabelVisible", &StandardNodule::setLabelVisible )
		.def( "getLabelVisible", &StandardNodule::getLabelVisible )
	;

	ConnectionCreatorClass<CompoundNodule>()
		.def( init<Gaffer::PlugPtr>( ( arg( "plug" ) ) ) )
	;

	ConnectionCreatorClass<CompoundNumericNodule>()
		.def( init<Gaffer::PlugPtr>( ( arg( "plug" ) ) ) )
	;

	GadgetClass<NoduleLayout>()
		.def( init<GraphComponentPtr, IECore::InternedString>() )
		.def( "nodule", (Nodule * (NoduleLayout::*)( const Plug *))&NoduleLayout::nodule, return_value_policy<CastToIntrusivePtr>() )
		.def( "customGadget", (Gadget * (NoduleLayout::*)( const std::string & ))&NoduleLayout::customGadget, return_value_policy<CastToIntrusivePtr>() )
		.def( "registerCustomGadget", &registerCustomGadget )
		.staticmethod( "registerCustomGadget" )
	;

}
