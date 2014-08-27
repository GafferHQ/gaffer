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

#include "Gaffer/StandardSet.h"
#include "Gaffer/Behaviours/OrphanRemover.h"
#include "Gaffer/Behaviours/InputGenerator.h"

#include "GafferBindings/BehaviourBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace Gaffer::Behaviours;
using namespace GafferBindings;

static size_t inputGeneratorLen( const InputGenerator<Plug> &g )
{
	return g.inputs().size();
}

static PlugPtr inputGeneratorGetItem( const InputGenerator<Plug> &g, long index )
{
	long s = g.inputs().size();

	if( index < 0 )
	{
		index += s;
	}

	if( index >= s || index < 0 )
	{
		PyErr_SetString( PyExc_IndexError, "Index out of range" );
		throw_error_already_set();
	}

	return g.inputs()[index];
}

void GafferBindings::bindBehaviours()
{

	class_<Behaviour>( "Behaviour", no_init )
	;

	class_<OrphanRemover>( "OrphanRemover", init<StandardSetPtr>() )
	;

	class_<InputGenerator<Plug> >( "InputGenerator", no_init )
		.def(
			init<GraphComponent *, Plug *, size_t, size_t>( (
				arg_( "parent" ),
				arg_( "plugPrototype" ),
				arg_( "minInputs" ) = 1,
				arg_( "maxInputs" ) = Imath::limits<size_t>::max()
			) )
		 )
		.def( "__len__", &inputGeneratorLen )
		.def( "__getitem__", &inputGeneratorGetItem )
	;

}
