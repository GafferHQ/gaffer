//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/SceneNode.h"
#include "GafferScene/FileSource.h"
#include "GafferScene/ModelCacheSource.h"
#include "GafferScene/SceneProcedural.h"
#include "GafferScene/SceneProcessor.h"
#include "GafferScene/AttributeCache.h"
#include "GafferScene/PrimitiveVariableProcessor.h"
#include "GafferScene/DeletePrimitiveVariables.h"
#include "GafferScene/MeshType.h"
#include "GafferScene/Group.h"
#include "GafferScene/SceneTimeWarp.h"
#include "GafferScene/Plane.h"
#include "GafferScene/Seeds.h"
#include "GafferScene/Instancer.h"
#include "GafferScene/ObjectToScene.h"
#include "GafferScene/Camera.h"
#include "GafferScene/GlobalsProcessor.h"
#include "GafferScene/Options.h"
#include "GafferScene/Shader.h"
#include "GafferScene/Assignment.h"
#include "GafferScene/Filter.h"
#include "GafferScene/PathFilter.h"
#include "GafferScene/Attributes.h"
#include "GafferScene/AlembicSource.h"
#include "GafferScene/SceneContextVariables.h"
#include "GafferScene/StandardOptions.h"
#include "GafferScene/SubTree.h"
#include "GafferScene/OpenGLAttributes.h"
#include "GafferScene/SceneWriter.h"
#include "GafferScene/SceneReader.h"
#include "GafferScene/Light.h"
#include "GafferScene/StandardAttributes.h"
#include "GafferScene/OpenGLShader.h"
#include "GafferScene/Transform.h"
#include "GafferScene/AimConstraint.h"
#include "GafferScene/Prune.h"

#include "GafferSceneBindings/ScenePlugBinding.h"
#include "GafferSceneBindings/DisplaysBinding.h"
#include "GafferSceneBindings/PathMatcherBinding.h"
#include "GafferSceneBindings/SceneProceduralBinding.h"
#include "GafferSceneBindings/PathMatcherDataBinding.h"
#include "GafferSceneBindings/RenderBinding.h"

using namespace boost::python;
using namespace GafferScene;
using namespace GafferSceneBindings;

BOOST_PYTHON_MODULE( _GafferScene )
{
	
	bindScenePlug();
	
	GafferBindings::DependencyNodeClass<SceneNode>();
	GafferBindings::DependencyNodeClass<Source>();
	GafferBindings::DependencyNodeClass<FileSource>();
	GafferBindings::DependencyNodeClass<ModelCacheSource>();
	GafferBindings::DependencyNodeClass<SceneProcessor>();
	GafferBindings::DependencyNodeClass<FilteredSceneProcessor>();
	GafferBindings::DependencyNodeClass<SceneElementProcessor>();
	GafferBindings::DependencyNodeClass<AttributeCache>();
	GafferBindings::DependencyNodeClass<PrimitiveVariableProcessor>();
	GafferBindings::DependencyNodeClass<DeletePrimitiveVariables>();
	GafferBindings::DependencyNodeClass<MeshType>();
	GafferBindings::DependencyNodeClass<Group>();
	GafferBindings::DependencyNodeClass<SceneContextProcessorBase>();
	GafferBindings::DependencyNodeClass<SceneContextProcessor>();
	GafferBindings::DependencyNodeClass<SceneTimeWarp>();
	GafferBindings::DependencyNodeClass<ObjectSource>();
	GafferBindings::DependencyNodeClass<Plane>();
	GafferBindings::DependencyNodeClass<BranchCreator>();
	GafferBindings::DependencyNodeClass<Seeds>();
	GafferBindings::DependencyNodeClass<Instancer>();
	GafferBindings::DependencyNodeClass<ObjectToScene>();
	GafferBindings::DependencyNodeClass<Camera>();
	GafferBindings::DependencyNodeClass<GlobalsProcessor>();
	GafferBindings::DependencyNodeClass<SceneReader>();
	GafferBindings::NodeClass<SceneWriter>()
		.def( "execute", &SceneWriter::execute )
	;

	bindDisplays();
	bindPathMatcher();
	bindPathMatcherData();

	bindSceneProcedural();
	
	GafferBindings::DependencyNodeClass<Options>();
	
	GafferBindings::NodeClass<Shader>()
		.def( "stateHash", (IECore::MurmurHash (Shader::*)() const )&Shader::stateHash )
		.def( "stateHash", (void (Shader::*)( IECore::MurmurHash &h ) const )&Shader::stateHash )
		.def( "state", &Shader::state )
	;
	
	GafferBindings::DependencyNodeClass<Assignment>();
	
	{
		scope s = GafferBindings::DependencyNodeClass<Filter>();
	
		enum_<Filter::Result>( "Result" )
			.value( "NoMatch", Filter::NoMatch )
			.value( "DescendantMatch", Filter::DescendantMatch )
			.value( "Match", Filter::Match )
		;
	}
				
	GafferBindings::DependencyNodeClass<PathFilter>();
	GafferBindings::DependencyNodeClass<Attributes>();
	GafferBindings::DependencyNodeClass<AlembicSource>();
	GafferBindings::DependencyNodeClass<SceneContextVariables>();
	GafferBindings::DependencyNodeClass<StandardOptions>();
	GafferBindings::DependencyNodeClass<SubTree>();
	GafferBindings::DependencyNodeClass<OpenGLAttributes>();
	GafferBindings::DependencyNodeClass<Light>();
	GafferBindings::DependencyNodeClass<StandardAttributes>();
	GafferBindings::DependencyNodeClass<Transform>();
	GafferBindings::DependencyNodeClass<Prune>();
	
	{
		scope s =  GafferBindings::DependencyNodeClass<Constraint>();
		
		enum_<Constraint::TargetMode>( "TargetMode" )
			.value( "Origin", Constraint::Origin )
			.value( "BoundMin", Constraint::BoundMin )
			.value( "BoundMax", Constraint::BoundMax )
			.value( "BoundCenter", Constraint::BoundCenter )
		;
	}
	
	GafferBindings::DependencyNodeClass<AimConstraint>();

	GafferBindings::NodeClass<OpenGLShader>()
		.def( "loadShader", &OpenGLShader::loadShader )
	;
	
	bindRender();
	
}
