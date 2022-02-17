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

#include "Gaffer/ContextAlgo.h"

#include "Gaffer/Plug.h"

#include "boost/container/flat_map.hpp"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace Gaffer::ContextAlgo;

namespace
{

using GlobalScopeMap = boost::container::flat_map<IECore::TypeId, vector<InternedString>>;
GlobalScopeMap &globalScopeMap()
{
	static GlobalScopeMap g_m;
	return g_m;
}

} // namespace

GlobalScope::GlobalScope( const Context *context, const Plug *plug )
{
	const GlobalScopeMap &m = globalScopeMap();
	auto it = m.find( plug->typeId() );
	if( it != m.end() )
	{
		m_scope.emplace( context );
		for( const auto &n : it->second )
		{
			m_scope->remove( n );
		}
	}
}

GlobalScope::~GlobalScope()
{
}

GlobalScope::Registration::Registration( IECore::TypeId plugTypeId, const std::initializer_list<IECore::InternedString> &variablesToErase )
{
	vector<InternedString> &v = globalScopeMap()[plugTypeId];
	v.insert( v.end(), variablesToErase );
}
