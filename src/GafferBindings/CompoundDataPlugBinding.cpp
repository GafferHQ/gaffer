//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "IECorePython/RunTimeTypedBinding.h"

#include "Gaffer/CompoundDataPlug.h"

#include "GafferBindings/CompoundDataPlugBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

static CompoundDataPlugPtr compoundDataPlugConstructor( const char *name, Plug::Direction direction, unsigned flags, tuple children )
{
	CompoundDataPlugPtr result = new CompoundDataPlug( name, direction, flags );
	size_t s = extract<size_t>( children.attr( "__len__" )() );
	for( size_t i=0; i<s; i++ )
	{
		Gaffer::PlugPtr c = extract<Gaffer::PlugPtr>( children[i] );
		result->addChild( c );
	}
	return result;
}

static Gaffer::CompoundPlugPtr addMemberWrapper( CompoundDataPlug &p, const std::string &name, IECore::DataPtr value )
{
	return p.addMember( name, value );
}

void GafferBindings::bindCompoundDataPlug()
{

	IECorePython::RunTimeTypedClass<CompoundDataPlug>()
		.def( "__init__", make_constructor( compoundDataPlugConstructor, default_call_policies(),  
				(
					arg( "name" ) = CompoundDataPlug::staticTypeName(),
					arg( "direction" ) = Gaffer::Plug::In,
					arg( "flags" ) = Gaffer::Plug::Default,
					arg( "children" ) = tuple()
				)
			)	
		)
		.def( "addMember", &addMemberWrapper )
		.def( "addMembers", &CompoundDataPlug::addMembers )
	;
	
}