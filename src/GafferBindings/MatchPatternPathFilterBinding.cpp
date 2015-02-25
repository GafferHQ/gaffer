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

#include "Gaffer/MatchPatternPathFilter.h"
#include "GafferBindings/MatchPatternPathFilterBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

MatchPatternPathFilterPtr construct( list pythonPatterns, const char *propertyName, bool leafOnly )
{
	std::vector<MatchPattern> patterns;
	boost::python::container_utils::extend_container( patterns, pythonPatterns );
	return new MatchPatternPathFilter( patterns, propertyName, leafOnly );
}

void setMatchPatterns( MatchPatternPathFilter &f, list pythonPatterns )
{
	std::vector<MatchPattern> patterns;
	boost::python::container_utils::extend_container( patterns, pythonPatterns );
	f.setMatchPatterns( patterns );
}

list getMatchPatterns( const MatchPatternPathFilter &f )
{
	list result;
	const std::vector<MatchPattern> &patterns = f.getMatchPatterns();
	for( std::vector<MatchPattern>::const_iterator it = patterns.begin(), eIt = patterns.end(); it != eIt; ++it )
	{
		result.append( *it );
	}
	return result;
}

const char *getPropertyName( const MatchPatternPathFilter &f )
{
	return f.getPropertyName().string().c_str();
}

} // namespace

void GafferBindings::bindMatchPatternPathFilter()
{
	RunTimeTypedClass<MatchPatternPathFilter>()
		.def( "__init__", make_constructor( construct, default_call_policies(),
				(
					boost::python::arg_( "patterns" ),
					boost::python::arg_( "propertyName" ) = "name",
					boost::python::arg_( "leafOnly" ) = true
				)
			)
		)
		.def( "setMatchPatterns", &setMatchPatterns )
		.def( "getMatchPatterns", &getMatchPatterns )
		.def( "setPropertyName", &MatchPatternPathFilter::setPropertyName )
		.def( "getPropertyName", &getPropertyName )
		.def( "setInverted", &MatchPatternPathFilter::setInverted )
		.def( "getInverted", &MatchPatternPathFilter::getInverted )
	;
}
