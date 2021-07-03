//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUIBINDINGS_GADGETBINDING_H
#define GAFFERUIBINDINGS_GADGETBINDING_H

#include "GafferUI/Gadget.h"
#include "GafferUI/Style.h"

#include "GafferBindings/GraphComponentBinding.h"

#include <utility>

namespace GafferUIBindings
{

template<typename T, typename TWrapper=T>
class GadgetClass : public GafferBindings::GraphComponentClass<T, TWrapper>
{
	public :

		GadgetClass( const char *docString = nullptr );

};

template<typename WrappedType>
class GadgetWrapper : public GafferBindings::GraphComponentWrapper<WrappedType>
{
	public :

		template<typename... Args>
		GadgetWrapper( PyObject *self, Args&&... args )
			:	GafferBindings::GraphComponentWrapper<WrappedType>( self, std::forward<Args>( args )... )
		{
		}

		void setHighlighted( bool highlighted ) override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "setHighlighted" );
					if( f )
					{
						f( highlighted );
						return;
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::setHighlighted( highlighted );
		}

		Imath::Box3f bound() const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "bound" );
					if( f )
					{
						return boost::python::extract<Imath::Box3f>( f() );
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::bound();
		}

		std::string getToolTip( const IECore::LineSegment3f &line ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "getToolTip" );
					if( f )
					{
						return boost::python::extract<std::string>( f( line ) );
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::getToolTip( line );
		}

		void updateLayout() const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "updateLayout" );
					if( f )
					{
						f();
						return;
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::updateLayout();
		}

		void doRenderLayer( GafferUI::Gadget::Layer layer, const GafferUI::Style *style ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "doRenderLayer" );
					if( f )
					{
						f( layer, GafferUI::StylePtr( const_cast<GafferUI::Style *>( style ) ) );
						return;
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::doRenderLayer( layer, style );
		}

		unsigned layerMask() const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "layerMask" );
					if( f )
					{
						return boost::python::extract<unsigned>( f() );
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::layerMask();
		}

		Imath::Box3f renderBound() const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "renderBound" );
					if( f )
					{
						return boost::python::extract<Imath::Box3f>( f() );
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::bound();
		}

};

} // namespace GafferUIBindings

#include "GafferUIBindings/GadgetBinding.inl"

#endif // GAFFERUIBINDINGS_GADGETBINDING_H
