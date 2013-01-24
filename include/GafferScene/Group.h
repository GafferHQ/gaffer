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

#ifndef GAFFERSCENE_GROUP_H
#define GAFFERSCENE_GROUP_H

#include "Gaffer/TransformPlug.h"

#include "GafferScene/SceneProcessor.h"

namespace GafferScene
{

class Group : public SceneProcessor
{

	public :

		Group( const std::string &name=staticTypeName() );
		virtual ~Group();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Group, GroupTypeId, SceneProcessor );
		
		Gaffer::StringPlug *namePlug();
		const Gaffer::StringPlug *namePlug() const;
		
		Gaffer::TransformPlug *transformPlug();
		const Gaffer::TransformPlug *transformPlug() const;
		
		virtual void affects( const Gaffer::ValuePlug *input, AffectedPlugsContainer &outputs ) const;
	
	protected :
			
		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;
		virtual IECore::ObjectPtr computeMapping( const Gaffer::Context *context ) const;
		virtual Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual Imath::M44f computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstCompoundObjectPtr computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstObjectPtr computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstStringVectorDataPtr computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const;
		virtual IECore::ConstObjectVectorPtr computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const;

		std::string sourcePath( const std::string &outputPath, const std::string &groupName, ScenePlug **source ) const;
		
	private :
	
		Gaffer::ObjectPlug *mappingPlug();
		const Gaffer::ObjectPlug *mappingPlug() const;
		
		Gaffer::ObjectPlug *inputMappingPlug();
		const Gaffer::ObjectPlug *inputMappingPlug() const;
	
		void childAdded( GraphComponent *parent, GraphComponent *child );
		
		void plugInputChanged( Gaffer::Plug *plug );
		void addAndRemoveInputs();
		virtual void parentChanging( Gaffer::GraphComponent *newParent );
		
		boost::signals::connection m_plugInputChangedConnection;
	
		// we keep this up to date in childAdded(), so no matter how
		// we get the plugs, we can access them quickly.
		std::vector<ScenePlug *> m_inPlugs;

		static size_t g_firstPlugIndex;
			
};

} // namespace GafferScene

#endif // GAFFERSCENE_GROUP_H
