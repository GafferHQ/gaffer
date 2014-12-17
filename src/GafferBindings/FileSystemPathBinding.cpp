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

#include "Gaffer/PathFilter.h"
#include "Gaffer/FileSystemPath.h"
#include "GafferBindings/PathBinding.h"
#include "GafferBindings/FileSystemPathBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

PathFilterPtr createStandardFilter( list pythonExtensions, const std::string &extensionsLabel )
{
	std::vector<std::string> extensions;
	boost::python::container_utils::extend_container( extensions, pythonExtensions );
	return FileSystemPath::createStandardFilter( extensions, extensionsLabel );
}

} // namespace

void GafferBindings::bindFileSystemPath()
{

	PathClass<FileSystemPath>()
		.def(
			init<PathFilterPtr>( arg( "filter" ) = object() )
		)
		.def(
			init<const std::string &, PathFilterPtr>( (
				arg( "path" ),
				arg( "filter" ) = object()
			) )
		)
		.def( "createStandardFilter", &createStandardFilter, (
				arg( "extensions" ) = list(),
				arg( "extensionsLabel" ) = ""
			)
		)
		.staticmethod( "createStandardFilter" )
	;

}
