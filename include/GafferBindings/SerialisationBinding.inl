//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERBINDINGS_SERIALISATIONBINDING_INL
#define GAFFERBINDINGS_SERIALISATIONBINDING_INL

namespace GafferBindings
{

namespace Detail
{

// Method wrappers
// ===============
//
// These functions are used to wrap the methods of the Serialisers
// that we bind. For instance, when `serialiser.moduleDependencies()`
// is called in Python, the `moduleDependencies()` function below will
// be called, and it will make the call to the actual C++ method.
//
// The functions are called in two scenarios :
//
// 1. The `self` argument was constructed in Python,
//    and therefore is an instance of the `Wrapper` type.
//    Typically these are instances of a derived class
//    implemented in Python. If we naively call `self->method()`,
//    it would forward back into Python via the override
//    handler in SerialiserWrapper, causing an infinite loop
//    as the Python override calls the base class which calls
//    the Python override again. We must therefore statically
//    call `self->T::method()` instead.
//
// 2. The self argument was constructed in C++, and may well
//    be a derived class of T that hasn't even been exposed
//    to Python. Here we must call `self->method()` the usual
//    way, so that we dispatch to the correct virtual override
//    implemented in C++.
//
// All these functions therefore take the following form :
//
// ```
// template<typename T, typename Wrapper>
// foo( const T *self, ... )
// {
//     if( dynamic_cast<const Wrapper *>( self ) )
//     {
//         // Self was constructed in Python. Dispatch statically,
//         // to allow Python overrides to safely call the base
//         // class implementation.
//         self->T::foo( ... );
//     }
//     else
//     {
//         // Self was constructed in C++. Dispatch
//         // dynamically, so we call the virtual
//         // override for the most derived class.
//         self->foo( ... );
//     }
// }
// ```

template<typename T, typename Wrapper>
boost::python::object moduleDependencies( const T *self, const Gaffer::GraphComponent *graphComponent, const Serialisation &serialisation )
{
	std::set<std::string> modules;
	if( dynamic_cast<const Wrapper *>( self ) )
	{
		self->T::moduleDependencies( graphComponent, modules, serialisation );
	}
	else
	{
		self->moduleDependencies( graphComponent, modules, serialisation );
	}

	boost::python::list modulesList;
	for( std::set<std::string>::const_iterator it = modules.begin(); it != modules.end(); ++it )
	{
		modulesList.append( *it );
	}
	PyObject *modulesSet = PySet_New( modulesList.ptr() );
	return boost::python::object( boost::python::handle<>( modulesSet ) );
}

template<typename T, typename Wrapper>
std::string constructor( const T *self, const Gaffer::GraphComponent *graphComponent, Serialisation &serialisation )
{
	if( dynamic_cast<const Wrapper *>( self ) )
	{
		return self->T::constructor( graphComponent, serialisation );
	}
	else
	{
		return self->constructor( graphComponent, serialisation );
	}
}

template<typename T, typename Wrapper>
std::string postConstructor( const T *self, const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation )
{
	if( dynamic_cast<const Wrapper *>( self ) )
	{
		return self->T::postConstructor( graphComponent, identifier, serialisation );
	}
	else
	{
		return self->postConstructor( graphComponent, identifier, serialisation );
	}
}

template<typename T, typename Wrapper>
std::string postHierarchy( const T *self, const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation )
{
	if( dynamic_cast<const Wrapper *>( self ) )
	{
		return self->T::postHierarchy( graphComponent, identifier, serialisation );
	}
	else
	{
		return self->postHierarchy( graphComponent, identifier, serialisation );
	}
}

template<typename T, typename Wrapper>
std::string postScript( const T *self, const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation )
{
	if( dynamic_cast<const Wrapper *>( self ) )
	{
		return self->T::postScript( graphComponent, identifier, serialisation );
	}
	else
	{
		return self->postScript( graphComponent, identifier, serialisation );
	}
}

template<typename T, typename Wrapper>
bool childNeedsSerialisation( const T *self, const Gaffer::GraphComponent *child, const Serialisation &serialisation )
{
	if( dynamic_cast<const Wrapper *>( self ) )
	{
		return self->T::childNeedsSerialisation( child, serialisation );
	}
	else
	{
		return self->childNeedsSerialisation( child, serialisation );
	}
}

template<typename T, typename Wrapper>
bool childNeedsConstruction( const T *self, const Gaffer::GraphComponent *child, const Serialisation &serialisation )
{
	if( dynamic_cast<const Wrapper *>( self ) )
	{
		return self->T::childNeedsConstruction( child, serialisation );
	}
	else
	{
		return self->childNeedsConstruction( child, serialisation );
	}
}

} // namespace Detail

template<typename T, typename Base, typename TWrapper>
SerialiserClass<T, Base, TWrapper>::SerialiserClass( const char *name )
	:	IECorePython::RefCountedClass<T, Base, TWrapper>( name )
{
	this->def( boost::python::init<>() );
	this->def( "moduleDependencies", &Detail::moduleDependencies<T, TWrapper> );
	this->def( "constructor", &Detail::constructor<T, TWrapper> );
	this->def( "postConstructor", &Detail::postConstructor<T, TWrapper> );
	this->def( "postHierarchy", &Detail::postHierarchy<T, TWrapper> );
	this->def( "postScript", &Detail::postScript<T, TWrapper> );
	this->def( "childNeedsSerialisation", &Detail::childNeedsSerialisation<T, TWrapper> );
	this->def( "childNeedsConstruction", &Detail::childNeedsConstruction<T, TWrapper> );
}

} // namespace GafferBindings

#endif // GAFFERBINDINGS_SERIALISATIONBINDING_INL
