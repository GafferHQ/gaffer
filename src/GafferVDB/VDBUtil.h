//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
//      * Neither the name of Image Engine Design Inc nor the names of
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

#ifndef GAFFERVDB_VDBUTIL_H
#define GAFFERVDB_VDBUTIL_H

#include "openvdb/openvdb.h"
#include "OpenEXR/ImathBox.h"

namespace GafferVDB
{
//! Calculate the worldspace bounds for a grid
//! padding a full voxel, not just the centers, and add generous buffer of 5% of voxel size
template<typename T>
Imath::Box<Imath::Vec3<T> > getBounds( openvdb::GridBase::ConstPtr grid, float padding = 0.55f )
{
	openvdb::Vec3i min = grid->metaValue<openvdb::Vec3i>( grid->META_FILE_BBOX_MIN );
	openvdb::Vec3i max = grid->metaValue<openvdb::Vec3i>( grid->META_FILE_BBOX_MAX );

	openvdb::Vec3d offset = openvdb::Vec3d( padding );
	openvdb::BBoxd indexBounds = openvdb::BBoxd( min - offset, max + offset );
	openvdb::BBoxd worldBounds = grid->transform().indexToWorld( indexBounds );
	openvdb::Vec3d minBB = worldBounds.min();
	openvdb::Vec3d maxBB = worldBounds.max();

	return Imath::Box<Imath::Vec3<T> >( Imath::Vec3<T>( minBB[0], minBB[1], minBB[2] ), Imath::Vec3<T>( maxBB[0], maxBB[1], maxBB[2] ) );

}

}

#endif // GAFFERVDB_VDBUTIL_H