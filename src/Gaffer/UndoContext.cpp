//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "IECore/MessageHandler.h"

#include "Gaffer/UndoContext.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Action.h"

using namespace Gaffer;

UndoContext::UndoContext( ScriptNodePtr script, State state )
	:	m_script( script )
{
	if( state==Invalid )
	{
		throw IECore::Exception( "Cannot construct UndoContext with Invalid state." );
	}
	if( m_script )
	{	
		m_stateStackSize = script->m_undoStateStack.size();
		script->m_undoStateStack.push( state );
		if( m_stateStackSize==0 )
		{
			assert( script->m_actionAccumulator==0 );
			script->m_actionAccumulator = ScriptNode::ActionVectorPtr( new ScriptNode::ActionVector() );
		}
	}
}

UndoContext::~UndoContext()
{
	if( m_script )
	{
		m_script->m_undoStateStack.pop();
		if( m_script->m_undoStateStack.size()!=m_stateStackSize )
		{
			IECore::msg( IECore::Msg::Warning, "UndoContext::~UndoContext", "Bad undo stack nesting detected" ); 
		}
		if( m_script->m_undoStateStack.size()==0 )
		{
			if( m_script->m_actionAccumulator->size() )
			{
				m_script->m_undoList.erase( m_script->m_undoIterator, m_script->m_undoList.end() );
				m_script->m_undoList.insert( m_script->m_undoList.end(), m_script->m_actionAccumulator );
				m_script->m_undoIterator = m_script->m_undoList.end();
			}
			m_script->m_actionAccumulator = ScriptNode::ActionVectorPtr();
		}
	}
}
