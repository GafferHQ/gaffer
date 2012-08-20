//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFER_EXPRESSIONNODE_H
#define GAFFER_EXPRESSIONNODE_H

#include "Gaffer/Node.h"
#include "Gaffer/TypedPlug.h"

namespace Gaffer
{

class ExpressionNode : public Node
{

	public :

		ExpressionNode( const std::string &name=staticTypeName() );
		virtual ~ExpressionNode();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( ExpressionNode, ExpressionNodeTypeId, Node );
		
		StringPlug *enginePlug();
		const StringPlug *enginePlug() const;
		
		StringPlug *expressionPlug();
		const StringPlug *expressionPlug() const;
		
		IE_CORE_FORWARDDECLARE( Engine )
		
		class Engine : public IECore::RefCounted
		{
			
			public :
				
				IE_CORE_DECLAREMEMBERPTR( Engine );
				
				/// Must return a path to the plug the expression wishes to set.
				/// Paths should be of the form nodeName.plugName, and are expected to
				/// be relative to the parent of the ExpressionNode.
				virtual std::string outPlug() = 0;
				/// Must fill plugs with paths to the plugs the expression wishes to read from.
				/// Paths should be of the form nodeName.plugName, and are expected to be relative to
				/// the parent of the expression node.
				virtual void inPlugs( std::vector<std::string> &plugPaths ) = 0;
				/// Must execute the expression in the specified context, using the values
				/// provided by proxyInputs and setting the result in proxyOutput.
				virtual void execute( const Context *context, const std::vector<const ValuePlug *> &proxyInputs, ValuePlug *proxyOutput ) = 0;
				
				static EnginePtr create( const std::string engineType, const std::string &expression );
				
				typedef boost::function<EnginePtr ( const std::string &expression )> Creator;
				static void registerEngine( const std::string engineType, Creator creator );
				static void registeredEngines( std::vector<std::string> &engineTypes );

			private :
			
				typedef std::map<std::string, Creator> CreatorMap;
				static CreatorMap &creators();
				
		};
		
		virtual void affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const;
		
	protected :
		
		virtual void compute( ValuePlug *output, const Context *context ) const;
		
	private :
	
		void plugSet( Plug *plug );
		void parentChanged( GraphComponent *child, GraphComponent *oldParent );
		
		void updatePlugs( const std::string &outPlugPath, std::vector<std::string> &inPlugPaths );
		ValuePlugPtr createPlug( const ValuePlug *partner ) const;
		
		EnginePtr m_engine;
		
};

} // namespace Gaffer

#endif // GAFFER_EXPRESSIONNODE_H
