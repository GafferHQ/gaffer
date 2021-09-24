//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Murray Stevenson. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//       copyright notice, this list of conditions and the following
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

#ifndef GAFFERSCENE_CRYPTOMATTE_H
#define GAFFERSCENE_CRYPTOMATTE_H

#include "GafferScene/ScenePlug.h"

#include "GafferImage/FlatImageProcessor.h"

#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"

namespace GafferScene
{

class GAFFERSCENE_API Cryptomatte : public GafferImage::FlatImageProcessor
{

    public:
        Cryptomatte(const std::string &name = defaultName<Cryptomatte>());
        ~Cryptomatte() override;

        IE_CORE_DECLARERUNTIMETYPEDEXTENSION(GafferScene::Cryptomatte, CryptomatteTypeId, GafferImage::FlatImageProcessor);

        enum class ManifestSource
        {
            Metadata = 0,
            Sidecar
        };

        //! @name Plug Accessors
        /// Returns a pointer to the node's plugs.
        //////////////////////////////////////////////////////////////
        //@{
        Gaffer::StringPlug *layerPlug();
        const Gaffer::StringPlug *layerPlug() const;

        Gaffer::IntPlug *manifestSourcePlug();
        const Gaffer::IntPlug *manifestSourcePlug() const;

        Gaffer::StringPlug *manifestPathPlug();
        const Gaffer::StringPlug *manifestPathPlug() const;

        Gaffer::StringVectorDataPlug *matteNamesPlug();
        const Gaffer::StringVectorDataPlug *matteNamesPlug() const;

        Gaffer::StringPlug *outputChannelPlug();
        const Gaffer::StringPlug *outputChannelPlug() const;
        //@}

        void affects(const Gaffer::Plug *input, AffectedPlugsContainer &outputs) const override;

    protected:
        void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
        void compute(Gaffer::ValuePlug *output, const Gaffer::Context *context) const override;
        Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;

        void hashChannelNames(const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h) const override;
        IECore::ConstStringVectorDataPtr computeChannelNames(const Gaffer::Context *context, const GafferImage::ImagePlug *parent) const override;

        void hashChannelData(const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h) const override;
        IECore::ConstFloatVectorDataPtr computeChannelData(const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const GafferImage::ImagePlug *parent) const override;

    private:
        Gaffer::FloatVectorDataPlug *matteValuesPlug();
        const Gaffer::FloatVectorDataPlug *matteValuesPlug() const;

        Gaffer::AtomicCompoundDataPlug *manifestPlug();
        const Gaffer::AtomicCompoundDataPlug *manifestPlug() const;

        Gaffer::PathMatcherDataPlug *manifestPathDataPlug();
        const Gaffer::PathMatcherDataPlug *manifestPathDataPlug() const;

        GafferScene::ScenePlug *manifestScenePlug();
        const GafferScene::ScenePlug *manifestScenePlug() const;

        Gaffer::FloatVectorDataPlug *matteChannelDataPlug();
        const Gaffer::FloatVectorDataPlug *matteChannelDataPlug() const;

        static size_t g_firstPlugIndex;
};

IE_CORE_DECLAREPTR(Cryptomatte);

} // namespace GafferScene

#endif // GAFFERSCENE_CRYPTOMATTE_H