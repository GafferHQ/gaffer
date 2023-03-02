//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "GafferUIBindings/GadgetBinding.h"

#include "GafferUI/NodeGadget.h"

namespace GafferUIBindings
{

template<typename T, typename TWrapper=T>
class NodeGadgetClass : public GadgetClass<T, TWrapper>
{
	public :

		NodeGadgetClass( const char *docString = nullptr );

};

template<typename WrappedType>
class NodeGadgetWrapper : public GadgetWrapper<WrappedType>
{

	public :

		template<typename... Args>
		NodeGadgetWrapper( PyObject *self, Args&&... args )
			:	GadgetWrapper<WrappedType>( self, std::forward<Args>( args )... )
		{
		}

		GafferUI::Nodule *nodule( const Gaffer::Plug *plug ) override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "nodule" );
					if( f )
					{
						return boost::python::extract<GafferUI::Nodule *>(
							f( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( plug ) ) )
						);
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::nodule( plug );
		}

		const GafferUI::Nodule *nodule( const Gaffer::Plug *plug ) const override
		{
			// naughty cast is better than repeating the above logic.
			return const_cast<NodeGadgetWrapper *>( this )->nodule( plug );
		}

		Imath::V3f connectionTangent( const GafferUI::ConnectionCreator *creator ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "connectionTangent" );
					if( f )
					{
						return boost::python::extract<Imath::V3f>(
							f( GafferUI::ConnectionCreatorPtr( const_cast<GafferUI::ConnectionCreator *>( creator ) ) )
						);
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::connectionTangent( creator );
		}

};

} // namespace GafferUIBindings

#include "GafferUIBindings/NodeGadgetBinding.inl"
