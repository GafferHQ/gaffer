//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "boost/python.hpp"
#include "boost/format.hpp"

#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/Wrapper.h"

#include "Gaffer/ParameterisedHolder.h"
#include "Gaffer/CompoundParameterHandler.h"

#include "GafferBindings/ParameterisedHolderBinding.h"
#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/ComputeNodeBinding.h"
#include "GafferBindings/Serialisation.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

typedef ParameterisedHolderWrapper<NodeWrapper<ParameterisedHolderNode> > ParameterisedHolderNodeWrapper;
typedef ParameterisedHolderWrapper<DependencyNodeWrapper<ParameterisedHolderDependencyNode> > ParameterisedHolderDependencyNodeWrapper;
typedef ParameterisedHolderWrapper<ComputeNodeWrapper<ParameterisedHolderComputeNode> > ParameterisedHolderComputeNodeWrapper;

IE_CORE_DECLAREPTR( ParameterisedHolderNodeWrapper )
IE_CORE_DECLAREPTR( ParameterisedHolderDependencyNodeWrapper )
IE_CORE_DECLAREPTR( ParameterisedHolderComputeNodeWrapper )

template<typename T>
class ParameterisedHolderSerialiser : public NodeSerialiser
{

	virtual std::string postScript( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
	{
		const T *parameterisedHolder = static_cast<const T *>( graphComponent );
		
		std::string className;
		int classVersion = 0;
		std::string searchPathEnvVar;
		parameterisedHolder->getParameterised( &className, &classVersion, &searchPathEnvVar );
		
		if( className.size() )
		{
			return boost::str( boost::format( "%s.setParameterised( \"%s\", %d, \"%s\", keepExistingValues=True )\n" ) % identifier % className % classVersion % searchPathEnvVar );
		}

		return "";
	}

};

void GafferBindings::bindParameterisedHolder()
{

	ParameterisedHolderClass<NodeClass<ParameterisedHolderNode, ParameterisedHolderNodeWrapperPtr> >();
	ParameterisedHolderClass<DependencyNodeClass<ParameterisedHolderDependencyNode, ParameterisedHolderDependencyNodeWrapperPtr> >();
	ParameterisedHolderClass<DependencyNodeClass<ParameterisedHolderComputeNode, ParameterisedHolderComputeNodeWrapperPtr> >();

	Serialisation::registerSerialiser( ParameterisedHolderNode::staticTypeId(), new ParameterisedHolderSerialiser<ParameterisedHolderNode>() );
	Serialisation::registerSerialiser( ParameterisedHolderDependencyNode::staticTypeId(), new ParameterisedHolderSerialiser<ParameterisedHolderDependencyNode>() );
	Serialisation::registerSerialiser( ParameterisedHolderComputeNode::staticTypeId(), new ParameterisedHolderSerialiser<ParameterisedHolderComputeNode>() );

}
