//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
//  
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//  
//	  * Redistributions of source code must retain the above
//		copyright notice, this list of conditions and the following
//		disclaimer.
//  
//	  * Redistributions in binary form must reproduce the above
//		copyright notice, this list of conditions and the following
//		disclaimer in the documentation and/or other materials provided with
//		the distribution.
//  
//	  * Neither the name of John Haddon nor the names of
//		any other contributors to this software may be used to endorse or
//		promote products derived from this software without specific prior
//		written permission.
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

#ifndef GAFFER_EXECUTABLE_H
#define GAFFER_EXECUTABLE_H

#include <vector>
#include "IECore/MurmurHash.h"
#include "IECore/RefCounted.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Node )
IE_CORE_FORWARDDECLARE( Context )
IE_CORE_FORWARDDECLARE( Plug )

/// Pure virtual class to allow the definition of nodes with external side effects
/// such as creation of files, rendering, etc.
/// These nodes also can be chained together with other Executable nodes as requirement 
/// for their execution. 
/// They also define a hash that uniquely identify the results of an execution on a given context.
/// Executable nodes are operated by Despatcher objects that know
/// how to query the requirements and schedule their execution appropriately.
class Executable
{
	public :

		/// A Task defines the execution of an Executable node in a specific Context.
		/// It's used in Executable nodes to describe the requirements and in Despatchers
		/// to represent what they are supposed to execute.
		/// The comparison and hash methods can be used for building sets of unique Tasks.
		class Task
		{
			public :

				Task();
				Task( const Task &t );
				Task( NodePtr n, ContextPtr c );
				IECore::MurmurHash hash() const;
				bool operator == ( const Task &rhs ) const;
				bool operator < ( const Task &rhs ) const;

				NodePtr node;
				ContextPtr context;
		};

		typedef std::vector<Task> Tasks;
		typedef std::vector<ConstContextPtr> Contexts;

		virtual ~Executable();

		/// Must be implemented to specify all the requirements which must be satisfied
		/// before it is allowed to call execute() with the given context.
		virtual void executionRequirements( const Context *context, Tasks &requirements ) const = 0;

		/// Must be implemented to set a hash that uniquely represents the
		/// side effects (files created etc) of calling execute with the given context.
		/// If the node returns the default hash it means this node does not compute anything.
		virtual IECore::MurmurHash executionHash( const Context *context ) const = 0;

		/// Must be implemented to execute in all the specified contexts
		/// in sequence.
		virtual void execute( const Contexts &contexts ) const = 0;	

	protected :

		/// Constructs the Executable for the Node, also creates the plugs that 
		/// allows connecting one Executable node to another as pre-requisite for it's execution.
		Executable( Node *node );

		/// Utility function that derived classes can call during their executionRequirements(), which will simply
		/// query the 'requirements' plug for it's connection and will set the same input context for each connected node.
		static void defaultRequirements( const Node *node, const Context *context, Tasks &requirements );

		/// Utility function that derived classes can call during their acceptsInput(), which will only return False if 
		/// the plug that is being connected is the 'requirements' plug, and it is connecting to a node that is not Executable.
		static bool acceptsRequirementsInput( const Plug *plug, const Plug *inputPlug );

};

} // namespace Gaffer

#endif // GAFFER_EXECUTABLE_H
