//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2013, John Haddon. All rights reserved.
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferBindings/NodeBinding.h"

#include "GafferScene/SceneProcessor.h"
#include "GafferSceneUI/SceneView.h"
#include "GafferSceneUIBindings/SceneViewBinding.h"

using namespace std;
using namespace boost::python;
using namespace IECorePython;
using namespace GafferScene;
using namespace GafferSceneUI;

namespace
{

struct ShadingModeCreator
{

	ShadingModeCreator( object fn )
		:	m_fn( fn )
	{
	}

	SceneProcessorPtr operator()()
	{
		IECorePython::ScopedGILLock gilLock;
		SceneProcessorPtr result = extract<SceneProcessorPtr>( m_fn() );
		return result;
	}

	private :

		object m_fn;

};

void registerShadingMode( const std::string &name, object creator )
{
	SceneView::registerShadingMode( name, ShadingModeCreator( creator ) );
}

boost::python::list registeredShadingModes()
{
	vector<string> n;
	SceneView::registeredShadingModes( n );
	boost::python::list result;
	for( vector<string>::const_iterator it = n.begin(), eIt = n.end(); it != eIt; ++it )
	{
		result.append( *it );
	}

	return result;
}

} // namespace

void GafferSceneUIBindings::bindSceneView()
{

	GafferBindings::NodeClass<SceneView>()
		.def( "expandSelection", &SceneView::expandSelection, ( boost::python::arg_( "depth" ) = 1 ) )
		.def( "collapseSelection", &SceneView::collapseSelection )
		.def( "registerShadingMode", &registerShadingMode )
		.staticmethod( "registerShadingMode" )
		.def( "registeredShadingModes", &registeredShadingModes )
		.staticmethod( "registeredShadingModes" )
	;

}
