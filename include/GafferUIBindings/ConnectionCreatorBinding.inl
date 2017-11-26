//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUIBINDINGS_CONNECTIONCREATORBINDING_INL
#define GAFFERUIBINDINGS_CONNECTIONCREATORBINDING_INL

namespace GafferUIBindings
{

namespace Detail
{

template<typename T>
static bool canCreateConnection( const T &connectionCreator, const Gaffer::Plug *endpoint )
{
	IECorePython::ScopedGILRelease gilRelease;
	return connectionCreator.T::canCreateConnection( endpoint );
}

template<typename T>
static void updateDragEndPoint( T &connectionCreator, const Imath::V3f position, const Imath::V3f &tangent )
{
	IECorePython::ScopedGILRelease gilRelease;
	return connectionCreator.T::updateDragEndPoint( position, tangent );
}

template<typename T>
static void createConnection( T &connectionCreator, Gaffer::Plug *endpoint )
{
	IECorePython::ScopedGILRelease gilRelease;
	return connectionCreator.T::createConnection( endpoint );
}

} // namespace Detail

template<typename T, typename TWrapper>
ConnectionCreatorClass<T, TWrapper>::ConnectionCreatorClass( const char *docString )
	:	GadgetClass<T, TWrapper>( docString )
{
	this->def( "canCreateConnection", &Detail::canCreateConnection<T> );
	this->def( "updateDragEndPoint", &Detail::updateDragEndPoint<T> );
	this->def( "createConnection", &Detail::createConnection<T> );
}

} // namespace GafferUIBindings

#endif // GAFFERUIBINDINGS_CONNECTIONCREATORBINDING_INL
