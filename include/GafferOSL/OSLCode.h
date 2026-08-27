//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferOSL/OSLShader.h"

#include <unordered_map>

namespace GafferOSL
{

class GAFFEROSL_API OSLCode : public OSLShader
{

	public :

		explicit OSLCode( const std::string &name=defaultName<OSLCode>() );
		~OSLCode() override;

		GAFFER_NODE_DECLARE_TYPE( GafferOSL::OSLCode, OSLCodeTypeId, OSLShader );

		Gaffer::StringPlug *codePlug();
		const Gaffer::StringPlug *codePlug() const;

		/// Returns the source to a complete OSL shader created
		/// from this node, optionally specifying a specific name
		/// to give to it.
		std::string source( const std::string shaderName = "" ) const;

		// This is implemented to do nothing, because OSLCode node generates the shader from
		// the plugs, and not the other way around.  We don't want to inherit the loading behaviour
		// from OSLShader which tries to match the plugs to a shader on disk
		void loadShader( const std::string &shaderName, bool keepExistingValues=false ) override;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	private :

		// We connect the output from this into our `name` plug, allowing us
		// to generate the shader on disk "just in time", when the NetworkCreator
		// evaluates the name.
		Gaffer::StringPlug *shaderNamePlug();
		const Gaffer::StringPlug *shaderNamePlug() const;

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;
		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;

		void outputAdded();
		void outputRemoved();

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( OSLCode )

} // namespace GafferOSL
