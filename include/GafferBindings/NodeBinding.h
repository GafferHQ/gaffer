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

#ifndef GAFFERBINDINGS_NODEBINDING_H
#define GAFFERBINDINGS_NODEBINDING_H

#include "IECorePython/ScopedGILLock.h"

#include "Gaffer/Node.h"
#include "Gaffer/Context.h"

#include "GafferBindings/GraphComponentBinding.h"

namespace GafferBindings
{

#define GAFFERBINDINGS_NODEWRAPPERFNS( CLASSNAME )\
	GAFFERBINDINGS_GRAPHCOMPONENTWRAPPERFNS( CLASSNAME )\
\
	virtual void dirty( Gaffer::ConstPlugPtr dirty ) const\
	{\
		IECorePython::ScopedGILLock gilLock;\
		if( PyObject_HasAttrString( m_pyObject, "dirty" ) )\
		{\
			boost::python::override f = this->get_override( "dirty" );\
			if( f )\
			{\
				f( IECore::constPointerCast<Gaffer::Plug>( dirty ) );\
				return;\
			}\
		}\
		CLASSNAME::dirty( dirty );\
	}\
\
	virtual void compute( Gaffer::Plug *output, const Gaffer::Context *context ) const\
	{\
		IECorePython::ScopedGILLock gilLock;\
		if( PyObject_HasAttrString( m_pyObject, "compute" ) )\
		{\
			boost::python::override f = this->get_override( "compute" );\
			if( f )\
			{\
				f( Gaffer::PlugPtr( output ), Gaffer::ContextPtr( const_cast<Gaffer::Context *>( context ) ) );\
				return;\
			}\
		}\
		CLASSNAME::compute( output, context );\
	}

#define GAFFERBINDINGS_DEFNODEWRAPPERFNS( CLASSNAME ) \
	GAFFERBINDINGS_DEFGRAPHCOMPONENTWRAPPERFNS( CLASSNAME )
		
void bindNode();

void initNode( Gaffer::Node *node, const boost::python::dict &inputs, const boost::python::tuple &dynamicPlugs );

} // namespace GafferBindings

#endif // GAFFERBINDINGS_NODEBINDING_H
