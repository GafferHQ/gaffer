//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

#include "boost/python.hpp"

#include "Gaffer/SetExpressionAlgo.h"

#include "IECorePython/ScopedGILLock.h"
#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;

namespace
{

struct SetProviderWrapper : Gaffer::SetExpressionAlgo::SetProvider, wrapper<Gaffer::SetExpressionAlgo::SetProvider>
{

	IECore::ConstInternedStringVectorDataPtr setNames() const override
	{
		IECorePython::ScopedGILLock gilLock;
		object result = this->get_override( "setNames" )();
		extract<IECore::InternedStringVectorData *> e( result );

		if( e.check() )
		{
			return IECore::ConstInternedStringVectorDataPtr( e() );
		}
		else
		{
			return IECore::ConstInternedStringVectorDataPtr();
		}
	}

	const IECore::PathMatcher paths( const std::string &setName ) const override
	{
		IECorePython::ScopedGILLock gilLock;
		object result = this->get_override( "paths" )( setName );
		extract<IECore::PathMatcher> e( result );

		if( e.check() )
		{
			return e();
		}
		else
		{
			return IECore::PathMatcher();
		}
	}

	void hash( const std::string &setName, IECore::MurmurHash &h ) const override
	{
		IECorePython::ScopedGILLock gilLock;
		object pythonHash( h );
		this->get_override( "hash" )( setName, pythonHash );
		h = extract<IECore::MurmurHash>( pythonHash );
	}

};

IECore::PathMatcher evaluateSetExpressionWrapper( const std::string &setExpression, const Gaffer::SetExpressionAlgo::SetProvider &setProvider )
{
	IECorePython::ScopedGILRelease r;
	return evaluateSetExpression( setExpression, setProvider );
}

IECore::MurmurHash setExpressionHashWrapper1( const std::string &setExpression, const Gaffer::SetExpressionAlgo::SetProvider &setProvider )
{
	IECorePython::ScopedGILRelease r;
	return setExpressionHash( setExpression, setProvider );
}

void setExpressionHashWrapper2( const std::string &setExpression, const Gaffer::SetExpressionAlgo::SetProvider &setProvider, IECore::MurmurHash &h )
{
	IECorePython::ScopedGILRelease r;
	setExpressionHash( setExpression, setProvider, h );
}

}

namespace GafferModule
{

void bindSetExpressionAlgo()
{
	object module( borrowed( PyImport_AddModule( "Gaffer.SetExpressionAlgo" ) ) );
	scope().attr( "SetExpressionAlgo" ) = module;
	scope moduleScope( module );

	class_<SetProviderWrapper, boost::noncopyable>( "SetProvider" );

	def( "evaluateSetExpression", &evaluateSetExpressionWrapper );
	def( "setExpressionHash", &setExpressionHashWrapper1 );
	def( "setExpressionHash", &setExpressionHashWrapper2 );
	def( "simplify", &Gaffer::SetExpressionAlgo::simplify );
	def( "include", &Gaffer::SetExpressionAlgo::include );
	def( "exclude", &Gaffer::SetExpressionAlgo::exclude );
}

} // namespace GafferModule
