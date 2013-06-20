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

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/NodeBinding.h"

#include "GafferRenderMan/RenderManShader.h"
#include "GafferRenderMan/RenderManAttributes.h"
#include "GafferRenderMan/RenderManOptions.h"
#include "GafferRenderMan/RenderManLight.h"
#include "GafferRenderMan/InteractiveRenderManRender.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace GafferRenderMan;

/// \todo Move this serialisation to the bindings for GafferScene::Shader, once we've made Shader::loadShader() virtual
/// and implemented it so reloading works in ArnoldShader and OpenGLShader.
class RenderManShaderSerialiser : public GafferBindings::NodeSerialiser
{

	virtual std::string postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
	{
		const RenderManShader *shader = static_cast<const RenderManShader *>( graphComponent );
		std::string shaderName = shader->namePlug()->getValue();
		if( shaderName.size() )
		{
			return boost::str( boost::format( "%s.loadShader( \"%s\", keepExistingValues=True )\n" ) % identifier % shaderName );
		}

		return "";
	}

};

BOOST_PYTHON_MODULE( _GafferRenderMan )
{
	
	GafferBindings::DependencyNodeClass<RenderManShader>()
		.def( "loadShader", &RenderManShader::loadShader, ( arg_( "shaderName" ), arg_( "keepExistingValues" ) = false ) )
		.def( "shaderLoader", &RenderManShader::shaderLoader, return_value_policy<reference_existing_object>() )
		.staticmethod( "shaderLoader" )
	;
	
	Serialisation::registerSerialiser( RenderManShader::staticTypeId(), new RenderManShaderSerialiser() );

	GafferBindings::NodeClass<RenderManLight>()
		.def( "loadShader", &RenderManLight::loadShader )
	;

	GafferBindings::NodeClass<RenderManAttributes>();
	GafferBindings::NodeClass<RenderManOptions>();
	GafferBindings::NodeClass<InteractiveRenderManRender>();

}
