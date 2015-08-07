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

#ifndef GAFFERBINDINGS_COMPUTENODEBINDING_H
#define GAFFERBINDINGS_COMPUTENODEBINDING_H

#include "boost/python.hpp"

#include "IECorePython/ScopedGILLock.h"

#include "Gaffer/ComputeNode.h"
#include "Gaffer/Context.h"
#include "Gaffer/ValuePlug.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/ExceptionAlgo.h"

namespace GafferBindings
{

void bindComputeNode();

template<typename WrappedType>
class ComputeNodeWrapper : public DependencyNodeWrapper<WrappedType>
{
	public :

		ComputeNodeWrapper( PyObject *self, const std::string &name )
			:	DependencyNodeWrapper<WrappedType>( self, name )
		{
		}

		template<typename Arg1, typename Arg2>
		ComputeNodeWrapper( PyObject *self, Arg1 arg1, Arg2 arg2 )
			:	DependencyNodeWrapper<WrappedType>( self, arg1, arg2 )
		{
		}

		template<typename Arg1, typename Arg2, typename Arg3>
		ComputeNodeWrapper( PyObject *self, Arg1 arg1, Arg2 arg2, Arg3 arg3 )
			:	DependencyNodeWrapper<WrappedType>( self, arg1, arg2, arg3 )
		{
		}

		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
		{
			WrappedType::hash( output, context, h );
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "hash" );
					if( f )
					{
						boost::python::object pythonHash( h );
						f(
							Gaffer::ValuePlugPtr( const_cast<Gaffer::ValuePlug *>( output ) ),
							Gaffer::ContextPtr( const_cast<Gaffer::Context *>( context ) ),
							pythonHash
						);
						h = boost::python::extract<IECore::MurmurHash>( pythonHash );
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					translatePythonException();
				}
			}
		}

		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "compute" );
					if( f )
					{
						f( Gaffer::ValuePlugPtr( output ), Gaffer::ContextPtr( const_cast<Gaffer::Context *>( context ) ) );
						return;
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					translatePythonException();
				}
			}
			WrappedType::compute( output, context );
		}

};

} // namespace GafferBindings

#endif // GAFFERBINDINGS_COMPUTENODEBINDING_H
