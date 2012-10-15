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

#include "GafferBindings/NodeBinding.h"

#include "GafferScene/SceneNode.h"
#include "GafferScene/FileSource.h"
#include "GafferScene/ModelCacheSource.h"
#include "GafferScene/SceneProcedural.h"
#include "GafferScene/SceneProcessor.h"
#include "GafferScene/AttributeCache.h"
#include "GafferScene/PrimitiveVariableProcessor.h"
#include "GafferScene/DeletePrimitiveVariables.h"
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
#include "GafferScene/RenderCamera.h"

#include "GafferSceneBindings/ScenePlugBinding.h"
#include "GafferSceneBindings/DisplaysBinding.h"

using namespace boost::python;
using namespace GafferScene;
using namespace GafferSceneBindings;

BOOST_PYTHON_MODULE( _GafferScene )
{
	
	bindScenePlug();
	
	IECorePython::RefCountedClass<SceneProcedural, IECore::Renderer::Procedural>( "SceneProcedural" )
		.def(
			init<ScenePlugPtr, const Gaffer::Context *, const std::string &, optional<const IECore::StringVectorData *> >
			(
				(	
					arg( "scenePlug" ),
					arg( "context" ),
					arg( "scenePath" ),
					arg( "pathsToExpand" ) = 0
				)
			)
		)
	;

	GafferBindings::NodeClass<SceneNode>();
	GafferBindings::NodeClass<Source>();
	GafferBindings::NodeClass<FileSource>();
	GafferBindings::NodeClass<ModelCacheSource>();
	GafferBindings::NodeClass<SceneProcessor>();
	GafferBindings::NodeClass<SceneElementProcessor>();
	GafferBindings::NodeClass<AttributeCache>();
	GafferBindings::NodeClass<PrimitiveVariableProcessor>();
	GafferBindings::NodeClass<DeletePrimitiveVariables>();
	GafferBindings::NodeClass<Group>();
	GafferBindings::NodeClass<SceneContextProcessorBase>();
	GafferBindings::NodeClass<SceneContextProcessor>();
	GafferBindings::NodeClass<SceneTimeWarp>();
	GafferBindings::NodeClass<ObjectSource>();
	GafferBindings::NodeClass<Plane>();
	GafferBindings::NodeClass<BranchCreator>();
	GafferBindings::NodeClass<Seeds>();
	GafferBindings::NodeClass<Instancer>();
	GafferBindings::NodeClass<ObjectToScene>();
	GafferBindings::NodeClass<Camera>();
	GafferBindings::NodeClass<GlobalsProcessor>();

	bindDisplays();

	GafferBindings::NodeClass<Options>();
	
	GafferBindings::NodeClass<Shader>()
		.def( "stateHash", (IECore::MurmurHash (Shader::*)() const )&Shader::stateHash )
		.def( "stateHash", (void (Shader::*)( IECore::MurmurHash &h ) const )&Shader::stateHash )
		.def( "state", &Shader::state )
	;
	
	GafferBindings::NodeClass<Assignment>();
	
	{
		scope s = GafferBindings::NodeClass<Filter>();
	
		enum_<Filter::Result>( "Result" )
			.value( "NoMatch", Filter::NoMatch )
			.value( "DescendantMatch", Filter::DescendantMatch )
			.value( "Match", Filter::Match )
		;
	}
				
	GafferBindings::NodeClass<PathFilter>();
	GafferBindings::NodeClass<Attributes>();
	GafferBindings::NodeClass<AlembicSource>();
	GafferBindings::NodeClass<SceneContextVariables>();
	GafferBindings::NodeClass<RenderCamera>();

}
