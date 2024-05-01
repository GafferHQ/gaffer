import Gaffer
import GafferCycles

sections = {
    "principled_bsdf" : {
        "subsurface_method" : "Subsurface",
        "subsurface_weight" : "Subsurface",
        "subsurface_radius" : "Subsurface",
        "subsurface_scale" : "Subsurface",
        "subsurface_anisotropy" : "Subsurface",
        "subsurface_ior" : "Subsurface",
        "distribution" : "Specular",
        "specular_ior_level" : "Specular",
        "specular_tint" : "Specular",
        "anisotropic" : "Specular",
        "anisotropic_rotation" : "Specular",
        "tangent" : "Specular",
        "transmission_weight" : "Transmission",
        "coat_weight" : "Coat",
        "coat_roughness" : "Coat",
        "coat_ior" : "Coat",
        "coat_tint" : "Coat",
        "coat_normal" : "Coat",
        "sheen_weight" : "Sheen",
        "sheen_roughness" : "Sheen",
        "sheen_tint" : "Sheen",
        "emission_color" : "Emission",
        "emission_strength" : "Emission",
    },
    "principled_hair_bsdf" : {
        "color" : "Direct Coloring",
        "absorption_coefficient" : "Absorption Coefficient",
        "melanin" : "Melanin Concentration",
        "melanin_redness" : "Melanin Concentration",
        "tint" : "Melanin Concentration",
        "roughness" : "General", 
        "radial_roughness" : "General", 
        "coat" : "General",
        "ior" : "General",
        "offset" : "General",
        "random_color" : "General",
        "random_roughness" : "General",
        "random" : "General",
        "aspect_ratio" : "General",
        "R" : "General",
        "TT" : "General",
        "TRT" : "General",
    },
}

names = {
    "principled_bsdf" : {
        "base_color" : "Base Color",
        "ior" : "IOR",
        "subsurface_method" : "Method",
        "subsurface_weight" : "Weight",
        "subsurface_radius" : "Radius",
        "subsurface_scale" : "Scale",
        "subsurface_ior" : "IOR",
        "subsurface_anisotropy" : "Anisotropy",
        "specular_ior_level" : "IOR Level",
        "specular_tint" : "Tint",
        "specular_tint" : "Tint",
        "anisotropic_rotation" : "Anisotropic Rotation",
        "transmission_weight" : "Weight",
        "coat_weight" : "Weight",
        "coat_roughness" : "Roughness",
        "coat_ior" : "IOR",
        "coat_tint" : "Tint",
        "coat_normal" : "Normal",
        "sheen_weight" : "Weight",
        "sheen_roughness" : "Roughness",
        "sheen_tint" : "Tint",
        "emission_color" : "Color",
        "emission_strength" : "Strength",
    },
    "principled_hair_bsdf" : {
        "absorption_coefficient" : "Absorption Coefficient",
        "melanin_redness" : "Melanin Redness",
        "radial_roughness" : "Radial Roughness",
        "ior" : "IOR",
        "random_roughness" : "Random Roughness",
        "random_color" : "Random Color",
        "aspect_ratio" : "Aspect Ratio",
    },
    "principled_volume" : {
        "color_attribute" : "Color Attribute",
        "density_attribute" : "Density Attribute",
        "temperature_attribute" : "Temperature Attribute",
        "absorption_color" : "Absorption Color",
        "blackbody_intensity" : "Blackbody Intensity",
        "blackbody_tint" : "Blackbody Tint",
        "emission_color" : "Emission Color",
        "emission_strength" : "Emission Strength",
    },
    "vector_map_range" : {
        "range_type" : "Interpolation Type",
        "from_min" : "From Min",
        "from_max" : "From Max",
        "to_min" : "To Min",
        "to_max" : "To Max",
        "steps" : "Steps",
        "use_clamp" : "Clamp",
    },
    "map_range" : {
        "range_type" : "Interpolation Type",
        "from_min" : "From Min",
        "from_max" : "From Max",
        "to_min" : "To Min",
        "to_max" : "To Max",
        "steps" : "Steps",
        "use_clamp" : "Clamp",
    },
    "mix" : {
        "mix_type" : "Blending Mode",
        "use_clamp" : "Clamp",
        "color1" : "A",
        "color2" : "B",
    },
    "mix_color" : {
        "blend_type" : "Blending Mode",
        "use_clamp_result" : "Clamp Result",
        "use_clamp" : "Clamp Factor",
    },
    "float_curve" : {
        "min_x" : "Min X",
        "max_x" : "Max X",
    },
    "rgb_curves" : {
        "min_x" : "Min X",
        "max_x" : "Max X",
    },
    "vector_curves" : {
        "min_x" : "Min X",
        "max_x" : "Max X",
    },
    "vector_transform" : {
        "transform_type" : "Type",
        "convert_from" : "Convert From",
        "convert_to" : "Convert To",
    },
    "mapping" : {
        "mapping_type" : "Type",
    },
    "vector_rotate" : {
        "rotate_type" : "Type",
    },
    "clamp" : {
        "clamp_type" : "Clamp Type",
    },
    "mix_float" : {
        "use_clamp" : "Clamp",
    },
    "mix_vector" : {
        "use_clamp" : "Clamp",
    },
    "mix_vector_non_uniform" : {
        "use_clamp" : "Clamp",
    },
    "brightness_contrast" : {
        "bright" : "Brightness",
    },
    "normal" : {
        "direction" : "Direction",
    },
    "bump" : {
        "use_object_space" : "Use Object Space",
        "sample_center" : "Sample Center",
        "sample_x" : "Sample X",
        "sample_y" : "Sample Y",
    },
    "vertex_color" : {
        "layer_name" : "Layer Name",
    },
    "vector_math" : {
        "math_type" : "Operation",
    },
    "texture_coordinate" : {
        "from_dupli" : "From Dupli",
        "use_transform" : "Use Transform",
        "ob_tfm" : "Object Transform",
    },
    "ambient_occlusion" : {
        "only_local" : "Only Local",
    },
    "uvmap" : {
        "from_dupli" : "From Dupli",
    },
    "wireframe" : {
        "use_pixel_size" : "Use Pixel Size",
    },
    "tangent" : {
        "direction_type" : "Direction",
    },
    "point_density_texture" : {
        "tfm" : "Transform",
    },
    "image_texture" : {
        "alpha_type" : "Alpha Type",
        "projection_blend" : "Projection Blend",
    },
    "environment_texture" : {
        "alpha_type" : "Alpha Type",
    },
    "sky_texture" : {
        "sky_type" : "Type",
        "sun_direction" : "Sun Direction",
        "sun_disc" : "Sun Disc",
        "sun_size" : "Sun Size",
        "sun_intensity" : "Sun Intensity",
        "sun_elevation" : "Sun Elevation",
        "sun_rotation" : "Sun Rotation",
        "ground_albedo" : "Ground Albedo",
        "air_density" : "Air",
        "dust_density" : "Dust",
        "ozone_density" : "Ozone",
    },
    "noise_texture" : {
        "use_normalize" : "Normalize",
    },
    "gradient_texture" : {
        "gradient_type" : "Gradient Type",
    },
    "voronoi_texture" : {
        "use_normalize" : "Normalize",
    },
    "ies_light" : {
        "ies" : "IES",
    },
    "musgrave_texture" : {
        "musgrave_type" : "Musgrave Type",
    },
    "wave_texture" : {
        "wave_type" : "Wave Type",
        "bands_direction" : "Bands Direction",
        "rings_direction" : "Rings Direction",
        "detail_scale" : "Detail Scale",
        "detail_roughness" : "Detail Roughness",
    },
    "brick_texture" : {
        "offset_frequency" : "Offset Frequency",
        "squash_frequency" : "Squash Frequency",
        "mortar_size" : "Mortar Size",
        "mortar_smooth" : "Mortar Smooth",
        "brick_width" : "Brick Width",
        "row_height" : "Row Height",
    },
    "hair_bsdf" : {
        "roughness_u" : "Roughness U",
        "roughness_v" : "Roughness V",
    },
    "subsurface_scattering" : {
        "subsurface_ior" : "IOR",
        "subsurface_anisotropy" : "Anisotropy",
    },
    "math" : {
        "use_clamp" : "Clamp",
        "math_type" : "Operation",
    },
    "rgb_ramp" : {
        "ramp_alpha" : "Ramp Alpha",
    },
}

indexes = {
    "principled_bsdf" : {
        "base_color" : 1, 
        "metallic" : 2, 
        "roughness" : 3,
        "ior" : 4, 
        "alpha" : 5, 
        "normal" : 6, 
        "subsurface_method" : 7, 
        "subsurface_weight" : 8, 
        "subsurface_radius" : 9, 
        "subsurface_scale" : 10, 
        "subsurface_anisotropy" : 11, 
        "distribution" : 12, 
        "specular_ior_level" : 13, 
        "specular_tint" : 14, 
        "anisotropic" : 15, 
        "anisotropic_rotation" : 16, 
        "tangent" : 17, 
        "transmission_weight" : 18, 
        "coat_weight" : 19, 
        "coat_roughness" : 20, 
        "coat_ior" : 21, 
        "coat_tint" : 22, 
        "coat_normal" : 23, 
        "sheen_weight" : 24, 
        "sheen_roughness" : 25, 
        "sheen_tint" : 26, 
        "emission_color" : 27,
        "emission_strength" : 28,
        
    },
    "principled_volume" : {
        "color" : 1,
        "color_attribute" : 2,
        "density" : 3,
        "density_attribute" : 4,
        "anisotropy" : 5,
        "absorption_color" : 6,
        "emission_strength" : 7,
        "emission_color" : 8,
        "blackbody_intensity" : 9,
        "blackbody_tint" : 10,
        "temperature" : 11,
        "temperature_attribute" : 12,
    },
    "principled_hair_bsdf" : {
        "color" : 1,
        "absorption_coefficient" : 2,
        "melanin" : 3,
        "melanin_redness" : 4,
        "tint" : 5,
        "roughness" : 6,
        "radial_roughness" : 7,
        "coat" : 8,
        "ior" : 9,
        "offset" : 10,
        "random_roughness" : 11,
        "random_color" : 12,
        "random" : 13,
        "R" : 14,
        "TT" : 15,
        "TRT" : 16,
        "aspect_ratio" : 17,
    },
    "bump" : {
        "invert" : 9,
        "strength" : 1,
        "distance" : 2,
        "height" : 3,
        "normal" : 4,
        "sample_center" : 5,
        "sample_x" : 6,
        "sample_y" : 7,
        "use_object_space" : 9,
    },
    "ambient_occlusion" : {
        "samples" : 1,
        "inside" : 2,
        "only_local" : 3,
        "color" : 4,
        "distance" : 5,
        "normal" : 6,
    },
    "glass_bsdf" : {
        "distribution" : 1,
        "color" : 2,
        "roughness" : 3,
        "ior" : 4,
        "normal" : 5,
    },
    "hair_bsdf" : {
        "component" : 1,
        "color" : 2,
        "roughness_u" : 3,
        "roughness_v" : 4,
        "offset" : 5,
        "tangent" : 6,
    },
    "toon_bsdf" : {
        "component" : 1,
        "color" : 2,
        "size" : 3,
        "smooth" : 4,
        "normal" : 5,
    },
    "glossy_bsdf" : {
        "distribution" : 1,
        "color" : 2,
        "roughness" : 3,
        "anisotropy" : 4,
        "rotation" : 5,
        "tangent" : 6,
        "normal" : 7,
    },
    "refraction_bsdf" : {
        "distribution" : 1,
        "color" : 2,
        "roughness" : 3,
        "ior" : 4,
        "normal" : 5,
    },
    "sheen_bsdf" : {
        "distribution" : 1,
        "color" : 2,
        "roughness" : 3,
        "normal" : 4,
    },
    "diffuse_bsdf" : {
        "color" : 1,
        "roughness" : 2,
        "normal" : 3,
    },
    "mix" : {
        "mix_type" : 1,
        "factor" : 2,
        "color1" : 3,
        "color2" : 4,
        "use_clamp" : 5,
    },
    "subsurface_scattering" : {
        "method" : 1,
        "color" : 2,
        "radius" : 3,
        "scale" : 4,
        "subsurface_ior" : 5,
        "subsurface_anisotropy" : 6,
        "normal" : 7,
    },
    "math" : {
        "math_type" : 1,
        "value1" : 2,
        "value2" : 3,
        "value3" : 4,
        "use_clamp" : 5,
    },

}

defaults = {
    "principled_bsdf" : {
        #"subsurface_radius.x" : 1, why doesn't this work?
        #"subsurface_radius.y" : .2,
        #"subsurface_radius.z" : .1,
        "subsurface_scale" : .05,
        "specular_ior_level" : .5,
    },
    "principled_volume" : {
        "density_attribute" : "density",
        "temperature_attribute" : "temperature",
    },
    "principled_hair_bsdf" : {
        "model" : "Chiang"
    },
}

def section( plug ) :

    global sections
    
    shaderName = plug.node()["name"].getValue()
    shaderDict = sections.get( shaderName )
    if shaderDict is None :
        return None
        
    return shaderDict.get( plug.getName() )

def name( plug ) :

    global names
    
    shaderName = plug.node()["name"].getValue()
    shaderDict = names.get( shaderName )
    if shaderDict is None :
        return None
        
    return shaderDict.get( plug.getName() )

def index( plug ) :

    global indexes
    
    shaderName = plug.node()["name"].getValue()
    shaderDict = indexes.get( shaderName )
    if shaderDict is None :
        return None
        
    return shaderDict.get( plug.getName() )

def default( plug ) :

    global defaults
    
    shaderName = plug.node()["name"].getValue()
    shaderDict = defaults.get( shaderName )
    if shaderDict is None :
        return None
        
    return shaderDict.get( plug.getName() )

### CyclesShader ###

### sections ###
        
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.*", "layout:section", section )

Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__translation", "layout:section", "Texture Mapping" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__rotation", "layout:section", "Texture Mapping" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__scale", "layout:section", "Texture Mapping" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__min", "layout:section", "Texture Mapping" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__max", "layout:section", "Texture Mapping" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__use_minmax", "layout:section", "Texture Mapping" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__x_mapping", "layout:section", "Texture Mapping" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__y_mapping", "layout:section", "Texture Mapping" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__z_mapping", "layout:section", "Texture Mapping" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__type", "layout:section", "Texture Mapping" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__projection", "layout:section", "Texture Mapping" )

### indexes ###

Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.*", "layout:index", index )

### labels ###

Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.*", "label", name )

Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.fac", "label", "Factor" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.color_type", "label", "Color Type" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.value_float", "label", "Float Value" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.value_color", "label", "Color Value" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.value_closure", "label", "Closure Value" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.value_int", "label", "Integer Value" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.value_normal", "label", "Normal Value" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.value_vector", "label", "Vector Value" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.value_point", "label", "Point Value" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.value_string", "label", "String Value" )

Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__translation", "label", "Translation" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__rotation", "label", "Rotation" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__scale", "label", "Scale" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__min", "label", "Min" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__max", "label", "Max" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__use_minmax", "label", "Use Min Max" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__x_mapping", "label", "X Mapping" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__y_mapping", "label", "Y Mapping" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__z_mapping", "label", "Z Mapping" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__type", "label", "Type" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__projection", "label", "Projection" )

### defaults ###

Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.*", "userDefault", default )

Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.subsurface_radius.x", "userDefault", 1 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.subsurface_radius.y", "userDefault", .2 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.subsurface_radius.z", "userDefault", .1 )

### hide dupli ###

Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.from_dupli", "plugValueWidget:type", "" )

### CyclesLight ###

### indexes ###

Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "name", "layout:index", 1 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "sets", "layout:index", 2 )

Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.color", "layout:index", 3 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.intensity", "layout:index", 4 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.exposure", "layout:index", 5 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.normalize", "layout:index", 6 )

Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.size", "layout:index", 7 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.spot_angle", "layout:index", 8 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.spot_smooth", "layout:index", 9 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.angle", "layout:index", 8 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.width", "layout:index", 8 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.height", "layout:index", 9 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.spread", "layout:index", 10 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.map_resolution", "layout:index", 7 )

Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.lightgroup", "layout:index", 11 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.max_bounces", "layout:index", 12 )

Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.cast_shadow", "layout:index", 13 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_mis", "layout:index", 14 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_camera", "layout:index", 15 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_diffuse", "layout:index", 16 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_glossy", "layout:index", 17 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_transmission", "layout:index", 18 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_scatter", "layout:index", 19 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_caustics", "layout:index", 20 )

### sections ###

Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.cast_shadow", "layout:section", "Contribution" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_mis", "layout:section", "Contribution" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_camera", "layout:section", "Contribution" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_diffuse", "layout:section", "Contribution" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_glossy", "layout:section", "Contribution" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_transmission", "layout:section", "Contribution" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_scatter", "layout:section", "Contribution" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_caustics", "layout:section", "Contribution" )

### labels ###

Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_mis", "label", "Use MIS" )
