//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

#include "GafferUIBindings/ConnectionGadgetBinding.h"
#include "GafferUIBindings/GadgetBinding.h"
#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/Nodule.h"

#include "Gaffer/Node.h"

#include "IECorePython/RunTimeTypedBinding.h"

using namespace boost::python;
using namespace GafferUIBindings;
using namespace GafferUI;

static NodulePtr srcNodule( ConnectionGadget &c )
{
	return c.srcNodule();
}

static NodulePtr dstNodule( ConnectionGadget &c )
{
	return c.dstNodule();
}

struct ConnectionGadgetCreator
{
	ConnectionGadgetCreator( object fn )
		:	m_fn( fn )
	{
	}
	
	ConnectionGadgetPtr operator()( NodulePtr srcNodule, NodulePtr dstNodule )
	{
		IECorePython::ScopedGILLock gilLock;
		ConnectionGadgetPtr result = extract<ConnectionGadgetPtr>( m_fn( srcNodule, dstNodule ) );
		return result;
	}
	
	private :
	
		object m_fn;

};

static void registerConnectionGadget1( IECore::TypeId dstPlugType, object creator )
{
	ConnectionGadget::registerConnectionGadget( dstPlugType, ConnectionGadgetCreator( creator ) );
}

static void registerConnectionGadget2( IECore::TypeId nodeType, const std::string &dstPlugPathRegex, object creator )
{
	ConnectionGadget::registerConnectionGadget( nodeType, dstPlugPathRegex, ConnectionGadgetCreator( creator ) );
}

void GafferUIBindings::bindConnectionGadget()
{
	IECorePython::RunTimeTypedClass<ConnectionGadget>()
		.GAFFERUIBINDINGS_DEFGADGETWRAPPERFNS( ConnectionGadget )
		.def( "srcNodule", &srcNodule )
		.def( "dstNodule", &dstNodule )
		.def( "setNodules", &ConnectionGadget::setNodules )
		.def( "setMinimised", &ConnectionGadget::setMinimised )
		.def( "getMinimised", &ConnectionGadget::getMinimised )
		.def( "create", &ConnectionGadget::create )
		.staticmethod( "create" )
		.def( "registerConnectionGadget", &registerConnectionGadget1 )
		.def( "registerConnectionGadget", &registerConnectionGadget2 )
		.staticmethod( "registerConnectionGadget" )
	;
}
