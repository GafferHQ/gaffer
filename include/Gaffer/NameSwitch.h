//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_NAMESWITCH_H
#define GAFFER_NAMESWITCH_H

#include "Gaffer/Switch.h"

namespace Gaffer
{

class StringPlug;

class IECORE_EXPORT NameSwitch : public Switch
{

	public :

		GAFFER_NODE_DECLARE_TYPE( Gaffer::NameSwitch, NameSwitchTypeId, Switch );

		NameSwitch( const std::string &name=GraphComponent::defaultName<NameSwitch>() );
		~NameSwitch() override;

		void setup( const Plug *plug );

		StringPlug *selectorPlug();
		const StringPlug *selectorPlug() const;

		void affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override;
		void compute( ValuePlug *output, const Context *context ) const override;

	private :

		IntPlug *outIndexPlug();
		const IntPlug *outIndexPlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( NameSwitch );

} // namespace Gaffer

#endif // GAFFER_NAMESWITCH_H
