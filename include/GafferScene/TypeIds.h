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

#ifndef GAFFERSCENE_TYPEIDS_H
#define GAFFERSCENE_TYPEIDS_H

namespace GafferScene
{

enum TypeId
{
	ScenePlugTypeId = 110501,
	SceneNodeTypeId = 110502,
	FileSourceTypeId = 110503,
	ModelCacheSourceTypeId = 110504, // obsolete - available for reuse
	SceneProcessorTypeId = 110505,
	SceneElementProcessorTypeId = 110506,
	AttributeCacheTypeId = 110507,
	PrimitiveVariableProcessorTypeId = 110508,
	DeletePrimitiveVariablesTypeId = 110509,
	GroupTypeId = 110510,
	SceneMixinBaseTypeId = 110511,
	SceneContextProcessorTypeId = 110512,
	SceneTimeWarpTypeId = 110513,
	ObjectSourceTypeId = 110514,
	PlaneTypeId = 110515,
	SeedsTypeId = 110516,
	InstancerTypeId = 110517,
	BranchCreatorTypeId = 110518,
	ObjectToSceneTypeId = 110519,
	CameraTypeId = 110520,
	GlobalsProcessorTypeId = 110521,
	DisplaysTypeId = 110522,
	OptionsTypeId = 110523,
	ShaderTypeId = 110524,
	ShaderAssignmentTypeId = 110525,
	FilterTypeId = 110526,
	PathFilterTypeId = 110527,
	AttributesTypeId = 110528,
	AlembicSourceTypeId = 110529,
	SourceTypeId = 110530,
	SceneContextVariablesTypeId = 110531,
	StandardOptionsTypeId = 110532,
	SubTreeTypeId = 110533,
	OpenGLAttributesTypeId = 110534,
	SceneWriterTypeId = 110535,
	SceneReaderTypeId = 110536,
	PathMatcherDataTypeId = 110537,
	LightTypeId = 110538,
	StandardAttributesTypeId = 110539,
	OpenGLShaderTypeId = 110540,
	TransformTypeId = 110541,
	ConstraintTypeId = 110542,
	AimConstraintTypeId = 110543,
	MeshTypeTypeId = 110544,
	FilteredSceneProcessorTypeId = 110545,
	PruneTypeId = 110546,
	RenderTypeId = 110547,
	ExecutableRenderTypeId = 110548,
	OpenGLRenderTypeId = 110549,
	InteractiveRenderTypeId = 110550,
	CubeTypeId = 110551,
	SphereTypeId = 110552,
	TextTypeId = 110553,
	MapProjectionTypeId = 110554,
	PointConstraintTypeId = 110555,
	CustomAttributesTypeId = 110556,
	CustomOptionsTypeId = 110557,
	MapOffsetTypeId = 110558,
	IsolateTypeId = 110559,
	AttributeProcessorTypeId = 110560,
	DeleteAttributesTypeId = 110561,
	UnionFilterTypeId = 110562,
	SceneSwitchTypeId = 110563,
	ShaderSwitchTypeId = 110564,
	
	LastTypeId = 110650
};

} // namespace GafferScene

#endif // GAFFERSCENE_TYPEIDS_H
