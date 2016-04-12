#pragma annotation "help" "Helpful description for the shader as a whole"

surface annotationsExample(

#pragma annotation "primaryInput" "primaryParam"
shader primaryParam = null;


uniform float labelParam = 1;
#pragma annotation "labelParam.label" "Special Label"


uniform float helpParam = 1;
#pragma annotation "helpParam.help" "This is some help."


uniform float mapperParam = 1;
#pragma annotation "mapperParam.widget" "mapper"
#pragma annotation "mapperParam.options" "Mode A:1|Mode B:2"

uniform string popupParam = "this";
#pragma annotation "popupParam.widget" "popup"
#pragma annotation "popupParam.options" "this|that|theOther"

uniform float checkBoxParam = 1;
#pragma annotation "checkBoxParam.widget" "checkBox"

uniform string fileNameParam = "/foo/bar";
#pragma annotation "fileNameParam.widget" "filename"

uniform float nullParam = 1;
#pragma annotation "nullParam.widget" "null"

uniform float intParam = 1;
#pragma annotation "intParam.type" "int"

uniform float boolParam = 1;
#pragma annotation "boolParam.type" "bool"

uniform float minMaxParam = 1;
#pragma annotation "minMaxParam.min" "-5"
#pragma annotation "minMaxParam.max" "5"


uniform float dividerParam = 1;
#pragma annotation "dividerParam.divider" "1"


uniform float activatorParamA = 1;
uniform float activatorParamB = 0;
#pragma annotation "activator.activator1.expression" "activatorParamA"
#pragma annotation "activator.activator2.expression" "activatorParamA and activatorParamB"

uniform string enabledParam = "foo";
#pragma annotation "enabledParam.activator" "activator1"
uniform string disabledParam = "foo";
#pragma annotation "disabledParam.activator" "activator2"


uniform float pageParam1 = 1;
uniform float pageParam2 = 1;
#pragma annotation "pageParam1.page" "My Page A"
#pragma annotation "pageParam2.page" "My Page A"
#pragma annotation "page.My Page B.collapsed" "True"

uniform float pageParam3 = 1;
uniform float pageParam4 = 1;
#pragma annotation "pageParam3.page" "My Page B"
#pragma annotation "pageParam4.page" "My Page B"
#pragma annotation "page.My Page B.collapsed" "False"

)
{
	Oi = 1;
	Ci = 1;
}
