# Tutorial: Using The OSLCode Node #

Using OSL to build shaders opens up a world of possibility for creating complex and customized looks, shading, and processing. Gaffer's built-in OSLCode node enables execution of arbitrary code in OSL. In this tutorial, we will demonstrate how to build a very rudimentary striped shader. We will cover the following topics:

- Inputting code into the OSLCode node
- Adding input and output parameter plugs to the node

Before starting this tutorial, we recommend completing the [Assembling the Gaffer Bot](../../GettingStarted/index.md) and [Introduction to Scripting](../GettingStarted/index.md) starter tutorials.


## Creating a Striped Shader ##

OSLCode nodes require input and output parameter plugs for the code to work with. Once the parameters are established, any OSL code can be entered to generate an output based on them.


### The basic setup ###

To begin the striped look, first create the node, add some parameters, and then input some basic code:

1. Create an OSLCode node and select it. The _Viewer_ and _Node Editor_ will show a shader with empty values.

    ![Default OSLCode node, in the Viewer](images/viewerShader.png "Default OSLCode node, in the Viewer")

    ![Default OSLCode node, in the Node Editor](images/nodeEditorShader.png "Default OSLCode node, in the Node Editor")

2. In the _Node Editor_, in the _Inputs_ section, click ![the plus icon](images/plus.png "The plus icon") and select _Float_ from the drop-down menu. A Float input plug named _Input1_ will appear.

3. Double-click the _Input1_ label, and rename it to `width`.

4. Set the Width value to `0.025`.

5. In the _Outputs_ section, click ![the plus icon](images/plus.png "The plus icon") and select _Color_ from the drop-down menu. A Color output plug named _Output1_ will appear.

6. Double-click the _Output1_ label, and rename it to `stripes`.

7. Put the following in the _Code_ input field:

    ```
    stripes = aastep( 0, sin( v * M_PI / width ) )
    ```

    ![OSLCode node's parameters and plugs](images/nodeEditorShaderParameters.png "OSLCode node's parameters and plugs")

> Tip :
> To reference a plug from the _Inputs_ or _Outputs_ sections in your OSL code, drag and drop its label onto the _Code_ input field. This is key to referring to the Color Spline input, which uses a special syntax.

Since shader previews in the _Viewer_ are interactive, the _Viewer_ will automatically update to show the shader, now with a monochrome stripe pattern.

![The shader ball with stripes, in the Viewer](images/viewerShaderStripes.png "The shader ball with stripes, in the Viewer")


### Adding colors and wobble ###

Now it's time to add color using a few more input parameters, and a noisy wobble pattern to the stripes using additional code:

1. Add a color input parameter plug and rename it to `color1`.

2. Add another color input parameter plug and rename it to `color2`.

3. Click the color swatch (the black rectangle) at the far-right of the plug.
    
    ![The color plugs](images/nodeEditorColorInputs.png "The color plugs")

    For each plug, pick a color of your choosing.

4. Update the code:

    ```
    float vv = v + 0.05 * pnoise( u * 20, 4 );
    float m = aastep( 0, sin( vv * M_PI / width ) );
    stripes = mix( color1, color2, m );
    ```

The final resulting shader:

![The shader ball with stripes and colors](images/viewerShaderStripesColors.png "The shader ball with stripes and colors")


## Recap ##

While this was quick introduction with a very simple shader, you should now be equipped to use the OSLCode node by interactively adding input and output parameter plugs and editing code.


## See Also ##

- [OSLCode Node Reference](../../NodeReference/GafferOSL/OSLCode.md)
- [Expression Node](../ExpressionNode/index.md)
- [PythonCommand Node](../PythonCommandNode/index.md)
- [SystemCommand Node](../SystemCommandNode/index.md)
