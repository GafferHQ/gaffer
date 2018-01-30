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

#include "boost/python.hpp"

#include "DirtyPropagationScopeBinding.h"

#include "Gaffer/DirtyPropagationScope.h"

#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace Gaffer;

namespace
{

class DirtyPropagationScopeWrapper : boost::noncopyable
{

	public :

		DirtyPropagationScopeWrapper()
			:	m_scope( nullptr )
		{
		}

		~DirtyPropagationScopeWrapper()
		{
			reset();
		}

		void enter()
		{
			reset();
			m_scope = new DirtyPropagationScope();
		}

		void exit( object type, object value, object traceback )
		{
			reset();
		}

	private :

		void reset()
		{
			if( !m_scope )
			{
				return;
			}

			// The destructor for the scope may trigger a dirty
			// propagation, and observers of plugDirtiedSignal() may
			// well invoke a compute. We need to release the GIL so that
			// if that compute is multithreaded, those threads can acquire
			// the GIL for python based nodes and expressions.
			IECorePython::ScopedGILRelease gilRelease;
			delete m_scope;
			m_scope = nullptr;
		}

		DirtyPropagationScope *m_scope;

};

} // namespace

void GafferModule::bindDirtyPropagationScope()
{
	class_<DirtyPropagationScopeWrapper, boost::noncopyable>( "DirtyPropagationScope" )
		.def( "__enter__", &DirtyPropagationScopeWrapper::enter )
		.def( "__exit__", &DirtyPropagationScopeWrapper::exit )
	;
}
