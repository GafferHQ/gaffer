import Gaffer
import GafferCycles
import imath
import functools

parameterMetadata = {
    "principled_bsdf" : {
        "base_color" : {
            "label" : "Base Color",
            "layout:index" : 1,
        },
        "metallic" : {
            "layout:index" : 2,
        },
        "roughness" : {
            "layout:index" : 3,
        },
        "ior" : {
            "label" : "IOR",
            "layout:index" : 4,
        },
        "alpha" : {
            "layout:index" : 5,
        },
        "normal" : {
            "layout:index" : 6,
        },
        "subsurface_method" : {
            "layout:section" : "Subsurface",
            "label" : "Method",
            "layout:index" : 7,
        },
        "subsurface_weight" : {
            "layout:section" : "Subsurface",
            "label" : "Weight",
            "layout:index" : 8,
        },
        "subsurface_radius" : {
            "layout:section" : "Subsurface",
            "label" : "Radius",
            "layout:index" : 9,
            "userDefault" : imath.Color3f( 1, .2, .1 ),
        },
        "subsurface_scale" : {
            "layout:section" : "Subsurface",
            "label" : "Scale",
            "layout:index" : 10,
        },
        "subsurface_anisotropy" : {
            "layout:section" : "Subsurface",
            "label" : "Anisotropy",
            "layout:index" : 11,
        },
        "subsurface_ior" : {
            "layout:section" : "Subsurface",
            "label" : "IOR",
            "layout:index" : 12,
        },
        "distribution" : {
            "layout:section" : "Specular",
            "label" : "Distribution",
            "layout:index" : 13,
        },
        "specular_ior_level" : {
            "layout:section" : "Specular",
            "label" : "IOR Level",
            "layout:index" : 14,
            "userDefault" : 0.5,
        },
        "specular_tint" : {
            "layout:section" : "Specular",
            "label" : "Tint",
            "layout:index" : 15,
        },
        "anisotropic" : {
            "layout:section" : "Specular",
            "label" : "Anisotropic",
            "layout:index" : 16,
        },
        "anisotropic_rotation" : {
            "layout:section" : "Specular",
            "label" : "Anisotropic Rotation",
            "layout:index" : 17,
        },
        "tangent" : {
            "layout:section" : "Specular",
            "label" : "Tangent",
            "layout:index" : 18,
        },
        "transmission_weight" : {
            "layout:section" : "Transmission",
            "label" : "Weight",
            "layout:index" : 19,
        },
        "coat_weight" : {
            "layout:section" : "Coat",
            "label" : "Weight",
            "layout:index" : 20,
        },
        "coat_roughness" : {
            "layout:section" : "Coat",
            "label" : "Roughness",
            "layout:index" : 21,
        },
        "coat_ior" : {
            "layout:section" : "Coat",
            "label" : "IOR",
            "layout:index" : 22,
        },
        "coat_tint" : {
            "layout:section" : "Coat",
            "label" : "Tint",
            "layout:index" : 23,
        },
        "coat_normal" : {
            "layout:section" : "Coat",
            "label" : "Normal",
            "layout:index" : 24,
        },
        "sheen_weight" : {
            "layout:section" : "Sheen",
            "label" : "Weight",
            "layout:index" : 25,
        },
        "sheen_roughness" : {
            "layout:section" : "Sheen",
            "label" : "Roughness",
            "layout:index" : 26,
        },
        "sheen_tint" : {
            "layout:section" : "Sheen",
            "label" : "Tint",
            "layout:index" : 27,
        },
        "emission_color" : {
            "layout:section" : "Emission",
            "label" : "Color",
            "layout:index" : 28,
        },
        "emission_strength" : {
            "layout:section" : "Emission",
            "label" : "Strength",
            "layout:index" : 29,
        },
    },
    "principled_hair_bsdf" : {
        "model" : {
            "userDefault" : "Chiang",
        },
        "color" : {
            "layout:index" : 1,
        },
        "absorption_coefficient" : {
            "label" : "Absorption Coefficient",
            "layout:index" : 2,
        },
        "melanin" : {
            "layout:index" : 3,
        },
        "melanin_redness" : {
            "label" : "Melanin Redness",
            "layout:index" : 4,
        },
        "tint" : {
            "layout:index" : 5,
        },
        "roughness" : {
            "layout:index" : 6,
        },
        "radial_roughness" : {
            "label" : "Radial Roughness",
            "layout:index" : 7,
        },
        "coat" : {
            "layout:index" : 8,
        },
        "ior" : {
            "label" : "IOR",
            "layout:index" : 9,
        },
        "offset" : {
            "layout:index" : 10,
        },
        "random_color" : {
            "label" : "Random Color",
            "layout:index" : 11,
        },
        "random_roughness" : {
            "label" : "Random Roughness",
            "layout:index" : 12,
        },
        "random" : {
            "layout:index" : 13,
        },
        "R" : {
            "layout:index" : 14,
        },
        "TT" : {
            "layout:index" : 15,
        },
        "TRT" : {
            "layout:index" : 16,
        },
        "aspect_ratio" : {
            "label" : "Aspect Ratio",
            "layout:index" : 17,
        },
    },
    "principled_volume" : {
         "color" : {
            "layout:index" : 1,
        },
        "color_attribute" : {
            "label" : "Color Attribute",
            "layout:index" : 2,
        },
        "density" : {
            "layout:index" : 3,
        },
        "density_attribute" : {
            "label" : "Density Attribute",
            "layout:index" : 4,
            "userDefault" : "density",
        },
        "anisotropy" : {
            "layout:index" : 5,
        },
        "absorption_color" : {
            "label" : "Absorption Color",
            "layout:index" : 6,
        },
        "emission_strength" : {
            "label" : "Emission Strength",
            "layout:index" : 7,
        },
        "emission_color" : {
            "label" : "Emission Color",
            "layout:index" : 8,
        },
        "blackbody_intensity" : {
            "label" : "Blackbody Intensity",
            "layout:index" : 9,
        },
        "blackbody_tint" : {
            "label" : "Blackbody Tint",
            "layout:index" : 10,
        },
        "temperature" : {
            "layout:index" : 11,
        },
        "temperature_attribute" : {
            "label" : "Temperature Attribute",
            "layout:index" : 12,
            "userDefault" : "temperature",
        },
    },
    "vector_map_range" : {
        "range_type" : {
            "label" : "Interpolation Type",
        },
        "from_min" : {
            "label" : "From Min",
        },
        "from_max" : {
            "label" : "From Max",
        },
        "to_min" : {
            "label" : "To Min",
        },
        "to_max" : {
            "label" : "To Max",
        },
        "steps" : {
            "label" : "Steps",
        },
        "use_clamp" : {
            "label" : "Clamp",
        },
    },
    "map_range" : {
        "range_type" : {
            "label" : "Interpolation Type",
        },
        "from_min" : {
            "label" : "From Min",
        },
        "from_max" : {
            "label" : "From Max",
        },
        "to_min" : {
            "label" : "To Min",
        },
        "to_max" : {
            "label" : "To Max",
        },
        "steps" : {
            "label" : "Steps",
        },
        "use_clamp" : {
            "label" : "Clamp",
        },
    },
    "mix" : {
        "mix_type" : {
            "label" : "Blending Mode",
            "layout:index" : 1,
        },
        "factor" : {
            "layout:index" : 2,
        },
        "color1" : {
            "label" : "A",
            "layout:index" : 3,
        },
        "color2" : {
            "label" : "B",
            "layout:index" : 4,
        },
        "use_clamp" : {
            "label" : "Clamp",
            "layout:index" : 5,
        },
    },
    "mix_color" : {
        "blend_type" : {
            "label" : "Blending Mode",
        },
        "use_clamp_result" : {
            "label" : "Clamp Result",
        },
        "use_clamp" : {
            "label" : "Clamp Factor",
        },
    },
    "float_curve" : {
        "min_x" : {
            "label" : "Min X",
        },
        "max_x" : {
            "label" : "Max X",
        },
    },
    "rgb_curves" : {
        "min_x" : {
            "label" : "Min X",
        },
        "max_x" : {
            "label" : "Max X",
        },
    },
    "vector_curves" : {
        "min_x" : {
            "label" : "Min X",
        },
        "max_x" : {
            "label" : "Max X",
        },
    },
    "vector_transform" : {
        "transform_type" : {
            "label" : "Type",
        },
        "convert_from" : {
            "label" : "Convert From",
        },
        "convert_to" : {
            "label" : "MConvert To",
        },
    },
    "mapping" : {
        "mapping_type" : {
            "label" : "Type",
        },
    },
    "vector_rotate" : {
        "rotate_type" : {
            "label" : "Type",
        },
        "rotation" : {
            "layout:index" : 5,
        },
    },
    "clamp" : {
        "clamp_type" : {
            "label" : "Clamp Type",
        },
    },
    "mix_float" : {
        "use_clamp" : {
            "label" : "Clamp",
        },
    },
    "mix_vector" : {
        "use_clamp" : {
            "label" : "Clamp",
        },
    },
    "mix_vector_non_uniform" : {
        "use_clamp" : {
            "label" : "Clamp",
        },
    },
    "brightness_contrast" : {
        "bright" : {
            "label" : "Brightness",
        },
    },
    "normal" : {
        "direction" : {
            "label" : "Direction",
        },
    },
    "bump" : {
        "strength" : {
            "layout:index" : 1,
        },
        "distance" : {
            "layout:index" : 2,
        },
        "height" : {
            "layout:index" : 3,
        },
        "normal" : {
            "layout:index" : 4,
        },
        "sample_center" : {
            "label" : "Sample Center",
            "layout:index" : 5,
        },
        "sample_x" : {
            "label" : "Sample X",
            "layout:index" : 6,
        },
        "sample_y" : {
            "label" : "Sample Y",
            "layout:index" : 7,
        },
        "invert" : {
            "layout:index" : 8,
        },
        "use_object_space" : {
            "label" : "Use Object Space",
            "layout:index" : 9,
        },
    },
    "vertex_color" : {
        "layer_name" : {
            "label" : "Layer Name",
        },
    },
    "vector_math" : {
        "math_type" : {
            "label" : "Operation",
        },
    },
    "texture_coordinate" : {
        "from_dupli" : {
            "label" : "From Dupli",
        },
        "use_transform" : {
            "label" : "Use Transform",
        },
        "ob_tfm" : {
            "label" : "Object Transform",
        },
    },
    "ambient_occlusion" : {
        "samples" : {
            "layout:index" : 1,
        },
        "inside" : {
            "layout:index" : 2,
        },
        "only_local" : {
            "label" : "Only Local",
            "layout:index" : 3,
        },
        "color" : {
            "layout:index" : 4,
        },
        "distance" : {
            "layout:index" : 5,
        },
        "normal" : {
            "layout:index" : 6,
        },
    },
    "uvmap" : {
        "from_dupli" : {
            "label" : "From Dupli",
        },
    },
    "wireframe" : {
        "use_pixel_size" : {
            "label" : "Use Pixel Size",
        },
    },
    "tangent" : {
        "direction_type" : {
            "label" : "Direction",
        },
    },
    "point_density_texture" : {
        "tfm" : {
            "label" : "Transform",
        },
    },
    "image_texture" : {
        "alpha_type" : {
            "label" : "Alpha Type",
        },
        "projection_blend" : {
            "label" : "Projection Blend",
        },
    },
    "environment_texture" : {
        "alpha_type" : {
            "label" : "Alpha Type",
        },
    },
    "sky_texture" : {
        "sky_type" : {
            "label" : "Type",
        },
        "sun_direction" : {
            "label" : "Sun Direction",
        },
        "sun_disc" : {
            "label" : "Sun Disc",
        },
        "sun_size" : {
            "label" : "Sun Size",
        },
        "sun_intensity" : {
            "label" : "Sun Intensity",
        },
        "sun_elevation" : {
            "label" : "Sun Elevation",
        },
        "sun_rotation" : {
            "label" : "Sun Rotation",
        },
        "ground_albedo" : {
            "label" : "Ground Albedo",
        },
        "air_density" : {
            "label" : "Air",
        },
        "dust_density" : {
            "label" : "Dust",
        },
        "ozone_density" : {
            "label" : "Ozone",
        },
    },
    "noise_texture" : {
        "use_normalize" : {
            "label" : "Normalize",
        },
    },
    "gradient_texture" : {
        "gradient_type" : {
            "label" : "Gradient Type",
        },
    },
    "voronoi_texture" : {
        "use_normalize" : {
            "label" : "Normalize",
        },
    },
    "ies_light" : {
        "ies" : {
            "label" : "IES",
        },
    },
    "musgrave_texture" : {
        "musgrave_type" : {
            "label" : "Musgrave Type",
        },
    },
    "wave_texture" : {
        "wave_type" : {
            "label" : "Wave Type",
        },
        "bands_direction" : {
            "label" : "Bands Direction",
        },
        "rings_direction" : {
            "label" : "Rings Direction",
        },
        "detail_scale" : {
            "label" : "Detail Scale",
        },
        "detail_roughness" : {
            "label" : "Detail Roughness",
        },
    },
    "brick_texture" : {
        "offset_frequency" : {
            "label" : "Offset Frequency",
        },
        "squash_frequency" : {
            "label" : "Squash Frequency",
        },
        "mortar_size" : {
            "label" : "Mortar Size",
        },
        "mortar_smooth" : {
            "label" : "Mortar Smooth",
        },
        "brick_width" : {
            "label" : "Brick Width",
        },
        "brick_height" : {
            "label" : "Row Width",
        },
    },
    "hair_bsdf" : {
        "component" : {
            "layout:index" : 1,
        },
        "color" : {
            "layout:index" : 2,
        },
        "roughness_u" : {
            "label" : "Roughness U",
            "layout:index" : 3,
        },
        "roughness_v" : {
            "label" : "Roughness V",
            "layout:index" : 4,
        },
        "offset" : {
            "layout:index" : 5,
        },
        "tangent" : {
            "layout:index" : 6,
        },
    },
    "subsurface_scattering" : {
        "method" : {
            "layout:index" : 1,
        },
        "color" : {
            "layout:index" : 2,
        },
        "radius" : {
            "layout:index" : 3,
        },
        "scale" : {
            "layout:index" : 4,
        },
        "subsurface_ior" : {
            "label" : "IOR",
            "layout:index" : 5,
        },
        "subsurface_anisotropy" : {
            "label" : "Anisotropy",
            "layout:index" : 6,
        },
        "normal" : {
            "layout:index" : 7,
        },
    },
    "math" : {
        "math_type" : {
            "label" : "Operation",
            "layout:index" : 1,
        },
        "value1" : {
            "layout:index" : 2,
        },
        "value2" : {
            "layout:index" : 3,
        },
        "value3" : {
            "layout:index" : 4,
        },
        "use_clamp" : {
            "label" : "Clamp",
            "layout:index" : 5,
        },
    },
    "rgb_ramp" : {
        "ramp_alpha" : {
            "label" : "Ramp Alpha",
        },
    },
    "glass_bsdf" : {
        "distribution" : {
            "layout:index" : 1,
        },
        "color" : {
            "layout:index" : 2,
        },
        "roughness" : {
            "layout:index" : 3,
        },
        "ior" : {
            "layout:index" : 4,
        },
        "normal" : {
            "layout:index" : 5,
        },
    },
    "toon_bsdf" : {
        "component" : {
            "layout:index" : 1,
        },
        "color" : {
            "layout:index" : 2,
        },
        "size" : {
            "layout:index" : 3,
        },
        "smooth" : {
            "layout:index" : 4,
        },
        "normal" : {
            "layout:index" : 5,
        },
    },
    "glossy_bsdf" : {
        "distribution" : {
            "layout:index" : 1,
        },
        "color" : {
            "layout:index" : 2,
        },
        "roughness" : {
            "layout:index" : 3,
        },
        "anisotropy" : {
            "layout:index" : 4,
        },
        "rotation" : {
            "layout:index" : 5,
        },
        "tangent" : {
            "layout:index" : 6,
        },
        "normal" : {
            "layout:index" : 7,
        },
    },
    "refraction_bsdf" : {
        "distribution" : {
            "layout:index" : 1,
        },
        "color" : {
            "layout:index" : 2,
        },
        "roughness" : {
            "layout:index" : 3,
        },
        "ior" : {
            "layout:index" : 4,
        },
        "normal" : {
            "layout:index" : 5,
        },
    },
    "sheen_bsdf" : {
        "distribution" : {
            "layout:index" : 1,
        },
        "color" : {
            "layout:index" : 2,
        },
        "roughness" : {
            "layout:index" : 3,
        },
        "normal" : {
            "layout:index" : 4,
        },
    },
    "diffuse_bsdf" : {
        "color" : {
            "layout:index" : 1,
        },
        "roughness" : {
            "layout:index" : 2,
        },
        "normal" : {
            "layout:index" : 3,
        },
    },
}

def visibility( plug, value, param ) :  

    node = { "principled_hair_bsdf", "vector_rotate", "environment_texture", "image_texture",
             "voronoi_texture", "sky_texture", "noise_texture",
             "ies_light", "checker_texture", "gradient_texture",
             "musgrave_texture", "magic_texture", "wave_texture",
             "brick_texture" }
    
    for x in node :
        if plug.node()["name"].getValue() == x :
            return plug.node()["parameters"][param].getValue() == value 

def metadata( plug, name ) :

    global parameterMetadata

    shaderName = plug.node()["name"].getValue()
    shaderDict = parameterMetadata.get( shaderName )
    if shaderDict is None :
        return None

    parameterDict = shaderDict.get( plug.getName() )
    if parameterDict is None :
        return None
    return parameterDict.get( name )

### CyclesShader ###

### main metadata assignments ###

for name in ( "label", "layout:section", "layout:index", "userDefault" ) :
    Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.*", name, functools.partial( metadata, name = name ) )

### parameter visibility in principled_hair_bsdf and vector_rotate ### 

Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.absorption_coefficient", "layout:visibilityActivator", functools.partial( visibility, value = "Absorption coefficient", param = "parametrization" ) )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.melanin", "layout:visibilityActivator", functools.partial( visibility, value = "Melanin concentration", param = "parametrization" ) )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.melanin_redness", "layout:visibilityActivator", functools.partial( visibility, value = "Melanin concentration", param = "parametrization" ) )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tint", "layout:visibilityActivator", functools.partial( visibility, value = "Melanin concentration", param = "parametrization" ) )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.random_color", "layout:visibilityActivator", functools.partial( visibility, value = "Melanin concentration", param = "parametrization" ) )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.color", "layout:visibilityActivator", functools.partial( visibility, value = "Direct coloring", param = "parametrization" ) )

Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.rotation", "layout:visibilityActivator", functools.partial( visibility, value = "euler_xyz", param = "rotate_type" ) )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.axis", "layout:visibilityActivator", functools.partial( visibility, value = "axis", param = "rotate_type" ) )

mapping = [ "parameters.tex_mapping__translation", "parameters.tex_mapping__rotation", "parameters.tex_mapping__scale", "parameters.tex_mapping__use_minmax", 
           "parameters.tex_mapping__min", "parameters.tex_mapping__max", "parameters.tex_mapping__x_mapping", "parameters.tex_mapping__y_mapping", 
           "parameters.tex_mapping__z_mapping", "parameters.tex_mapping__type", "parameters.tex_mapping__projection" ]
mapping_labels = [ "Translation", "Rotation", "Scale", "Use Min Max", "Min", "Max", "X Mapping", "Y Mapping", "Z Mapping", "Type", "Projection" ]
mapping_index = 89

### tex_mapping section, indexes and labels ###

for x, y in zip( mapping, mapping_labels ) :
    Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, x, "layout:section", "Texture Mapping" )
    Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, x, "layout:index", mapping_index )
    Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, x, "label", y )

    mapping_index += 1

### parameter visibility for tex_mapping min/max ###

Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__min", "layout:visibilityActivator", functools.partial( visibility, value = True, param = "tex_mapping__use_minmax" ) )
Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.tex_mapping__max", "layout:visibilityActivator", functools.partial( visibility, value = True, param = "tex_mapping__use_minmax" ) )

### universal labels ###

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

### hide dupli ###

Gaffer.Metadata.registerValue( GafferCycles.CyclesShader, "parameters.from_dupli", "plugValueWidget:type", "" )

### CyclesLight ###

### universal indexes ###

Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "name", "layout:index", 1 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "sets", "layout:index", 2 )

Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.color", "layout:index", 3 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.intensity", "layout:index", 4 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.exposure", "layout:index", 5 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.normalize", "layout:index", 6 )

Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.size", "layout:index", 7 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.map_resolution", "layout:index", 7 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.spot_angle", "layout:index", 8 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.angle", "layout:index", 8 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.width", "layout:index", 8 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.spot_smooth", "layout:index", 9 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.height", "layout:index", 9 )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.spread", "layout:index", 10 )
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

### universal sections ###

Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.cast_shadow", "layout:section", "Contribution" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_mis", "layout:section", "Contribution" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_camera", "layout:section", "Contribution" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_diffuse", "layout:section", "Contribution" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_glossy", "layout:section", "Contribution" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_transmission", "layout:section", "Contribution" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_scatter", "layout:section", "Contribution" )
Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_caustics", "layout:section", "Contribution" )

### universal labels ###

Gaffer.Metadata.registerValue( GafferCycles.CyclesLight, "parameters.use_mis", "label", "Use MIS" )

### defaults ###

Gaffer.Metadata.registerValue( "cycles:surface:environment_texture:tex_mapping__scale.x", "userDefault", -1.0 )
Gaffer.Metadata.registerValue( "cycles:surface:environment_texture:tex_mapping__y_mapping", "userDefault", "z" )
Gaffer.Metadata.registerValue( "cycles:surface:environment_texture:tex_mapping__z_mapping", "userDefault", "y" )
