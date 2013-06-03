//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#include <boost/python/suite/indexing/container_utils.hpp>
#include "boost/python.hpp"
#include "boost/format.hpp"
#include "IECorePython/RunTimeTypedBinding.h"
#include "GafferBindings/Serialisation.h"
#include "GafferImage/Filter.h"
#include "GafferImageBindings/FilterBinding.h"

using namespace boost;
using namespace boost::python;
using namespace IECore;
using namespace IECorePython;
using namespace GafferImage;
using namespace Gaffer;
using namespace GafferBindings;

namespace GafferImageBindings
{

static boost::python::list filterList()
{
	std::vector<std::string> filters( Filter::filters() );
	std::vector<std::string>::iterator it( filters.begin() );	
	boost::python::list result;
	for( ; it != filters.end(); it++ )
	{
		result.append( *it );
	}
	
	return result;
}

template<typename T>
static void bindTypedFilter()
{
	IECorePython::RunTimeTypedClass<T>()
		.def( init<float>(
				(
					boost::python::arg_( "scale" ) = 1.0
				)
			)
		)
	;
}

GafferImage::FilterPtr create1( std::string name ){ return GafferImage::Filter::create( name ); };
GafferImage::FilterPtr create2( std::string name, float scale ){ return GafferImage::Filter::create( name ); };
float weight( Filter& filter, float center, int pos ){ return filter.weight( center, pos  ); };

void bindFilters()
{
	RunTimeTypedClass<Filter> bind( "Filter" );
	bind.def( "__len__", &Filter::width );
	bind.def( "width", &Filter::width );
	bind.def( "getScale", &Filter::getScale );
	bind.def( "setScale", &Filter::setScale );
	bind.def( "tap", &Filter::tap );
	bind.def( "weight", &weight );
	
	// Convenience methods for creating Filter classes.
	bind.def( "filters", &filterList ).staticmethod("filters");
	bind.def( "create", &create1 );
	bind.def( "create", &create2 ).staticmethod( "create" );
	
	RunTimeTypedClass<SplineFilter>();
	RunTimeTypedClass<BoxFilter>();
	RunTimeTypedClass<BilinearFilter>();
	RunTimeTypedClass<CubicFilter>();
	RunTimeTypedClass<CatmullRomFilter>();
	RunTimeTypedClass<BSplineFilter>();
	RunTimeTypedClass<HermiteFilter>();
	RunTimeTypedClass<MitchellFilter>();
	RunTimeTypedClass<LanczosFilter>();
	RunTimeTypedClass<SincFilter>();
}

} // namespace IECorePython

