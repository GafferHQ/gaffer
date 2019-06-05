//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/ThreadState.h"

#include "Gaffer/Context.h"
#include "Gaffer/Monitor.h"

#include "tbb/enumerable_thread_specific.h"

using namespace Gaffer;

namespace
{

using Stack = std::stack<ThreadState>;
tbb::enumerable_thread_specific<Stack, tbb::cache_aligned_allocator<Stack>, tbb::ets_key_per_instance> g_stack;

ContextPtr g_defaultContext = new Context;

} // namespace

const ThreadState::MonitorSet ThreadState::g_defaultMonitors;
const ThreadState ThreadState::g_defaultState;

ThreadState::ThreadState()
	:	m_context( g_defaultContext.get() ), m_process( nullptr ), m_monitors( &g_defaultMonitors )
{
}

ThreadState::Scope::Scope( const ThreadState &state )
	:	m_stack( &g_stack.local() )
{
	m_stack->push( state );
	m_threadState = &m_stack->top();
}

ThreadState::Scope::Scope( bool push )
	:	m_threadState( nullptr ), m_stack( nullptr )
{
	if( push )
	{
		m_stack = &g_stack.local();
		m_stack->push( m_stack->size() ? m_stack->top() : g_defaultState );
		m_threadState = &m_stack->top();
	}
}

ThreadState::Scope::~Scope()
{
	if( m_stack )
	{
		m_stack->pop();
	}
}

const ThreadState &ThreadState::current()
{
	const Stack &stack = g_stack.local();
	return stack.size() ? stack.top() : g_defaultState;
}
