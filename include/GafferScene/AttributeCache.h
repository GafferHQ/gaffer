//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENE_ATTRIBUTECACHE_H
#define GAFFERSCENE_ATTRIBUTECACHE_H

#include "GafferScene/SceneElementProcessor.h"

namespace GafferScene
{

/// The AttributeCache node applies data previously cached using IECore::AttributeCache.
class AttributeCache : public SceneElementProcessor
{

	public :

		AttributeCache( const std::string &name=staticTypeName() );
		virtual ~AttributeCache();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( AttributeCache, AttributeCacheTypeId, SceneElementProcessor );
		
		/// Holds the name of the attribute cache file or sequence to be loaded.
		Gaffer::StringPlug *fileNamePlug();
		const Gaffer::StringPlug *fileNamePlug() const;

		virtual void affects( const Gaffer::ValuePlug *input, AffectedPlugsContainer &outputs ) const;
				
	protected :
		
		virtual Imath::Box3f processBound( const ScenePath &path, const Gaffer::Context *context, const Imath::Box3f &inputBound ) const;
		virtual Imath::M44f processTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const;
		virtual IECore::ObjectPtr processObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const;

		std::string entryForPath( const ScenePath &path ) const;
		
};

} // namespace GafferScene

#endif // GAFFERSCENE_ATTRIBUTECACHE_H
