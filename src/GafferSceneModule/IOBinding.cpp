//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "IOBinding.h"

#include "GafferScene/SceneReader.h"
#include "GafferScene/SceneWriter.h"

#include "GafferDispatchBindings/TaskNodeBinding.h"

#include "GafferBindings/DependencyNodeBinding.h"

using namespace GafferScene;

namespace
{

boost::python::list supportedExtensions()
{
	std::vector<std::string> e;
	SceneReader::supportedExtensions( e );

	boost::python::list result;
	for( std::vector<std::string>::const_iterator it = e.begin(), eIt = e.end(); it != eIt; ++it )
	{
		result.append( *it );
	}

	return result;
}

} // namespace

void GafferSceneModule::bindIO()
{

	GafferBindings::DependencyNodeClass<SceneReader>()
		.def( "supportedExtensions", &supportedExtensions )
		.staticmethod( "supportedExtensions" )
	;

	using SceneWriterWrapper = GafferDispatchBindings::TaskNodeWrapper<SceneWriter>;
	GafferDispatchBindings::TaskNodeClass<SceneWriter, SceneWriterWrapper>();
}
