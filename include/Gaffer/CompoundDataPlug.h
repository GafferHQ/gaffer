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

#ifndef GAFFER_COMPOUNDDATAPLUG_H
#define GAFFER_COMPOUNDDATAPLUG_H

#include "IECore/CompoundData.h"
#include "IECore/CompoundObject.h"

#include "Gaffer/CompoundPlug.h"

namespace Gaffer
{

/// This plug provides an easy means of building CompoundData containing
/// arbitrary keys and values, where each key and value is represented
/// by an individual child plug.
class CompoundDataPlug : public Gaffer::CompoundPlug
{

	public :
		
		CompoundDataPlug(
			const std::string &name = staticTypeName(),
			Direction direction=In,
			unsigned flags = Default
		);
		virtual ~CompoundDataPlug();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( CompoundDataPlug, CompoundDataPlugTypeId, Gaffer::CompoundPlug );

		/// Accepts only children that can generate values for the CompoundData.
		virtual bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const;

		Gaffer::CompoundPlug *addMember( const std::string &name, const IECore::Data *value );
		void addMembers( const IECore::CompoundData *parameters );
		
		/// Fills the CompoundDataMap with values based on the child plugs of this node.
		void fillCompoundData( IECore::CompoundDataMap &compoundDataMap ) const;
		/// As above but fills a CompoundObjectMap instead.
		void fillCompoundObject( IECore::CompoundObject::ObjectMap &compoundObjectMap ) const;

	private :
	
		IECore::DataPtr parameterDataAndName( const CompoundPlug *parameterPlug, std::string &name ) const;

};

IE_CORE_DECLAREPTR( CompoundDataPlug );

typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, CompoundDataPlug> > CompoundDataPlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, CompoundDataPlug> > InputCompoundDataPlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, CompoundDataPlug> > OutputCompoundDataPlugIterator;

} // namespace Gaffer

#endif // GAFFER_COMPOUNDDATAPLUG_H
