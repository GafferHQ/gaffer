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

#include "ParameterisedHolderBinding.h"

#include "GafferCortex/CompoundParameterHandler.h"
#include "GafferCortex/ParameterisedHolder.h"

#include "GafferDispatchBindings/TaskNodeBinding.h"

#include "GafferBindings/ComputeNodeBinding.h"
#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/Serialisation.h"

#include "fmt/format.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace GafferDispatchBindings;
using namespace GafferCortex;
using namespace GafferCortexModule;

namespace
{

using ParameterisedHolderNodeWrapper = ParameterisedHolderWrapper<NodeWrapper<ParameterisedHolderNode> >;
using ParameterisedHolderDependencyNodeWrapper = ParameterisedHolderWrapper<DependencyNodeWrapper<ParameterisedHolderDependencyNode> >;
using ParameterisedHolderComputeNodeWrapper = ParameterisedHolderWrapper<ComputeNodeWrapper<ParameterisedHolderComputeNode> >;
using ParameterisedHolderTaskNodeWrapper = ParameterisedHolderWrapper<TaskNodeWrapper<ParameterisedHolderTaskNode> >;

template<typename T>
class ParameterisedHolderSerialiser : public NodeSerialiser
{

	std::string postScript( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
	{
		const T *parameterisedHolder = static_cast<const T *>( graphComponent );

		std::string className;
		int classVersion = 0;
		std::string searchPathEnvVar;
		parameterisedHolder->getParameterised( &className, &classVersion, &searchPathEnvVar );

		if( className.size() )
		{
			return fmt::format( "{}.setParameterised( \"{}\", {}, \"{}\", keepExistingValues=True )\n", identifier, className, classVersion, searchPathEnvVar );
		}

		return "";
	}

};

} // namespace

void GafferCortexModule::bindParameterisedHolder()
{

	ParameterisedHolderClass<NodeClass<ParameterisedHolderNode, ParameterisedHolderNodeWrapper> >();
	ParameterisedHolderClass<DependencyNodeClass<ParameterisedHolderDependencyNode, ParameterisedHolderDependencyNodeWrapper> >();
	ParameterisedHolderClass<DependencyNodeClass<ParameterisedHolderComputeNode, ParameterisedHolderComputeNodeWrapper> >();
	ParameterisedHolderClass<TaskNodeClass<ParameterisedHolderTaskNode, ParameterisedHolderTaskNodeWrapper> >();

	Serialisation::registerSerialiser( ParameterisedHolderNode::staticTypeId(), new ParameterisedHolderSerialiser<ParameterisedHolderNode>() );
	Serialisation::registerSerialiser( ParameterisedHolderDependencyNode::staticTypeId(), new ParameterisedHolderSerialiser<ParameterisedHolderDependencyNode>() );
	Serialisation::registerSerialiser( ParameterisedHolderComputeNode::staticTypeId(), new ParameterisedHolderSerialiser<ParameterisedHolderComputeNode>() );
	Serialisation::registerSerialiser( ParameterisedHolderTaskNode::staticTypeId(), new ParameterisedHolderSerialiser<ParameterisedHolderTaskNode>() );

}
