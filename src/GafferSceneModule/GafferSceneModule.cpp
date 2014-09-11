//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2013, John Haddon. All rights reserved.
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

#include "GafferBindings/ComputeNodeBinding.h"
#include "GafferBindings/ExecutableNodeBinding.h"

#include "GafferScene/SceneNode.h"
#include "GafferScene/FileSource.h"
#include "GafferScene/SceneProcedural.h"
#include "GafferScene/SceneProcessor.h"
#include "GafferScene/AttributeCache.h"
#include "GafferScene/PrimitiveVariableProcessor.h"
#include "GafferScene/DeletePrimitiveVariables.h"
#include "GafferScene/MeshType.h"
#include "GafferScene/Group.h"
#include "GafferScene/Plane.h"
#include "GafferScene/Seeds.h"
#include "GafferScene/Instancer.h"
#include "GafferScene/ObjectToScene.h"
#include "GafferScene/Camera.h"
#include "GafferScene/GlobalsProcessor.h"
#include "GafferScene/Shader.h"
#include "GafferScene/AlembicSource.h"
#include "GafferScene/SubTree.h"
#include "GafferScene/SceneWriter.h"
#include "GafferScene/SceneReader.h"
#include "GafferScene/Light.h"
#include "GafferScene/OpenGLShader.h"
#include "GafferScene/Prune.h"
#include "GafferScene/Isolate.h"
#include "GafferScene/Cube.h"
#include "GafferScene/Sphere.h"
#include "GafferScene/Text.h"
#include "GafferScene/MapProjection.h"
#include "GafferScene/MapOffset.h"

#include "GafferSceneBindings/ScenePlugBinding.h"
#include "GafferSceneBindings/OutputsBinding.h"
#include "GafferSceneBindings/PathMatcherBinding.h"
#include "GafferSceneBindings/SceneProceduralBinding.h"
#include "GafferSceneBindings/PathMatcherDataBinding.h"
#include "GafferSceneBindings/RenderBinding.h"
#include "GafferSceneBindings/ShaderBinding.h"
#include "GafferSceneBindings/ConstraintBinding.h"
#include "GafferSceneBindings/AttributesBinding.h"
#include "GafferSceneBindings/FilterBinding.h"
#include "GafferSceneBindings/MixinBinding.h"
#include "GafferSceneBindings/TransformBinding.h"
#include "GafferSceneBindings/ParentBinding.h"
#include "GafferSceneBindings/SceneReaderBinding.h"
#include "GafferSceneBindings/PrimitiveVariablesBinding.h"
#include "GafferSceneBindings/DuplicateBinding.h"
#include "GafferSceneBindings/GridBinding.h"
#include "GafferSceneBindings/OptionsBinding.h"
#include "GafferSceneBindings/SetBinding.h"
#include "GafferSceneBindings/FreezeTransformBinding.h"
#include "GafferSceneBindings/SceneAlgoBinding.h"
#include "GafferSceneBindings/CoordinateSystemBinding.h"
#include "GafferSceneBindings/DeleteGlobalsBinding.h"
#include "GafferSceneBindings/ExternalProceduralBinding.h"

using namespace boost::python;
using namespace GafferScene;
using namespace GafferSceneBindings;

BOOST_PYTHON_MODULE( _GafferScene )
{

	bindScenePlug();

	GafferBindings::DependencyNodeClass<SceneNode>();
	GafferBindings::DependencyNodeClass<Source>();
	GafferBindings::DependencyNodeClass<FileSource>();
	GafferBindings::DependencyNodeClass<SceneProcessor>();
	GafferBindings::DependencyNodeClass<FilteredSceneProcessor>();
	GafferBindings::DependencyNodeClass<SceneElementProcessor>();
	GafferBindings::DependencyNodeClass<AttributeCache>();
	GafferBindings::DependencyNodeClass<MeshType>();
	GafferBindings::DependencyNodeClass<Group>();
	GafferBindings::DependencyNodeClass<ObjectSource>();
	GafferBindings::DependencyNodeClass<Cube>();
	GafferBindings::DependencyNodeClass<Plane>();
	GafferBindings::DependencyNodeClass<BranchCreator>();
	GafferBindings::DependencyNodeClass<Seeds>();
	GafferBindings::DependencyNodeClass<Instancer>();
	GafferBindings::DependencyNodeClass<ObjectToScene>();
	GafferBindings::DependencyNodeClass<Camera>();
	GafferBindings::DependencyNodeClass<GlobalsProcessor>();

	GafferBindings::ExecutableNodeClass<SceneWriter>();

	bindDeleteGlobals();
	bindOutputs();
	bindPathMatcher();
	bindPathMatcherData();
	bindSceneProcedural();
	bindShader();
	bindOptions();

	GafferBindings::DependencyNodeClass<AlembicSource>();
	GafferBindings::DependencyNodeClass<SubTree>();
	GafferBindings::DependencyNodeClass<Light>();
	GafferBindings::DependencyNodeClass<Prune>();
	GafferBindings::DependencyNodeClass<Isolate>();
	GafferBindings::DependencyNodeClass<Text>();
	GafferBindings::DependencyNodeClass<MapProjection>();
	GafferBindings::DependencyNodeClass<MapOffset>();

	GafferBindings::NodeClass<OpenGLShader>()
		.def( "loadShader", &OpenGLShader::loadShader )
	;

	{
		scope s = GafferBindings::DependencyNodeClass<Sphere>();

		enum_<Sphere::Type>( "Type" )
			.value( "Primitive", Sphere::Primitive )
			.value( "Mesh", Sphere::Mesh )
		;
	}

	bindRender();
	bindConstraint();
	bindAttributes();
	bindFilter();
	bindMixin();
	bindTransform();
	bindParent();
	bindSceneReader();
	bindPrimitiveVariables();
	bindDuplicate();
	bindGrid();
	bindSet();
	bindFreezeTransform();
	bindSceneAlgo();
	bindCoordinateSystem();
	bindExternalProcedural();

}
