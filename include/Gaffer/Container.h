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

#ifndef GAFFER_CONTAINER_H
#define GAFFER_CONTAINER_H

#include "Gaffer/Export.h"

namespace Gaffer
{

template<typename Base, typename T>
class GAFFER_EXPORT Container : public Base
{

	public :

		IE_CORE_DECLAREMEMBERPTR( Container );

		Container();
		virtual ~Container();

		//! @name RunTimeTyped interface
		////////////////////////////////////////////////////////////
		//@{
		virtual IECore::TypeId typeId() const;
		virtual const char *typeName() const;
		virtual bool isInstanceOf( IECore::TypeId typeId ) const;
		virtual bool isInstanceOf( const char *typeName ) const;
		static IECore::TypeId staticTypeId();
		static const char *staticTypeName();
		static bool inheritsFrom( IECore::TypeId typeId );
		static bool inheritsFrom( const char *typeName );
		typedef Base BaseClass;
		//@}

		/// Accepts only type T.
		virtual bool acceptsChild( const GraphComponent *potentialChild ) const;

	private :

		static const IECore::RunTimeTyped::TypeDescription< Container<Base, T> > g_typeDescription;
};

#define GAFFER_DECLARECONTAINERSPECIALISATIONS( TYPENAME, TYPEID  )			\
																			\
	template<> GAFFER_EXPORT												\
	IECore::TypeId TYPENAME::staticTypeId()									\
	{																		\
		return (IECore::TypeId)TYPEID;										\
	}																		\
	template<> GAFFER_EXPORT												\
	const char *TYPENAME::staticTypeName()									\
	{																		\
		return #TYPENAME;													\
	}																		\
	template<> GAFFER_EXPORT 												\
	const IECore::RunTimeTyped::TypeDescription<TYPENAME>  TYPENAME::g_typeDescription; \


} // namespace Gaffer

#include "Gaffer/Container.inl"

#endif // GAFFER_CONTAINER_H
