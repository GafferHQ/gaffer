#! /usr/bin/env python

# Prints out handy parsing of the 3Delight for Houdini outputs ready for
# 3Delight entries in `outputs.py`.


import urllib.request
import shlex

url = "https://gitlab.com/3Delight/3delight-for-houdini/-/raw/master/ui/aov.cpp"

outputsRaw = []

with urllib.request.urlopen( url ) as f :
    lines = f.read().decode( "utf-8" ).split("\n")
    for i in range( 0, len( lines ) ) :
        line = lines[i]
        if line.strip() == "std::vector<aov::description> descriptions =" :
            i += 1  # Skip `{`
            line = lines[i]
            while line.strip() != "};" :
                outputsRaw.append( line.strip()[1:-2].strip() )  # Remove leading `{` and trailing `},`
                i += 1
                line = lines[i]
            break

outputs = []
print("for name, displayName, source, dataType in [")
for o in outputsRaw :
    if o == "" :
        continue
    m_type, m_ui_name, m_filename_token, m_variable_name, m_variable_source, m_layer_type, m_with_alpha, m_support_mutlilight = shlex.split( o )

    m_layer_type = { "vector": "point", "scalar": "float" }.get( m_layer_type.rstrip( "," ), m_layer_type )

    print(
        '    ( "{}", "{}", "{}", "{}" ),'.format(
            m_variable_name.rstrip( "," ),
            m_ui_name.rstrip( "," ),
            m_variable_source.rstrip( "," ),
            m_layer_type.rstrip( "," )
        )
    )
print( "] :\n\n" )
