//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

#ifndef GAFFER_CONTAINER_INL
#define GAFFER_CONTAINER_INL

namespace Gaffer
{

template<typename Base, typename T>
Container<Base, T>::Container( const std::string &name )
	:	Base( name )
{
}

template<typename Base, typename T>
Container<Base, T>::~Container()
{
}

template<typename Base, typename T>
IECore::TypeId Container<Base, T>::typeId() const
{
	return staticTypeId();
}

template<typename Base, typename T>
const char *Container<Base, T>::typeName() const
{
	return staticTypeName();
}

template<typename Base, typename T>
bool Container<Base, T>::isInstanceOf( IECore::TypeId typeId ) const
{
	if( typeId==staticTypeId() )
	{
		return true;
	}
	return Base::isInstanceOf( typeId );
}

template<typename Base, typename T>
bool Container<Base, T>::isInstanceOf( const char *typeName ) const
{
	if( 0==strcmp( typeName, staticTypeName() ) )
	{
		return true;
	}
	return Base::isInstanceOf( typeName );
}

template<typename Base, typename T>
bool Container<Base, T>::inheritsFrom( IECore::TypeId typeId )
{
	return Base::staticTypeId()==typeId ? true : Base::inheritsFrom( typeId );
}

template<typename Base, typename T>
bool Container<Base, T>::inheritsFrom( const char *typeName )
{
	return 0==strcmp( Base::staticTypeName(), typeName ) ? true : Base::inheritsFrom( typeName );
}

template<typename Base, typename T>
bool Container<Base, T>::acceptsChild( const GraphComponent *potentialChild ) const
{
	return potentialChild->isInstanceOf( T::staticTypeId() );
}

} // namespace Gaffer

#endif // GAFFER_CONTAINER_INL
