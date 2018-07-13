# OSLCode Node #

The OSLCode node is a code node from the [GafferOSL module](../../../Reference/NodeReference/GafferOSL/index.md). The nodes in the OSL module provide the capability to create networks of predefined OSL shaders and processes. Sometimes, however, the shader you need does not exist, or it would be easier to express your ideas through a few lines of code. For these situations, the OSLCode node is needed. It allows OSL code to be evaluated directly in the node graph to create new shaders on-the-fly, opening up a world of possibility for creating complex and customized looks, shading, and processing.


![The default OSLCode node](images/mainOSLCodeNode.png "The default OSLCode node")

The OSLCode node's plugs are split into three sections:

- _Inputs:_ The input parameter plugs. Plug types include a variety of number and vectors.
- _Outputs:_ The output parameter plugs. Plug types are the same as the input plug types.
- _Code:_ Input field containing the OSL code to evaluate, using the _input_ and _output_ parameter plugs.


## Interactive Shaderball ##

When selected, the OSLCode node will provide a shaderball preview in the _Viewer_. Use this to interactively build and modify your shader.


## See Also ##

- [Using the OSLCode Node](../UsingOSLCodeNode/index.md)
- [OSLCode Node Reference](../../../Reference/NodeReference/GafferOSL/OSLCode.md)
- [OSL language specification](https://github.com/imageworks/OpenShadingLanguage/blob/master/src/doc/osl-languagespec.pdf)
    - Also available in Gaffer menu: _Help_ > _Open Shading Language_ > _Language Reference_
- [OSL mailing list](https://groups.google.com/forum/#!forum/osl-dev)
