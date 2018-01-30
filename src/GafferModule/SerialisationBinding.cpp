//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "SerialisationBinding.h"

#include "GafferBindings/GraphComponentBinding.h"
#include "GafferBindings/MetadataBinding.h"
#include "GafferBindings/Serialisation.h"

#include "Gaffer/Context.h"
#include "Gaffer/Plug.h"

#include "IECorePython/ScopedGILLock.h"

#include "IECore/MessageHandler.h"

#include "boost/format.hpp"
#include "boost/python/suite/indexing/container_utils.hpp"
#include "boost/tokenizer.hpp"

using namespace IECore;
using namespace Gaffer;
using namespace GafferBindings;
using namespace boost::python;

namespace
{

class SerialiserWrapper : public IECorePython::RefCountedWrapper<Serialisation::Serialiser>
{

	public :

		SerialiserWrapper( PyObject *self )
			:	IECorePython::RefCountedWrapper<Serialisation::Serialiser>( self )
		{
		}

		void moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "moduleDependencies" );
				if( f )
				{
					object mo = f( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ), serialisation );
					std::vector<std::string> mv;
					container_utils::extend_container( mv, mo );
					modules.insert( mv.begin(), mv.end() );
					return;
				}
			}
			Serialiser::moduleDependencies( graphComponent, modules, serialisation );
		}

		std::string constructor( const Gaffer::GraphComponent *graphComponent, const Serialisation &serialisation ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "constructor" );
				if( f )
				{
					return boost::python::extract<std::string>(
						f( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ), serialisation )
					);
				}
			}
			return Serialiser::constructor( graphComponent, serialisation );
		}

		std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "postConstructor" );
				if( f )
				{
					return boost::python::extract<std::string>(
						f( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ), identifier, serialisation )
					);
				}
			}
			return Serialiser::postConstructor( graphComponent, identifier, serialisation );
		}

		std::string postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "postHierarchy" );
				if( f )
				{
					return boost::python::extract<std::string>(
						f( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ), identifier, serialisation )
					);
				}
			}
			return Serialiser::postHierarchy( graphComponent, identifier, serialisation );
		}

		std::string postScript( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "postScript" );
				if( f )
				{
					return boost::python::extract<std::string>(
						f( GraphComponentPtr( const_cast<GraphComponent *>( graphComponent ) ), identifier, serialisation )
					);
				}
			}
			return Serialiser::postScript( graphComponent, identifier, serialisation );
		}

		bool childNeedsSerialisation( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "childNeedsSerialisation" );
				if( f )
				{
					return f( GraphComponentPtr( const_cast<GraphComponent *>( child ) ), serialisation );
				}
			}
			return Serialiser::childNeedsSerialisation( child, serialisation );
		}

		bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "childNeedsConstruction" );
				if( f )
				{
					return f( GraphComponentPtr( const_cast<GraphComponent *>( child ) ), serialisation );
				}
			}
			return Serialiser::childNeedsConstruction( child, serialisation );
		}

};

GraphComponentPtr parent( const Serialisation &serialisation )
{
	return const_cast<GraphComponent *>( serialisation.parent() );
}

object moduleDependencies( Serialisation::Serialiser &serialiser, const Gaffer::GraphComponent *graphComponent, const Serialisation &serialisation )
{
	std::set<std::string> modules;
	serialiser.moduleDependencies( graphComponent, modules, serialisation );
	boost::python::list modulesList;
	for( std::set<std::string>::const_iterator it = modules.begin(); it != modules.end(); ++it )
	{
		modulesList.append( *it );
	}
	PyObject *modulesSet = PySet_New( modulesList.ptr() );
	return object( handle<>( modulesSet ) );
}

} // namespace

void GafferModule::bindSerialisation()
{

	scope s = boost::python::class_<Serialisation>( "Serialisation", no_init )
		.def(
			init<const Gaffer::GraphComponent *, const std::string &, const Gaffer::Set *>
			(
				(
					arg( "parent" ),
					arg( "parentName" ) = "parent",
					arg( "filter" ) = object()
				)
			)
		)
		.def( "parent", &parent )
		.def( "identifier", &Serialisation::identifier )
		.def( "result", &Serialisation::result )
		.def( "modulePath", (std::string (*)( object & ))&Serialisation::modulePath )
		.staticmethod( "modulePath" )
		.def( "classPath", (std::string (*)( object & ))&Serialisation::classPath )
		.staticmethod( "classPath" )
		.def( "registerSerialiser", &Serialisation::registerSerialiser )
		.staticmethod( "registerSerialiser" )
		.def( "acquireSerialiser", &Serialisation::acquireSerialiser, return_value_policy<reference_existing_object>() )
		.staticmethod( "acquireSerialiser" )
	;

	IECorePython::RefCountedClass<Serialisation::Serialiser, IECore::RefCounted, SerialiserWrapper>( "Serialiser" )
		.def( init<>() )
		.def( "moduleDependencies", &moduleDependencies )
		.def( "constructor", &Serialisation::Serialiser::constructor )
		.def( "postConstructor", &Serialisation::Serialiser::postConstructor )
		.def( "postHierarchy", &Serialisation::Serialiser::postHierarchy )
		.def( "postScript", &Serialisation::Serialiser::postScript )
		.def( "childNeedsSerialisation", &Serialisation::Serialiser::childNeedsSerialisation )
		.def( "childNeedsConstruction", &Serialisation::Serialiser::childNeedsConstruction )
	;

}
