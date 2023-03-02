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

#pragma once

#include "GafferOSL/Export.h"
#include "GafferOSL/TypeIds.h"

#include "Gaffer/Plug.h"

#include "IECore/CompoundObject.h"

namespace GafferOSL
{

/// Plug that provides a proxy for representing closure types when
/// loader a shader from OSL or a renderer.  We probably won't be able
/// to set or get closure plugs, but we need to be able to connect
/// them, and they should only connect to other closure plugs.
class GAFFEROSL_API ClosurePlug : public Gaffer::Plug
{

	public :

		ClosurePlug( const std::string &name=defaultName<ClosurePlug>(), Direction direction=In, unsigned flags=Default );
		~ClosurePlug() override;

		GAFFER_PLUG_DECLARE_TYPE( GafferOSL::ClosurePlug, ClosurePlugTypeId, Plug );

		bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const override;
		Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;
		bool acceptsInput( const Gaffer::Plug *input ) const override;

	private:

};

IE_CORE_DECLAREPTR( ClosurePlug );

} // namespace GafferOSL
