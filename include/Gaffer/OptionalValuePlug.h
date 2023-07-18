//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "Gaffer/TypeIds.h"

#include "Gaffer/TypedPlug.h"

namespace Gaffer
{

class GAFFER_API OptionalValuePlug : public Gaffer::ValuePlug
{

	public :

		GAFFER_PLUG_DECLARE_TYPE( Gaffer::OptionalValuePlug, OptionalValuePlugTypeId, Gaffer::ValuePlug );

		OptionalValuePlug(
			IECore::InternedString name,
			const Gaffer::ValuePlugPtr &valuePlug,
			bool enabledPlugDefaultValue = false,
			Direction direction = In,
			unsigned flags = Default
		);

		Gaffer::BoolPlug *enabledPlug();
		const Gaffer::BoolPlug *enabledPlug() const;

		template<typename T = Gaffer::ValuePlug>
		T *valuePlug();
		template<typename T = Gaffer::ValuePlug>
		const T *valuePlug() const;

		bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const override;
		Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

};

IE_CORE_DECLAREPTR( OptionalValuePlug );

} // namespace Gaffer

#include "Gaffer/OptionalValuePlug.inl"
