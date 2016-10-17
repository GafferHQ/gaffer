//////////////////////////////////////////////////////////////////////////
//
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

#ifndef GAFFER_METADATA_INL
#define GAFFER_METADATA_INL

namespace Gaffer
{

template<typename T>
typename T::ConstPtr Metadata::value( IECore::InternedString target, IECore::InternedString key )
{
	return IECore::runTimeCast<const T>( valueInternal( target, key ) );
}

template<typename T>
typename T::ConstPtr Metadata::value( const GraphComponent *target, IECore::InternedString key, bool instanceOnly )
{
	return IECore::runTimeCast<const T>( valueInternal( target, key, instanceOnly ) );
}

template<typename T>
typename T::ConstPtr Metadata::nodeValue( const Node *node, IECore::InternedString key, bool inherit, bool instanceOnly )
{
	return IECore::runTimeCast<const T>( nodeValueInternal( node, key, inherit, instanceOnly ) );
}

template<typename T>
typename T::ConstPtr Metadata::plugValue( const Plug *plug, IECore::InternedString key, bool inherit, bool instanceOnly )
{
	return IECore::runTimeCast<const T>( plugValueInternal( plug, key, inherit, instanceOnly ) );
}

} // namespace Gaffer

#endif // GAFFER_METADATA_INL
