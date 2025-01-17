//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

namespace GafferBindings
{

namespace Detail
{

// bindings for node wrapper functions

template<typename T>
static boost::python::list affects( const T &n, const Gaffer::Plug *p )
{
	Gaffer::DependencyNode::AffectedPlugsContainer a;
	n.T::affects( p, a );
	boost::python::list result;
	for( Gaffer::DependencyNode::AffectedPlugsContainer::const_iterator it=a.begin(); it!=a.end(); it++ )
	{
		result.append( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( *it ) ) );
	}
	return result;
}

template<typename T>
static Gaffer::BoolPlug::Ptr enabledPlug( T &n )
{
	return n.T::enabledPlug();
}

template<typename T>
static Gaffer::PlugPtr correspondingInput( T &n, const Gaffer::Plug *output )
{
	return n.T::correspondingInput( output );
}

GAFFERBINDINGS_API PyTypeObject *dependencyNodeMetaclass();

} // namespace Detail

template<typename T, typename Ptr>
DependencyNodeClass<T, Ptr>::DependencyNodeClass( const char *docString )
	:	NodeClass<T, Ptr>( docString )
{
	this->def( "affects", &Detail::affects<T> );
	this->def( "enabledPlug", &Detail::enabledPlug<T> );
	this->def( "correspondingInput", &Detail::correspondingInput<T> );
	// Install our custom metaclass.
	Py_SET_TYPE( this->ptr(), Detail::dependencyNodeMetaclass() );
}

template<typename T, typename Ptr>
DependencyNodeClass<T, Ptr>::DependencyNodeClass( const char *docString, boost::python::no_init_t )
	:	NodeClass<T, Ptr>( docString, boost::python::no_init )
{
	this->def( "affects", &Detail::affects<T> );
	this->def( "enabledPlug", &Detail::enabledPlug<T> );
	this->def( "correspondingInput", &Detail::correspondingInput<T> );
	// Install our custom metaclass.
	Py_SET_TYPE( this->ptr(), Detail::dependencyNodeMetaclass() );
}

} // namespace GafferBindings
