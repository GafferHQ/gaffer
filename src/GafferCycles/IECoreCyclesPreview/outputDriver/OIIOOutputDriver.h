//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Alex Fuller. All rights reserved.
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
//      * Neither the name of Alex Fuller nor the names of
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

// Cycles
#include "kernel/types.h"
#include "session/output_driver.h"

// Cortex
#include "IECore/CompoundData.h"
#include "IECore/InternedString.h"

// OIIO
#include "OpenImageIO/typedesc.h"

namespace IECoreCycles
{

class OIIOOutputDriver : public ccl::OutputDriver
{
	public:

		OIIOOutputDriver( const Imath::Box2i &displayWindow, const Imath::Box2i &dataWindow, IECore::ConstCompoundDataPtr parameters );
		virtual ~OIIOOutputDriver();

		void write_render_tile( const Tile &tile ) override;

	protected:

		struct Layer
		{
			std::string name;
			int numChannels;
			std::string path;
			OIIO::TypeDesc typeDesc;
			ccl::PassType passType;
			IECore::CompoundDataPtr metadata;
		};

		Imath::Box2i m_displayWindow;
		Imath::Box2i m_dataWindow;
		typedef std::vector<Layer> Layers;
		Layers m_layers;
};

} // namespace
