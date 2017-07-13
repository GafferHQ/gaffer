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

#include "Gaffer/Plug.h"
#include "GafferBindings/ExceptionAlgo.h"

#include "GafferUI/NoduleLayout.h"
#include "GafferUI/Nodule.h"

#include "GafferUIBindings/NoduleLayoutBinding.h"
#include "GafferUIBindings/GadgetBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferUIBindings;

namespace
{

struct CustomGadgetCreator
{

	CustomGadgetCreator( object fn )
		:	m_fn( fn )
	{
	}

	GadgetPtr operator()( Gaffer::GraphComponentPtr parent )
	{
		IECorePython::ScopedGILLock gilLock;
		try
		{
			return extract<GadgetPtr>( m_fn( parent ) );
		}
		catch( const error_already_set & )
		{
			GafferBindings::translatePythonException();
		}
		return nullptr;
	}

	private :

		object m_fn;

};

void registerCustomGadget( const std::string &gadgetName, object creator )
{
	NoduleLayout::registerCustomGadget( gadgetName, CustomGadgetCreator( creator ) );
}

} // namespace

void GafferUIBindings::bindNoduleLayout()
{

	GadgetClass<NoduleLayout>()
		.def( init<GraphComponentPtr, IECore::InternedString>() )
		.def( "nodule", (Nodule * (NoduleLayout::*)( const Plug *))&NoduleLayout::nodule, return_value_policy<CastToIntrusivePtr>() )
		.def( "customGadget", (Gadget * (NoduleLayout::*)( const std::string & ))&NoduleLayout::customGadget, return_value_policy<CastToIntrusivePtr>() )
		.def( "registerCustomGadget", &registerCustomGadget )
		.staticmethod( "registerCustomGadget" )
	;

}
