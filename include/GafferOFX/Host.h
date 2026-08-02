//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Lucien Fostier. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "GafferOFX/Export.h"

#include "HostSupport/ofxhPluginCache.h"
#include "HostSupport/ofxhImageEffectAPI.h"


namespace GafferOFX
{

class GAFFEROFX_API Host : public OFX::Host::ImageEffect::Host
{
	public :

		Host();

		OFX::Host::ImageEffect::Instance* newInstance(
			void* clientData,
			OFX::Host::ImageEffect::ImageEffectPlugin* plugin,
			OFX::Host::ImageEffect::Descriptor& desc,
			const std::string& context
		) override;

		OFX::Host::ImageEffect::Descriptor* makeDescriptor(OFX::Host::ImageEffect::ImageEffectPlugin* plugin) override;
		OFX::Host::ImageEffect::Descriptor* makeDescriptor(
			const OFX::Host::ImageEffect::Descriptor& rootContext,
			OFX::Host::ImageEffect::ImageEffectPlugin* plugin
		) override;
		OFX::Host::ImageEffect::Descriptor* makeDescriptor(
			const std::string& bundlePath,
			OFX::Host::ImageEffect::ImageEffectPlugin* plugin
		) override;

		OfxStatus vmessage(
			const char* type,
			const char* id,
			const char* format,
			va_list args
		) override;

		OfxStatus setPersistentMessage(
			const char* type,
			const char* id,
			const char* format,
			va_list args
		) override;

		OfxStatus clearPersistentMessage() override;

		static Host& instance();
		static void findOFXPlugins();
		static std::vector<std::string> pluginIDs();
		static std::map<std::string, std::string> pluginBundles();
		OfxStatus flushOpenGLResources() const override;

		static OFX::Host::ImageEffect::PluginCache m_pluginCache;
};

} // GafferOFX

