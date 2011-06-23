//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_TYPEIDS_H
#define GAFFER_TYPEIDS_H

namespace Gaffer
{

enum TypeId
{

	GraphComponentTypeId = 400000,
	NodeTypeId = 400001,
	PlugTypeId = 400002,
	ValuePlugTypeId = 400003,
	FloatPlugTypeId = 400004,
	IntPlugTypeId = 400005,
	StringPlugTypeId = 400006,
	ScriptNodeTypeId = 400007,
	ApplicationRootTypeId = 400008,
	ScriptContainerTypeId = 400009,
	SetTypeId = 400010,
	ObjectPlugTypeId = 400011,
	CompoundPlugTypeId = 400012,
	V2fPlugTypeId = 400013,
	V3fPlugTypeId = 400014,
	V2iPlugTypeId = 400015,
	V3iPlugTypeId = 400016,
	Color3fPlugTypeId = 400017,
	Color4fPlugTypeId = 400018,
	SplineffPlugTypeId = 400019,
	SplinefColor3fPlugTypeId = 400020,
	M33fPlugTypeId = 400021,
	M44fPlugTypeId = 400022,
	BoolPlugTypeId = 400023,
	ParameterisedHolderNodeTypeId = 400024,
	IntVectorDataPlugTypeId = 400025,
	FloatVectorDataPlugTypeId = 400026,
	StringVectorDataPlugTypeId = 400027,
	V3fVectorDataPlugTypeId = 400028,
	StandardSetTypeId = 400029,
	
	FirstPythonTypeId = 405000,
	
	LastTypeId = 409999
	
};

} // namespace Gaffer

#endif // GAFFER_TYPEIDS_H
