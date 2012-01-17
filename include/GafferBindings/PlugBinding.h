//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#ifndef GAFFERBINDINGS_PLUGBINDING_H
#define GAFFERBINDINGS_PLUGBINDING_H

#include "GafferBindings/Serialiser.h"
#include "GafferBindings/GraphComponentBinding.h"
#include "Gaffer/Plug.h"

namespace GafferBindings
{

#define GAFFERBINDINGS_PLUGWRAPPERFNS( BASECLASS )\
\
	GAFFERBINDINGS_GRAPHCOMPONENTWRAPPERFNS( BASECLASS )\
\
	virtual bool acceptsInput( ConstPlugPtr input ) const\
	{\
		IECorePython::ScopedGILLock gilLock;\
		if( PyObject_HasAttrString( m_pyObject, "acceptsInput" ) )\
		{\
			override f = this->get_override( "acceptsInput" );\
			if( f )\
			{\
				return f( IECore::constPointerCast<Plug>( input ) );\
			}\
		}\
		return BASECLASS::acceptsInput( input );\
	}\
\
	virtual void setInput( PlugPtr input )\
	{\
		IECorePython::ScopedGILLock gilLock;\
		if( PyObject_HasAttrString( m_pyObject, "setInput" ) )\
		{\
			override f = this->get_override( "setInput" );\
			if( f ) \
			{\
				f( IECore::constPointerCast<Plug>( input ) );\
				return;\
			}\
		}\
		BASECLASS::setInput( input );\
	}\

/// This must be used in /every/ plug binding. See the lengthy comments in
/// IECorePython/ParameterBinding.h for an explanation.
#define GAFFERBINDINGS_DEFPLUGWRAPPERFNS( CLASSNAME )\
	GAFFERBINDINGS_DEFGRAPHCOMPONENTWRAPPERFNS( CLASSNAME ) \
	.def( "acceptsInput", &acceptsInput<CLASSNAME> )\
	.def( "setInput", &setInput<CLASSNAME> )

template<typename T>
static bool acceptsInput( const T &p, Gaffer::ConstPlugPtr input )
{
	return p.T::acceptsInput( input );
}

template<typename T>
static void setInput( T &p, Gaffer::PlugPtr input )
{
	p.T::setInput( input );
}
	
void bindPlug();

std::string serialisePlugDirection( Gaffer::Plug::Direction direction );
std::string serialisePlugFlags( unsigned flags );
std::string serialisePlugInput( Serialiser &s, Gaffer::ConstPlugPtr plug );

} // namespace GafferBindings

#endif // GAFFERBINDINGS_PLUGBINDING_H
