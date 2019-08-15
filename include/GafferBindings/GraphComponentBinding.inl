//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERBINDINGS_GRAPHCOMPONENTBINDING_INL
#define GAFFERBINDINGS_GRAPHCOMPONENTBINDING_INL

namespace GafferBindings
{

namespace Detail
{

template<typename T>
static bool acceptsChild( const T &p, const Gaffer::GraphComponent *potentialChild )
{
	return p.T::acceptsChild( potentialChild );
}

template<typename T>
static bool acceptsParent( const T &p, const Gaffer::GraphComponent *potentialParent )
{
	return p.T::acceptsParent( potentialParent );
}

template<typename RangeType>
static boost::python::object range( Gaffer::GraphComponent &graphComponent )
{
	boost::python::list l;
	for( auto &c : RangeType( graphComponent ) )
	{
		l.append( c );
	}
	// We could just return a list object, but instead we're returning an
	// iterator to a list. This gives us a bit more latitude to
	// replace with a true iterator in future, to avoid fully generating the
	// range before returning. The reason we don't do that now is that
	// if a python script modified the graph while iterating, it would
	// invalidate the iterator it was using, leading to crashes.
	return l.attr( "__iter__" )();
}

} // namespace Detail

template<typename T, typename TWrapper>
GraphComponentClass<T, TWrapper>::GraphComponentClass( const char *docString )
	:	IECorePython::RunTimeTypedClass<T, TWrapper>( docString )
{
	this->def( "acceptsChild", &Detail::acceptsChild<T> );
	this->def( "acceptsParent", &Detail::acceptsParent<T> );
	this->def( "Range", &Detail::range<typename T::Range> );
	this->staticmethod( "Range" );
	this->def( "RecursiveRange", &Detail::range<typename T::RecursiveRange> );
	this->staticmethod( "RecursiveRange" );
}

} // namespace GafferBindings

#endif // GAFFERBINDINGS_NODEBINDING_INL
