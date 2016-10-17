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

#ifndef GAFFERBINDINGS_NODEBINDING_H
#define GAFFERBINDINGS_NODEBINDING_H

#include "boost/python.hpp"

#include "IECorePython/ScopedGILLock.h"

#include "Gaffer/Node.h"

#include "GafferBindings/GraphComponentBinding.h"
#include "GafferBindings/Serialisation.h"

namespace GafferBindings
{

void bindNode();

template<typename T, typename TWrapper=T>
class NodeClass : public GraphComponentClass<T, TWrapper>
{
	public :

		NodeClass( const char *docString = NULL );
		NodeClass( const char *docString, boost::python::no_init_t );

};

template<typename T>
class NodeWrapper : public GraphComponentWrapper<T>
{
	public :

		typedef T WrappedType;

		NodeWrapper( PyObject *self, const std::string &name )
			:	GraphComponentWrapper<T>( self, name )
		{
		}

		template<typename Arg1, typename Arg2>
		NodeWrapper( PyObject *self, Arg1 arg1, Arg2 arg2 )
			:	GraphComponentWrapper<WrappedType>( self, arg1, arg2 )
		{
		}

		template<typename Arg1, typename Arg2, typename Arg3>
		NodeWrapper( PyObject *self, Arg1 arg1, Arg2 arg2, Arg3 arg3 )
			:	GraphComponentWrapper<WrappedType>( self, arg1, arg2, arg3 )
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
			//
			// Note that we can't actually guarantee that we're not a
			// ScriptNode or DependencyNode, but those queries are so
			// common that we simply must accelerate them. We adjust for
			// this slightly overzealous optimisation in ScriptNodeWrapper
			// and DependencyNodeWrapper where we also override
			// isInstanceOf() and make the necessary correction.
			if(
				typeId == (IECore::TypeId)Gaffer::ScriptNodeTypeId ||
				typeId == (IECore::TypeId)Gaffer::DependencyNodeTypeId ||
				typeId == (IECore::TypeId)Gaffer::PlugTypeId ||
				typeId == (IECore::TypeId)Gaffer::ValuePlugTypeId ||
				typeId == (IECore::TypeId)Gaffer::CompoundPlugTypeId
			)
			{
				return false;
			}
			return GraphComponentWrapper<T>::isInstanceOf( typeId );
		}

		virtual bool acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "acceptsInput" );
				if( f )
				{
					return f( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( plug ) ), Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( inputPlug ) ) );
				}
			}
			return T::acceptsInput( plug, inputPlug );
		}

};

class NodeSerialiser : public Serialisation::Serialiser
{

	public :

		virtual void moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const;
		/// Implemented to serialise per-instance metadata.
		virtual std::string postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const;
		/// Implemented so that only plugs are serialised - child nodes are expected to
		/// be a part of the implementation of the node rather than something the user
		/// has created themselves.
		virtual bool childNeedsSerialisation( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const;
		/// Implemented so that dynamic plugs are constructed appropriately.
		virtual bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const;

};

} // namespace GafferBindings

#include "GafferBindings/NodeBinding.inl"

#endif // GAFFERBINDINGS_NODEBINDING_H
