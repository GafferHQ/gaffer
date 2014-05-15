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

#ifndef GAFFER_EXECUTABLENODE_H
#define GAFFER_EXECUTABLENODE_H

#include "Gaffer/Node.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Context )
IE_CORE_FORWARDDECLARE( ExecutableNode )
IE_CORE_FORWARDDECLARE( ArrayPlug )

/// A base class for nodes with external side effects such as the creation of files,
/// rendering, etc. ExecutableNodes can be chained together with other Executable nodes
/// to define a required execution order. Typically Executable nodes should be executed
/// by Despatcher classes that can query the required execution order and schedule it
/// appropriately.
class ExecutableNode : public Node
{

	public :

		/// A Task defines the execution of an Executable node in a specific Context.
		/// It's used in Executable nodes to describe the requirements and in Despatchers
		/// to represent what they are supposed to execute.
		/// The comparison and hash methods can be used for building sets of unique Tasks.
		/// \todo I think hash(), == and < are badly broken. I don't see any reason
		/// why hash() shouldn't just be returning node->executionHash( context ), because
		/// after all that is already defined to uniquely identify the task. Then I think
		/// operator == and operator < should be defined in terms of the hash as well.
		/// We might also want to consider making Tasks immutable, because any code using
		/// sets/hashes to identify unique tasks is vulnerable to hashes changing - in fact
		/// we have test cases checking that Tasks can be stored in python sets so immutability
		/// of the hash is essential for that to make sense. Perhaps hash should just be a
		/// member variable initialised at construction, and then all member variables should
		/// be made const.
		class Task
		{
			public :

				Task();
				Task( const Task &t );
				Task( ExecutableNodePtr n, ContextPtr c );
				IECore::MurmurHash hash() const;
				bool operator == ( const Task &rhs ) const;
				bool operator < ( const Task &rhs ) const;

				ExecutableNodePtr node;
				ContextPtr context;
		};

		typedef std::vector<Task> Tasks;
		typedef std::vector<ConstContextPtr> Contexts;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::ExecutableNode, ExecutableNodeTypeId, Node );

		ExecutableNode( const std::string &name=defaultName<ExecutableNode>() );
		virtual ~ExecutableNode();

		ArrayPlug *requirementsPlug();
		const ArrayPlug *requirementsPlug() const;

		Plug *requirementPlug();
		const Plug *requirementPlug() const;

		/// Fills requirements with all tasks that must be completed before execute()
		/// can be called. The default implementation declares requirements defined
		/// by the inputs to the requirementsPlug().
		virtual void executionRequirements( const Context *context, Tasks &requirements ) const;

		/// Returns a hash that uniquely represents the side effects (files created etc) of
		/// calling execute with the given context. If the node returns the default hash it
		/// means this node does not compute anything.
		virtual IECore::MurmurHash executionHash( const Context *context ) const = 0;

		/// Executes this node for all the specified contexts in sequence.
		virtual void execute( const Contexts &contexts ) const = 0;
		
	protected :
	
		/// Implemented to deny inputs to requirementsPlug() which do not come from
		/// the requirementPlug() of another ExecutableNode.
		virtual bool acceptsInput( const Plug *plug, const Plug *inputPlug ) const;

	private :
	
		static size_t g_firstPlugIndex;

};

} // namespace Gaffer

#endif // GAFFER_EXECUTABLENODE_H
