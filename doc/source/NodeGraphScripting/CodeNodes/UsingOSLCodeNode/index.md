# Using the OSLCode Node #

The OSLCode node enables execution of arbitrary code in OSL.


## Adding Input and Output Parameter Plugs ##

The OSLCode nodes requires input and output parameter plugs for the code to work with. Once the parameters are established, OSL code can be entered into the _Code_ input field to generate a resulting output.

1. Select the OSLCode node. The _Viewer_ and _Node Editor_ will show a shader with empty values.

2. In the _Node Editor_, in the _Inputs_ section, click ![the plus icon](images/plus.png "The plus icon"). A drop-down menu will appear.

3. Select a plug type from the drop-down menu. That type will be added to the _Inputs_ section, with the label _Input1_.

4. Double-click the _Input1_ label, and type an appropriate name.

5. Set the value of the plug as needed.

<!-- TODO: connecting other nodes to input plugs? -->

<!-- TODO: closure plug type? -->


## Updating the Interactive Shaderball ##

Once you update your code, you likely want to see the results.

To update the interactive shaderball: with the _Code_ field still focused, hit <kbd>Control</kbd> + <kbd>Enter</kbd>.


## Referencing Parameter Plugs ##

> Note :
> Dragging and dropping a ColorSpline plug type will reference its value, not its name.

To reference a plug from the _Inputs_ or _Outputs_ sections in your OSL code, drag and drop its label onto the _Code_ input field.


## See Also ##

- [OSLCode Node](../OSLCodeNode/index.md)
- [OSLCode Node Reference](../../../Reference/NodeReference/GafferOSL/OSLCode.md)

