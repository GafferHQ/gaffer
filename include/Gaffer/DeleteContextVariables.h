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

#ifndef GAFFER_DELETECONTEXTVARIABLES_H
#define GAFFER_DELETECONTEXTVARIABLES_H

#include "Gaffer/ContextProcessor.h"
#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/StringPlug.h"

namespace Gaffer
{

template<typename BaseType>
class DeleteContextVariables : public ContextProcessor<BaseType>
{

	public :

		IECORE_RUNTIMETYPED_DECLARETEMPLATE( DeleteContextVariables<BaseType>, ContextProcessor<BaseType> );
		IE_CORE_DECLARERUNTIMETYPEDDESCRIPTION( DeleteContextVariables<BaseType> );

		DeleteContextVariables( const std::string &name=GraphComponent::defaultName<DeleteContextVariables>() );
		virtual ~DeleteContextVariables();

		StringPlug *variablesPlug();
		const StringPlug *variablesPlug() const; 

		void affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const;

	protected :

		virtual void processContext( Context *context ) const;

	private :

		static size_t g_firstPlugIndex;

};

typedef DeleteContextVariables<ComputeNode> DeleteContextVariablesComputeNode;
IE_CORE_DECLAREPTR( DeleteContextVariablesComputeNode );

} // namespace Gaffer

#endif // GAFFER_DELETECONTEXTVARIABLES_H
