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

#ifndef GAFFERBINDINGS_PLUGBINDING_H
#define GAFFERBINDINGS_PLUGBINDING_H

#include "IECorePython/ScopedGILRelease.h"

#include "Gaffer/Plug.h"

#include "GafferBindings/GraphComponentBinding.h"
#include "GafferBindings/Serialisation.h"

namespace GafferBindings
{

void bindPlug();

template<typename T, typename TWrapper=T>
class PlugClass : public GraphComponentClass<T, TWrapper>
{
	public :

		PlugClass( const char *docString = 0 );

};

template<typename WrappedType>
class PlugWrapper : public GraphComponentWrapper<WrappedType>
{
	public :

		PlugWrapper( PyObject *self, const std::string &name, Gaffer::Plug::Direction direction, unsigned flags )
			:	GraphComponentWrapper<WrappedType>( self, name, direction, flags )
		{
		}

		virtual bool isInstanceOf( IECore::TypeId typeId ) const
		{
			// Optimise for common queries we know should fail.
			// The standard wrapper implementation of isInstanceOf()
			// would have to enter Python only to discover this inevitable
			// failure as it doesn't have knowledge of the relationships
			// among types. Entering Python is incredibly costly for such
			// a simple operation, and we perform these operations often,
			// so this optimisation is well worth it.
			if(
				typeId == (IECore::TypeId)Gaffer::ScriptNodeTypeId ||
				typeId == (IECore::TypeId)Gaffer::NodeTypeId ||
				typeId == (IECore::TypeId)Gaffer::DependencyNodeTypeId ||
				typeId == (IECore::TypeId)Gaffer::ComputeNodeTypeId
			)
			{
				return false;
			}
			return GraphComponentWrapper<WrappedType>::isInstanceOf( typeId );
		}

		virtual bool acceptsInput( const Gaffer::Plug *input ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "acceptsInput" );
				if( f )
				{
					return f( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( input ) ) );
				}
			}
			return WrappedType::acceptsInput( input );
		}

		virtual void setInput( Gaffer::PlugPtr input )
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "setInput" );
				if( f )
				{
					f( boost::const_pointer_cast<Gaffer::Plug>( input ) );
					return;
				}
			}
			WrappedType::setInput( input );
		}

		virtual Gaffer::PlugPtr createCounterpart( const std::string &name, Gaffer::Plug::Direction direction ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "createCounterpart" );
				if( f )
				{
					Gaffer::PlugPtr result = boost::python::extract<Gaffer::PlugPtr>( f( name, direction ) );
					return result;
				}
			}
			return WrappedType::createCounterpart( name, direction );
		}

};

class PlugSerialiser : public Serialisation::Serialiser
{

	public :

		virtual void moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const;
		virtual std::string constructor( const Gaffer::GraphComponent *graphComponent, const Serialisation &serialisation ) const;
		virtual std::string postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const;
		virtual bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const;

		static std::string directionRepr( Gaffer::Plug::Direction direction );
		static std::string flagsRepr( unsigned flags );

};

} // namespace GafferBindings

#include "GafferBindings/PlugBinding.inl"

#endif // GAFFERBINDINGS_PLUGBINDING_H
