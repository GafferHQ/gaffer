//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "Loader.h"

#include "IECore/MessageHandler.h"

#include "fmt/format.h"

#include <filesystem>

#ifdef _MSC_VER
#include "Windows.h"
#else
#include "dlfcn.h"
#endif

RixContext *IECoreRenderMan::Loader::context()
{
	static RixContext *g_context = [] () -> RixContext * {

		const char *rmanTree = getenv( "RMANTREE" );
		if( !rmanTree )
		{
			IECore::msg( IECore::Msg::Error, "IECoreRenderMan::Loader", "RMANTREE environment variable not set" );
			return nullptr;
		}

		std::filesystem::path libPath( rmanTree );
		libPath = libPath / "lib" / "libprman";

#ifdef _MSC_VER

		libPath.replace_extension( ".dll" );
		HMODULE handle = LoadLibrary( libPath.generic_string().c_str() );
		if( !handle )
		{
			IECore::msg( IECore::Msg::Error, "IECoreRenderMan::Loader", fmt::format( "Unable to load \"{}\"", libPath.generic_string() ) );
			return nullptr;
		}

		void *symbol = GetProcAddress( handle, "RixGetContext" );
		if( !symbol )
		{
			IECore::msg( IECore::Msg::Error, "IECoreRenderMan::Loader", "Unable to get address of RixGetContext" );
			return nullptr;
		}

#else

		libPath.replace_extension( ".so" );
		void *handle = dlopen( libPath.c_str(), RTLD_NOW | RTLD_GLOBAL );
		if( !handle )
		{
			if( char *e = dlerror() )
			{
				IECore::msg( IECore::Msg::Error, "IECoreRenderMan::Loader", e );
			}
			return nullptr;
		}

		void *symbol = dlsym( handle, "RixGetContext" );
		if( !symbol )
		{
			if( char *e = dlerror() )
			{
				IECore::msg( IECore::Msg::Error, "IECoreRenderMan::Loader", e );
			}
			return nullptr;
		}

#endif

		auto rixGetContext = (RixContext *(*)())symbol;
		return rixGetContext();

	}();
	return g_context;
}

const RiPredefinedStrings &IECoreRenderMan::Loader::strings()
{
	static RiPredefinedStrings g_strings = [] {
		auto resolver = (RixSymbolResolver *)context()->GetRixInterface( k_RixSymbolResolver );
		RiPredefinedStrings s;
		resolver->ResolvePredefinedStrings( s );
		return s;
	}();
	return g_strings;
}
