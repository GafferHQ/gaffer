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

#ifndef GAFFERBINDINGS_DEPENDENCYNODEBINDING_INL
#define GAFFERBINDINGS_DEPENDENCYNODEBINDING_INL

namespace GafferBindings
{

namespace Detail
{

// bindings for node wrapper functions

template<typename T>
static boost::python::list affects( const T &n, Gaffer::ConstValuePlugPtr p )
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
void defDependencyNodeWrapperFunctions( NodeClass<T, Ptr> &cls )
{
	cls.def( "affects", &affects<T> );
	cls.def( "enabledPlug", &enabledPlug<T> );
	cls.def( "correspondingInput", &correspondingInput<T> );
}

} // namespace Detail

template<typename T, typename Ptr>
DependencyNodeClass<T, Ptr>::DependencyNodeClass( const char *docString )
	:	NodeClass<T, Ptr>( docString )
{
	Detail::defDependencyNodeWrapperFunctions( *this );
}

} // namespace GafferBindings

#endif // GAFFERBINDINGS_DEPENDENCYNODEBINDING_INL
