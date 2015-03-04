//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
#include "boost/python/suite/indexing/container_utils.hpp"

#include "IECorePython/RunTimeTypedBinding.h"

#include "Gaffer/CompoundPathFilter.h"
#include "GafferBindings/CompoundPathFilterBinding.h"

using namespace boost::python;
using namespace IECore;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

void setFilters( CompoundPathFilter &f, list pythonFilters )
{
	CompoundPathFilter::Filters filters;
	boost::python::container_utils::extend_container( filters, pythonFilters );
	f.setFilters( filters );
}

list getFilters( const CompoundPathFilter &f )
{
	CompoundPathFilter::Filters filters;
	f.getFilters( filters );

	list result;
	for( CompoundPathFilter::Filters::const_iterator it = filters.begin(), eIt = filters.end(); it != eIt; ++it )
	{
		result.append( *it );
	}
	return result;
}

CompoundPathFilterPtr construct( list filters, CompoundDataPtr userData )
{
	CompoundPathFilterPtr result = new CompoundPathFilter( userData );
	setFilters( *result, filters );
	return result;
}

} // namespace

void GafferBindings::bindCompoundPathFilter()
{
	RunTimeTypedClass<CompoundPathFilter>()
		.def( "__init__", make_constructor( &construct, default_call_policies(),
				(
					arg( "filters" ) = list(),
					arg( "userData" ) = object()
				)
			)
		)
		.def( "addFilter", &CompoundPathFilter::addFilter )
		.def( "removeFilter", &CompoundPathFilter::removeFilter )
		.def( "setFilters", &setFilters )
		.def( "getFilters", &getFilters )
	;
}
