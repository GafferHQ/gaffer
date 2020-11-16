//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/TransformPlug.h"

#include "IECore/AngleConversion.h"

using namespace Imath;
using namespace Gaffer;

GAFFER_PLUG_DEFINE_TYPE( TransformPlug );

size_t TransformPlug::g_firstPlugIndex = 0;

TransformPlug::TransformPlug(
	const std::string &name, Direction direction,
	const V3f &defaultTranslate,
	const V3f &defaultRotate,
	const V3f &defaultScale,
	const V3f &defaultPivot,
	unsigned flags
)
	:	ValuePlug( name, direction, flags )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild(
		new V3fPlug(
			"translate",
			direction,
			defaultTranslate,
			V3f( limits<float>::min() ),
			V3f( limits<float>::max() ),
			flags
		)
	);

	addChild(
		new V3fPlug(
			"rotate",
			direction,
			defaultRotate,
			V3f( limits<float>::min() ),
			V3f( limits<float>::max() ),
			flags
		)
	);

	addChild(
		new V3fPlug(
			"scale",
			direction,
			defaultScale,
			V3f( limits<float>::min() ),
			V3f( limits<float>::max() ),
			flags
		)
	);

	addChild(
		new V3fPlug(
			"pivot",
			direction,
			defaultPivot,
			V3f( limits<float>::min() ),
			V3f( limits<float>::max() ),
			flags
		)
	);
}

TransformPlug::~TransformPlug()
{
}

bool TransformPlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	return children().size() != 4;
}

PlugPtr TransformPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new TransformPlug(
		name, direction,
		translatePlug()->defaultValue(),
		rotatePlug()->defaultValue(),
		scalePlug()->defaultValue(),
		pivotPlug()->defaultValue(),
		getFlags()
	);
}

V3fPlug *TransformPlug::translatePlug()
{
	return getChild<V3fPlug>( g_firstPlugIndex );
}

const V3fPlug *TransformPlug::translatePlug() const
{
	return getChild<V3fPlug>( g_firstPlugIndex );
}

V3fPlug *TransformPlug::rotatePlug()
{
	return getChild<V3fPlug>( g_firstPlugIndex + 1 );
}

const V3fPlug *TransformPlug::rotatePlug() const
{
	return getChild<V3fPlug>( g_firstPlugIndex + 1 );
}

V3fPlug *TransformPlug::scalePlug()
{
	return getChild<V3fPlug>( g_firstPlugIndex + 2 );
}

const V3fPlug *TransformPlug::scalePlug() const
{
	return getChild<V3fPlug>( g_firstPlugIndex + 2 );
}

V3fPlug *TransformPlug::pivotPlug()
{
	return getChild<V3fPlug>( g_firstPlugIndex + 3 );
}

const V3fPlug *TransformPlug::pivotPlug() const
{
	return getChild<V3fPlug>( g_firstPlugIndex + 3 );
}

Imath::M44f TransformPlug::matrix() const
{
	const V3f pivot = pivotPlug()->getValue();
	M44f result;
	result.translate( pivot + translatePlug()->getValue() );
	result.rotate( IECore::degreesToRadians( rotatePlug()->getValue() ) );
	result.scale( scalePlug()->getValue() );
	result.translate( -pivot );
	return result;
}
