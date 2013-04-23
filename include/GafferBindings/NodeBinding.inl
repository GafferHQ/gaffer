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

#ifndef GAFFERBINDINGS_NODEBINDING_INL
#define GAFFERBINDINGS_NODEBINDING_INL

namespace GafferBindings
{

namespace Detail
{

// node constructor bindings

template<typename T, typename Ptr>
void defNodeConstructor( NodeClass<T, Ptr> &cls, typename boost::enable_if<boost::mpl::not_< boost::is_abstract<typename Ptr::element_type> > >::type *enabler = 0 )
{
	cls.def( boost::python::init< const std::string & >( boost::python::arg( "name" ) = T::staticTypeName() ) );
}
	
template<typename T, typename Ptr>
void defNodeConstructor( NodeClass<T, Ptr> &cls, typename boost::enable_if<boost::is_abstract<typename Ptr::element_type> >::type *enabler = 0 )
{
	// nothing to bind for abstract classes
}

// bindings for node wrapper functions

template<typename T>
static Gaffer::BoolPlugPtr enabledPlug( T &n )
{
	return n.T::enabledPlug();
}

template<typename T>
static Gaffer::PlugPtr correspondingInput( T &n, const Gaffer::Plug *output )
{
	return n.T::correspondingInput( output );
}

template<typename T, typename Ptr>
void defNodeWrapperFunctions( NodeClass<T, Ptr> &cls )
{
	cls.GAFFERBINDINGS_DEFGRAPHCOMPONENTWRAPPERFNS( T );
	cls.def( "enabledPlug", &enabledPlug<T> );
	cls.def( "correspondingInput", &correspondingInput<T> );
}

} // namespace Detail

template<typename T, typename Ptr>
NodeClass<T, Ptr>::NodeClass( const char *docString )
	:	IECorePython::RunTimeTypedClass<T, Ptr>( docString )
{
	Detail::defNodeConstructor( *this );
	Detail::defNodeWrapperFunctions( *this );
}

} // namespace GafferBindings

#endif // GAFFERBINDINGS_NODEBINDING_INL
