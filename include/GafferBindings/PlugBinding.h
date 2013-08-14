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

#include "Gaffer/Plug.h"

#include "GafferBindings/GraphComponentBinding.h"
#include "GafferBindings/Serialisation.h"

#include "IECorePython/ScopedGILRelease.h"

namespace GafferBindings
{

template<typename WrappedType>
class PlugWrapper : public GraphComponentWrapper<WrappedType>
{
	public :
	
		PlugWrapper( PyObject *self, const std::string &name, Gaffer::Plug::Direction direction, unsigned flags )
			:	GraphComponentWrapper<WrappedType>( self, name, direction, flags )
		{
		}		

		virtual bool acceptsInput( const Gaffer::Plug *input ) const
		{
			IECorePython::ScopedGILLock gilLock;
			if( PyObject_HasAttrString( GraphComponentWrapper<WrappedType>::m_pyObject, "acceptsInput" ) )
			{
				boost::python::override f = this->get_override( "acceptsInput" );
				if( f )
				{
					return f( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( input ) ) );
				}
			}
			return WrappedType::acceptsInput( input );
		}
	
		virtual void setInput( Gaffer::PlugPtr input )
		{
			IECorePython::ScopedGILLock gilLock;
			if( PyObject_HasAttrString( GraphComponentWrapper<WrappedType>::m_pyObject, "setInput" ) )
			{
				boost::python::override f = this->get_override( "setInput" );
				if( f )
				{
					f( IECore::constPointerCast<Gaffer::Plug>( input ) );
					return;
				}
			}
			WrappedType::setInput( input );
		}

		virtual Gaffer::PlugPtr createCounterpart( const std::string &name, Gaffer::Plug::Direction direction ) const
		{
			IECorePython::ScopedGILLock gilLock;
			if( PyObject_HasAttrString( GraphComponentWrapper<WrappedType>::m_pyObject, "createCounterpart" ) )
			{
				boost::python::override f = this->get_override( "createCounterpart" );
				if( f )
				{
					return f( name, direction );
				}
			}
			return WrappedType::createCounterpart( name, direction );
		}
	
};

/// This must be used in /every/ plug binding. See the lengthy comments in
/// IECorePython/ParameterBinding.h for an explanation.
#define GAFFERBINDINGS_DEFPLUGWRAPPERFNS( CLASSNAME )\
	GAFFERBINDINGS_DEFGRAPHCOMPONENTWRAPPERFNS( CLASSNAME ) \
	.def( "acceptsInput", &acceptsInput<CLASSNAME> )\
	.def( "setInput", &setInput<CLASSNAME> )\
	.def( "createCounterpart", &createCounterpart<CLASSNAME> )

template<typename T>
static bool acceptsInput( const T &p, Gaffer::ConstPlugPtr input )
{
	return p.T::acceptsInput( input );
}

template<typename T>
static void setInput( T &p, Gaffer::PlugPtr input )
{
	IECorePython::ScopedGILRelease r;
	p.T::setInput( input );
}

template<typename T>
static Gaffer::PlugPtr createCounterpart( T &p, const std::string &name, Gaffer::Plug::Direction direction )
{
	return p.T::createCounterpart( name, direction );
}
	
void bindPlug();

class PlugSerialiser : public Serialisation::Serialiser
{

	public :
	
		virtual std::string constructor( const Gaffer::GraphComponent *graphComponent ) const;
		virtual std::string postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const;
		
		static std::string directionRepr( Gaffer::Plug::Direction direction );
		static std::string flagsRepr( unsigned flags );

};

} // namespace GafferBindings

#endif // GAFFERBINDINGS_PLUGBINDING_H
