//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#pragma once

#include "Gaffer/TypedPlug.h"
#include "Gaffer/NameValuePlug.h"

#include "IECore/CompoundData.h"
#include "IECore/CompoundObject.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

/// This plug provides an easy means of building CompoundData containing
/// arbitrary keys and values, where each key and value is represented
/// by an individual Gaffer::NameValuePlug.
class GAFFER_API CompoundDataPlug : public Gaffer::ValuePlug
{

	public :

		explicit CompoundDataPlug(
			const std::string &name = defaultName<CompoundDataPlug>(),
			Direction direction=In,
			unsigned flags = Default
		);
		~CompoundDataPlug() override;

		GAFFER_PLUG_DECLARE_TYPE( Gaffer::CompoundDataPlug, CompoundDataPlugTypeId, Gaffer::ValuePlug );

		/// Accepts only children that can generate values for the CompoundData.
		bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const override;
		PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		/// Adds each member from the specified CompoundData.
		void addMembers( const IECore::CompoundData *members, bool useNameAsPlugName = false );

		/// Returns the value for the member specified by the child parameterPlug, and fills name with the
		/// name for the member. If the user has disabled the member or the name is the empty string, then
		/// 0 is returned.
		IECore::DataPtr memberDataAndName( const NameValuePlug *parameterPlug, std::string &name ) const;

		/// Fills the CompoundDataMap with values based on the child plugs of this node.
		void fillCompoundData( IECore::CompoundDataMap &compoundDataMap ) const;
		/// As above but fills a CompoundObjectMap instead.
		void fillCompoundObject( IECore::CompoundObject::ObjectMap &compoundObjectMap ) const;

		IECore::MurmurHash hash() const override;
		void hash( IECore::MurmurHash &h ) const;

};

IE_CORE_DECLAREPTR( CompoundDataPlug );

} // namespace Gaffer
