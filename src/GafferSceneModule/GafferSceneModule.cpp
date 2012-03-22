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
#include "GafferScene/SceneHierarchyProcessor.h"
#include "GafferScene/GroupScenes.h"

using namespace boost::python;
using namespace GafferScene;

IECore::PrimitivePtr geometry( const ScenePlug &plug, const std::string &scenePath )
{
	IECore::ConstPrimitivePtr g = plug.geometry( scenePath );
	return g ? g->copy() : 0;
}


IECore::StringVectorDataPtr childNames( const ScenePlug &plug, const std::string &scenePath )
{
	IECore::ConstStringVectorDataPtr n = plug.childNames( scenePath );
	return n ? n->copy() : 0;
}

BOOST_PYTHON_MODULE( _GafferScene )
{
	
	IECorePython::RunTimeTypedClass<ScenePlug>()
		.def(
			init< const std::string &, Gaffer::Plug::Direction, unsigned >
			(
				(
					arg( "name" ) = Gaffer::CompoundPlug::staticTypeName(),
					arg( "direction" ) = Gaffer::Plug::In,
					arg( "flags" ) = Gaffer::Plug::Default
				)
			)	
		)
		.def( "bound", &ScenePlug::bound )
		.def( "transform", &ScenePlug::transform )
		.def( "geometry", &geometry )
		.def( "childNames", &childNames )
	;
	
	IECorePython::RefCountedClass<SceneProcedural, IECore::Renderer::Procedural>( "SceneProcedural" )
		.def( init<ScenePlugPtr, const Gaffer::Context *, const std::string &>() )
	;

	GafferBindings::NodeClass<SceneNode>();
	GafferBindings::NodeClass<FileSource>();
	GafferBindings::NodeClass<ModelCacheSource>();
	GafferBindings::NodeClass<SceneProcessor>();
	GafferBindings::NodeClass<SceneElementProcessor>();
	GafferBindings::NodeClass<AttributeCache>();
	GafferBindings::NodeClass<PrimitiveVariableProcessor>();
	GafferBindings::NodeClass<DeletePrimitiveVariables>();
	GafferBindings::NodeClass<SceneHierarchyProcessor>();
	GafferBindings::NodeClass<GroupScenes>();
	
}
