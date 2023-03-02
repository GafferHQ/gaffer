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

#pragma once

namespace GafferBindings
{

namespace Detail
{

// node constructor bindings

template<typename T, typename TWrapper>
void defNodeConstructor( NodeClass<T, TWrapper> &cls, typename boost::enable_if<boost::mpl::not_< boost::is_abstract<TWrapper> > >::type *enabler = nullptr )
{
	cls.def( boost::python::init< const std::string & >( boost::python::arg( "name" ) = Gaffer::GraphComponent::defaultName<T>() ) );
}

template<typename T, typename TWrapper>
void defNodeConstructor( NodeClass<T, TWrapper> &cls, typename boost::enable_if<boost::is_abstract<TWrapper> >::type *enabler = nullptr )
{
	// nothing to bind for abstract classes
}

} // namespace Detail

template<typename T, typename TWrapper>
NodeClass<T, TWrapper>::NodeClass( const char *docString )
	:	GraphComponentClass<T, TWrapper>( docString )
{
	Detail::defNodeConstructor( *this );
}

template<typename T, typename TWrapper>
NodeClass<T, TWrapper>::NodeClass( const char *docString, boost::python::no_init_t )
	:	GraphComponentClass<T, TWrapper>( docString )
{
}

} // namespace GafferBindings
