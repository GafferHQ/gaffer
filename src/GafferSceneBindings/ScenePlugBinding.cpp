//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "boost/tokenizer.hpp"

#include "IECorePython/RunTimeTypedBinding.h"

#include "GafferBindings/PlugBinding.h"

#include "GafferScene/ScenePlug.h"

#include "GafferSceneBindings/ScenePlugBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;
using namespace GafferSceneBindings;

// as a convenience we overload the ScenePlug accessors to accept either strings
// or InternedStringVectorData for paths when calling from python. we deliberately
// don't do the same in c++ to force people to use the faster form (vector of interned strings).
void GafferSceneBindings::objectToScenePath(  boost::python::object o, GafferScene::ScenePlug::ScenePath &path )
{
	extract<IECore::InternedStringVectorDataPtr> dataExtractor( o );
	if( dataExtractor.check() )
	{
		IECore::ConstInternedStringVectorDataPtr p = dataExtractor();
		path = p->readable();
		return;
	}
	
	extract<std::string> stringExtractor( o );
	if( stringExtractor.check() )
	{
		std::string s = stringExtractor();
		typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
		Tokenizer t( s, boost::char_separator<char>( "/" ) );
		for( Tokenizer::const_iterator it = t.begin(), eIt = t.end(); it != eIt; it++ )
		{
			path.push_back( *it );
		}
		return;
	}
	
	PyErr_SetString( PyExc_TypeError, "Path must be string or IECore.InternedStringVectorData." );
	throw_error_already_set();
}

Imath::Box3f boundWrapper( const ScenePlug &plug, object scenePath )
{
	ScenePlug::ScenePath p;
	objectToScenePath( scenePath, p );
	return plug.bound( p );
}

Imath::M44f transformWrapper( const ScenePlug &plug, object scenePath )
{
	ScenePlug::ScenePath p;
	objectToScenePath( scenePath, p );
	return plug.transform( p );
}

Imath::M44f fullTransformWrapper( const ScenePlug &plug, object scenePath )
{
	ScenePlug::ScenePath p;
	objectToScenePath( scenePath, p );
	return plug.fullTransform( p );
}

static IECore::ObjectPtr objectWrapper( const ScenePlug &plug, object scenePath, bool copy=true )
{
	ScenePlug::ScenePath p;
	objectToScenePath( scenePath, p );
	IECore::ConstObjectPtr o = plug.object( p );
	return copy ? o->copy() : IECore::constPointerCast<IECore::Object>( o );
}

static IECore::InternedStringVectorDataPtr childNamesWrapper( const ScenePlug &plug, object scenePath, bool copy=true )
{
	ScenePlug::ScenePath p;
	objectToScenePath( scenePath, p );
	IECore::ConstInternedStringVectorDataPtr n = plug.childNames( p );
	return copy ? n->copy() : IECore::constPointerCast<IECore::InternedStringVectorData>( n );
}

static IECore::CompoundObjectPtr attributesWrapper( const ScenePlug &plug, object scenePath, bool copy=true )
{
	ScenePlug::ScenePath p;
	objectToScenePath( scenePath, p );IECore::ConstCompoundObjectPtr a = plug.attributes( p );
	return copy ? a->copy() : IECore::constPointerCast<IECore::CompoundObject>( a );
}

static IECore::CompoundObjectPtr fullAttributesWrapper( const ScenePlug &plug, object scenePath )
{
	ScenePlug::ScenePath p;
	objectToScenePath( scenePath, p );
	return plug.fullAttributes( p );
}

IECore::MurmurHash boundHashWrapper( const ScenePlug &plug, object scenePath )
{
	ScenePlug::ScenePath p;
	objectToScenePath( scenePath, p );
	return plug.boundHash( p );
}

IECore::MurmurHash transformHashWrapper( const ScenePlug &plug, object scenePath )
{
	ScenePlug::ScenePath p;
	objectToScenePath( scenePath, p );
	return plug.transformHash( p );
}

IECore::MurmurHash objectHashWrapper( const ScenePlug &plug, object scenePath )
{
	ScenePlug::ScenePath p;
	objectToScenePath( scenePath, p );
	return plug.objectHash( p );
}

IECore::MurmurHash childNamesHashWrapper( const ScenePlug &plug, object scenePath )
{
	ScenePlug::ScenePath p;
	objectToScenePath( scenePath, p );
	return plug.childNamesHash( p );
}

IECore::MurmurHash attributesHashWrapper( const ScenePlug &plug, object scenePath )
{
	ScenePlug::ScenePath p;
	objectToScenePath( scenePath, p );
	return plug.attributesHash( p );
} 

void GafferSceneBindings::bindScenePlug()
{

	IECorePython::RunTimeTypedClass<ScenePlug>()
		.def( init<const std::string &, Plug::Direction, unsigned>(
				(
					arg( "name" ) = Gaffer::GraphComponent::defaultName<ScenePlug>(),
					arg( "direction" ) = Gaffer::Plug::In,
					arg( "flags" ) = Gaffer::Plug::Default
				)
			)
		)
		// value accessors
		.def( "bound", &boundWrapper )
		.def( "transform", &transformWrapper )
		.def( "fullTransform", &fullTransformWrapper )
		.def( "object", &objectWrapper, ( boost::python::arg_( "_copy" ) = true ) )
		.def( "childNames", &childNamesWrapper, ( boost::python::arg_( "_copy" ) = true ) )
		.def( "attributes", &attributesWrapper, ( boost::python::arg_( "_copy" ) = true ) )
		.def( "fullAttributes", &fullAttributesWrapper )
		// hash accessors
		.def( "boundHash", &boundHashWrapper )
		.def( "transformHash", &transformHashWrapper )
		.def( "objectHash", &objectHashWrapper )
		.def( "childNamesHash", &childNamesHashWrapper )
		.def( "attributesHash", &attributesHashWrapper )
	;
	
}
