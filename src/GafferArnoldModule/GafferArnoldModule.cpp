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

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferDispatchBindings/TaskNodeBinding.h"

#include "GafferArnold/ArnoldShader.h"
#include "GafferArnold/ArnoldOptions.h"
#include "GafferArnold/ArnoldAttributes.h"
#include "GafferArnold/ArnoldLight.h"
#include "GafferArnold/ArnoldVDB.h"
#include "GafferArnold/InteractiveArnoldRender.h"
#include "GafferArnold/ArnoldRender.h"
#include "GafferArnold/ArnoldDisplacement.h"
#include "GafferArnold/ArnoldMeshLight.h"

using namespace boost::python;
using namespace GafferArnold;

namespace
{

/// \todo Move this serialisation to the bindings for GafferScene::Shader, once we've made Shader::loadShader() virtual
/// and implemented it so reloading works in OpenGLShader.
class ArnoldShaderSerialiser : public GafferBindings::NodeSerialiser
{

	virtual std::string postScript( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const GafferBindings::Serialisation &serialisation ) const
	{
		const ArnoldShader *shader = static_cast<const ArnoldShader *>( graphComponent );
		std::string shaderName = shader->namePlug()->getValue();
		if( shaderName.size() )
		{
			return boost::str( boost::format( "%s.loadShader( \"%s\", keepExistingValues=True )\n" ) % identifier % shaderName );
		}

		return "";
	}

};

} // namespace

BOOST_PYTHON_MODULE( _GafferArnold )
{

	GafferBindings::DependencyNodeClass<ArnoldShader>()
		.def(
			"loadShader", (void (ArnoldShader::*)( const std::string &, bool ))&ArnoldShader::loadShader,
			(
				arg( "shaderName" ),
				arg( "keepExistingValues" ) = false
			)
		)
	;

	GafferBindings::Serialisation::registerSerialiser( ArnoldShader::staticTypeId(), new ArnoldShaderSerialiser() );

	GafferBindings::NodeClass<ArnoldLight>()
		.def( "loadShader", (void (ArnoldLight::*)( const std::string & ) )&ArnoldLight::loadShader )
	;

	GafferBindings::DependencyNodeClass<ArnoldOptions>();
	GafferBindings::DependencyNodeClass<ArnoldAttributes>();
	GafferBindings::DependencyNodeClass<ArnoldVDB>();
	GafferBindings::DependencyNodeClass<ArnoldDisplacement>();
	GafferBindings::DependencyNodeClass<ArnoldMeshLight>();
	GafferBindings::NodeClass<InteractiveArnoldRender>();
	GafferDispatchBindings::TaskNodeClass<ArnoldRender>();

}
