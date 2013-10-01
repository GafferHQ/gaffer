//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012-2013, John Haddon. All rights reserved.
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
#include "boost/python/suite/indexing/container_utils.hpp"

#include "IECore/VectorTypedData.h"

#include "GafferScene/PathMatcher.h"

#include "GafferSceneBindings/PathMatcherBinding.h"

using namespace boost::python;
using namespace GafferSceneBindings;
using namespace GafferScene;

namespace GafferSceneBindings
{

static PathMatcher *constructFromObject( boost::python::object oPaths )
{
	std::vector<std::string> paths;
	container_utils::extend_container( paths, oPaths );
	return new PathMatcher( paths.begin(), paths.end() );
}

static PathMatcher *constructFromVectorData( IECore::ConstStringVectorDataPtr paths )
{
	return new PathMatcher( paths->readable().begin(), paths->readable().end() );
}

static void initWrapper( PathMatcher &m, boost::python::object oPaths )
{
	std::vector<std::string> paths;
	container_utils::extend_container( paths, oPaths );
	return m.init( paths.begin(), paths.end() );
}

static list paths( const PathMatcher &p )
{
	std::vector<std::string> paths;
	p.paths( paths );
	list result;
	for( std::vector<std::string>::const_iterator it = paths.begin(), eIt = paths.end(); it != eIt; it++ )
	{
		result.append( *it );
	}
	return result;
}

void bindPathMatcher()
{
	class_<PathMatcher>( "PathMatcher" )
		.def( "__init__", make_constructor( constructFromObject ) )
		.def( "__init__", make_constructor( constructFromVectorData ) )
		.def( init<const PathMatcher &>() )
		.def( "init", &initWrapper )
		.def( "addPath", &PathMatcher::addPath )
		.def( "removePath", &PathMatcher::removePath )
		.def( "clear", &PathMatcher::clear )
		.def( "paths", &paths )
		.def( "match", (unsigned (PathMatcher ::*)( const std::string & ) const)&PathMatcher::match )
		.def( self == self )
		.def( self != self )
	;
}

} // namespace GafferSceneBindings
