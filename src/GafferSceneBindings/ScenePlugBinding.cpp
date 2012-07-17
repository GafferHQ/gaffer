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

#include "IECorePython/RunTimeTypedBinding.h"

#include "GafferBindings/Serialiser.h"
#include "GafferBindings/PlugBinding.h"

#include "GafferScene/ScenePlug.h"

#include "GafferSceneBindings/ScenePlugBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;

static IECore::ObjectPtr objectWrapper( const ScenePlug &plug, const std::string &scenePath )
{
	IECore::ConstObjectPtr o = plug.object( scenePath );
	return o ? o->copy() : 0;
}


static IECore::StringVectorDataPtr childNamesWrapper( const ScenePlug &plug, const std::string &scenePath )
{
	IECore::ConstStringVectorDataPtr n = plug.childNames( scenePath );
	return n ? n->copy() : 0;
}

static IECore::ObjectVectorPtr stateWrapper( const ScenePlug &plug, const std::string &scenePath )
{
	IECore::ConstObjectVectorPtr s = plug.state( scenePath );
	return s ? s->copy() : 0;
}

static std::string serialise( Serialiser &s, ConstGraphComponentPtr g )
{
	ConstPlugPtr plug = IECore::staticPointerCast<const Plug>( g );
	std::string result = s.modulePath( g ) + ".ScenePlug( \"" + g->getName() + "\", ";
	
	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + serialisePlugDirection( plug->direction() ) + ", ";
	}
		
	if( plug->getFlags() != Plug::Default )
	{
		result += "flags = " + serialisePlugFlags( plug->getFlags() ) + ", ";
	}
	
	std::string input = serialisePlugInput( s, plug );
	if( input.size() )
	{
		result += "input = " + input + ", ";
	}
		
	result += ")";

	return result;
}

static ScenePlugPtr construct(
	const char *name,
	Plug::Direction direction,
	unsigned flags,
	ScenePlugPtr input
)
{
	ScenePlugPtr result = new ScenePlug( name, direction, flags );
	result->setInput( input );
	return result;
}

void GafferSceneBindings::bindScenePlug()
{

	IECorePython::RunTimeTypedClass<ScenePlug>()
		.def(
			"__init__",
			make_constructor(
				construct, default_call_policies(),
				(
					arg( "name" ) = ScenePlug::staticTypeName(),
					arg( "direction" ) = Gaffer::Plug::In,
					arg( "flags" ) = Gaffer::Plug::Default,
					arg( "input" ) = object()
				)
			)
		)
		.def( "bound", &ScenePlug::bound )
		.def( "transform", &ScenePlug::transform )
		.def( "object", &objectWrapper )
		.def( "childNames", &childNamesWrapper )
		.def( "state", &stateWrapper )
	;

	Serialiser::registerSerialiser( ScenePlug::staticTypeId(), serialise );
	
}
