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

#ifndef GAFFERSCENE_OUTPUTS_H
#define GAFFERSCENE_OUTPUTS_H

#include "GafferScene/GlobalsProcessor.h"

#include "IECoreScene/Output.h"

namespace GafferScene
{

class GAFFERSCENE_API Outputs : public GlobalsProcessor
{

	public :

		Outputs( const std::string &name=defaultName<Outputs>() );
		~Outputs() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::Outputs, OutputsTypeId, GlobalsProcessor );

		Gaffer::ValuePlug *outputsPlug();
		const Gaffer::ValuePlug *outputsPlug() const;

		/// Add an output previously registered with registerOutput().
		Gaffer::ValuePlug *addOutput( const std::string &name );
		Gaffer::ValuePlug *addOutput( const std::string &name, const IECoreScene::Output *output );

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

		static void registerOutput( const std::string &name, const IECoreScene::Output *output );
		static void deregisterOutput( const std::string &name );

		static void registeredOutputs( std::vector<std::string> &names );

	protected :

		void hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Outputs )

} // namespace GafferScene

#endif // GAFFERSCENE_OUTPUTS_H
