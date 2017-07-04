//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERCORTEX_DATETIMEPARAMETERHANDLER_H
#define GAFFERCORTEX_DATETIMEPARAMETERHANDLER_H

#include "IECore/DateTimeParameter.h"

#include "GafferCortex/Export.h"
#include "GafferCortex/ParameterHandler.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferCortex
{

class GAFFERCORTEX_API DateTimeParameterHandler : public ParameterHandler
{

	public :

		IE_CORE_DECLAREMEMBERPTR( DateTimeParameterHandler );

		DateTimeParameterHandler( IECore::DateTimeParameterPtr parameter );
		virtual ~DateTimeParameterHandler();

		virtual IECore::Parameter *parameter();
		virtual const IECore::Parameter *parameter() const;
		virtual void restore( Gaffer::GraphComponent *plugParent );
		virtual Gaffer::Plug *setupPlug( Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction=Gaffer::Plug::In, unsigned flags = Gaffer::Plug::Default | Gaffer::Plug::Dynamic );
		virtual Gaffer::Plug *plug();
		virtual const Gaffer::Plug *plug() const;
		virtual void setParameterValue();
		virtual void setPlugValue();

	private :

		IECore::DateTimeParameterPtr m_parameter;
		Gaffer::StringPlugPtr m_plug;

		static ParameterHandlerDescription<DateTimeParameterHandler, IECore::DateTimeParameter> g_description;

};

} // namespace GafferCortex

#endif // GAFFERCORTEX_DATETIMEPARAMETERHANDLER_H
