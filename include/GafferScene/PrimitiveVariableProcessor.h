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

#ifndef GAFFERSCENE_PRIMITIVEVARIABLEPROCESSOR_H
#define GAFFERSCENE_PRIMITIVEVARIABLEPROCESSOR_H

#include "GafferScene/SceneElementProcessor.h"

namespace GafferScene
{

/// The PrimitiveVariableProcessor base class simplifies the process of manipulating
/// primitive variables.
class PrimitiveVariableProcessor : public SceneElementProcessor
{

	public :

		PrimitiveVariableProcessor( const std::string &name=defaultName<PrimitiveVariableProcessor>() );
		virtual ~PrimitiveVariableProcessor();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::PrimitiveVariableProcessor, PrimitiveVariableProcessorTypeId, SceneElementProcessor );
		
		Gaffer::StringPlug *namesPlug();
		const Gaffer::StringPlug *namesPlug() const;
		
		Gaffer::BoolPlug *invertNamesPlug();
		const Gaffer::BoolPlug *invertNamesPlug() const;

		/// Implemented so that namesPlug() affects outPlug()->objectPlug().
		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;
				
	protected :
		
		/// Implemented to call processPrimitiveVariable() for the appropriate variables of inputObject.
		virtual bool processesObject() const;
		virtual void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const;
		
		/// Must be implemented by subclasses to process the primitive variable in place.
		virtual void processPrimitiveVariable( const ScenePath &path, const Gaffer::Context *context, IECore::ConstPrimitivePtr inputGeometry, IECore::PrimitiveVariable &inputVariable ) const = 0;

	private :
	
		static size_t g_firstPlugIndex;
	
};

} // namespace GafferScene

#endif // GAFFERSCENE_PRIMITIVEVARIABLEPROCESSOR_H
