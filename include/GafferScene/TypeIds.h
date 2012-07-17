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

#ifndef GAFFERSCENE_TYPEIDS_H
#define GAFFERSCENE_TYPEIDS_H

namespace GafferScene
{

enum TypeId
{
	ScenePlugTypeId = 110501,
	SceneNodeTypeId = 110502,
	FileSourceTypeId = 110503,
	ModelCacheSourceTypeId = 110504,
	SceneProcessorTypeId = 110505,
	SceneElementProcessorTypeId = 110506,
	AttributeCacheTypeId = 110507,
	PrimitiveVariableProcessorTypeId = 110508,
	DeletePrimitiveVariablesTypeId = 110509,
	GroupTypeId = 110510,
	SceneContextProcessorBaseTypeId = 110511,
	SceneContextProcessorTypeId = 110512,
	SceneTimeWarpTypeId = 110513,
	ObjectSourceSceneNodeTypeId = 110514,
	PlaneTypeId = 110515,
	SeedsTypeId = 110516,
	InstancerTypeId = 110517,
	BranchCreatorTypeId = 110518,
	ObjectToSceneTypeId = 110519,
	CameraTypeId = 110520,
	GlobalsProcessorTypeId = 110521,
	DisplaysTypeId = 110522,
	ParameterListPlugTypeId = 110523,
	OptionsTypeId = 110524,
	ShaderTypeId = 110525,
	AssignmentTypeId = 110526,
	
	LastTypeId = 110700
};

} // namespace GafferScene

#endif // GAFFERSCENE_TYPEIDS_H
