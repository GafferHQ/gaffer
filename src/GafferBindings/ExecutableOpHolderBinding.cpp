//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "IECore/Op.h"

#include "IECorePython/Wrapper.h"
#include "IECorePython/RunTimeTypedBinding.h"

#include "Gaffer/Context.h"
#include "Gaffer/ExecutableOpHolder.h"
#include "Gaffer/CompoundParameterHandler.h"

#include "GafferBindings/ParameterisedHolderBinding.h"
#include "GafferBindings/ExecutableNodeBinding.h"
#include "GafferBindings/ExecutableOpHolderBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

typedef ParameterisedHolderWrapper< ExecutableNodeWrapper<ExecutableOpHolder> > ExecutableOpHolderWrapper;
IE_CORE_DECLAREPTR( ExecutableOpHolderWrapper );

static IECore::OpPtr getOp( ExecutableOpHolder &n )
{
	return n.getOp();
}

void GafferBindings::bindExecutableOpHolder()
{
	ExecutableNodeClass<ExecutableOpHolder, ExecutableOpHolderWrapperPtr>()
		.def(
			"setOp",
			&ExecutableOpHolder::setOp,
			(
				boost::python::arg_( "className" ),
				boost::python::arg_( "classVersion" ),
				boost::python::arg_( "keepExistingValues" ) = false
			)
		)
		.def( "getOp", &getOp )
	;
}
