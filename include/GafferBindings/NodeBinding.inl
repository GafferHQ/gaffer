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

#ifndef GAFFERBINDINGS_NODEBINDING_INL
#define GAFFERBINDINGS_NODEBINDING_INL

#include "IECorePython/Wrapper.h"

namespace GafferBindings
{

namespace Detail
{

// some traits to help us figure out what we're binding

template<typename T, typename Ptr>
struct IsWrapped : boost::is_base_of<IECorePython::Wrapper<T>, typename Ptr::element_type>
{
};

template<typename T, typename Ptr>
struct IsNotWrapped : boost::mpl::not_< IsWrapped<T, Ptr> >
{
};

template<typename T, typename Ptr>
struct IsNotWrappedAndIsConcrete : boost::mpl::and_< IsNotWrapped<T, Ptr>, boost::mpl::not_< boost::is_abstract<T> > >
{
};

// bindings for the node constructors of various kinds

template<typename T>
typename T::Ptr nodeConstructor( const char *name, const boost::python::dict &inputs, const boost::python::tuple &dynamicPlugs )
{
	T *result = new T( name );
	initNode( result, inputs, dynamicPlugs );
	return result;
}

template<typename T, typename Ptr>
void defNodeConstructor( NodeClass<T, Ptr> &cls, typename boost::enable_if<IsWrapped<T, Ptr> >::type *enabler = 0 )
{
	cls.def( boost::python::init< const std::string &, const boost::python::dict &, const boost::python::tuple & >
		(
			(
				boost::python::arg( "name" ) = T::staticTypeName(),
				boost::python::arg( "inputs" ) = boost::python::dict(),
				boost::python::arg( "dynamicPlugs" ) = boost::python::tuple()
			)
		)
	);
}

template<typename T, typename Ptr>
void defNodeConstructor( NodeClass<T, Ptr> &cls, typename boost::enable_if<IsNotWrappedAndIsConcrete<T, Ptr> >::type *enabler = 0 )
{
	cls.def( 
		"__init__",
		boost::python::make_constructor( 
			&nodeConstructor<T>,
			boost::python::default_call_policies(), 
			(
				boost::python::arg_( "name" ) = T::staticTypeName(),
				boost::python::arg( "inputs" ) = boost::python::dict(),
				boost::python::arg( "dynamicPlugs" ) = boost::python::tuple()
			)
		)
	);
}
	
template<typename T, typename Ptr>
void defNodeConstructor( NodeClass<T, Ptr> &cls, typename boost::enable_if<boost::is_abstract<T> >::type *enabler = 0 )
{
	// nothing to bind for abstract classes
}

// bindings for node wrapper functions

template<typename T>
static boost::python::list affects( const T &n, Gaffer::ConstValuePlugPtr p )
{
	Gaffer::Node::AffectedPlugsContainer a;
	n.T::affects( p, a );
	boost::python::list result;
	for( Gaffer::Node::AffectedPlugsContainer::const_iterator it=a.begin(); it!=a.end(); it++ )
	{
		result.append( Gaffer::ValuePlugPtr( const_cast<Gaffer::ValuePlug *>( *it ) ) );
	}
	return result;
}

template<typename T, typename Ptr>
void defNodeWrapperFunctions( NodeClass<T, Ptr> &cls )
{
	cls.GAFFERBINDINGS_DEFGRAPHCOMPONENTWRAPPERFNS( T );
	cls.def( "affects", &affects<T> );
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
