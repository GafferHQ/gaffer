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

#ifndef GAFFERSCENE_PARAMETERLISTPLUG_H
#define GAFFERSCENE_PARAMETERLISTPLUG_H

#include "IECore/CompoundData.h"

#include "Gaffer/CompoundPlug.h"
#include "GafferScene/TypeIds.h"

namespace GafferScene
{

/// This plug provides an easy means of generating arbitrary numbers of parameters
/// for use in IECore::Display, IECore::Camera and IECore::AttributeState etc. Note
/// that parameters in this context are not IECore::Parameters, but just simple
/// named Data values for passing to IECore::Renderer.
/// \todo Could this belong in the Gaffer namespace as simply CompoundDataPlug?. It
/// could be used to make a useful ContextProcessor.
class ParameterListPlug : public Gaffer::CompoundPlug
{

	public :
		
		ParameterListPlug(
			const std::string &name = staticTypeName(),
			Direction direction=In,
			unsigned flags = Default
		);
		virtual ~ParameterListPlug();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( ParameterListPlug, ParameterListPlugTypeId, Gaffer::CompoundPlug );

		/// Accepts only children that can generate values for a parameter list.
		virtual bool acceptsChild( Gaffer::ConstGraphComponentPtr potentialChild ) const;

		Gaffer::CompoundPlug *addParameter( const std::string &name, const IECore::Data *value );

		/// Fills the parameter list with values based on the child plugs of this node.
		void fillParameterList( IECore::CompoundDataMap &parameterList ) const;

};

IE_CORE_DECLAREPTR( ParameterListPlug );

typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, ParameterListPlug> > ParameterListPlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, ParameterListPlug> > InputParameterListPlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, ParameterListPlug> > OutputParameterListPlugIterator;

} // namespace GafferScene

#endif // GAFFERSCENE_PARAMETERLISTPLUG_H
