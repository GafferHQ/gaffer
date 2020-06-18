Tutorial: Using The OSLCode Node
================================

Gaffer allows the creation of networks of predefined [OSL][1] shaders to be used in renderering and image and geometry processing, without any coding required. But sometimes the shader you want doesn't exist, or it's easier to express your ideas through a few lines of code. In these situations, the OSLCode node allows OSL source code to be entered directly, to create new shaders on the fly.

A one line shader
-----------------

Start by creating an OSLCode node in the Graph Editor. With this selected, the Node Editor will display a blank shader to be edited.

![](images/blank.png "Blank Shader")

We'll start by adding some parameters (inputs and outputs) for the shader.

- Click on the upper ![](images/plus.png "Plus") and choose "Float" from the menu. This creates an input parameter which takes a floating point number.
- Double click the "Input1" label that appears, and rename the parameter to `width`.
- Enter the value `0.025` into the width field.
- Click on the lower ![](images/plus.png "Plus") and choose "Color" from the menu. This creates an output color parameter.
- Double click the "Output1" label, and rename the parameter to "stripes".

![](images/parameters.png "Parameters")

We can now enter any OSL code we want to generate the output from the input. Start by entering the following :

```
stripes = aastep( 0, sin( v * M_PI / width ) )
```

Now hit <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to update the shader. The Viewer will update to show a shader ball with the shader on it, and adjusting the width parameter will update the render interactively.

![](images/shaderBallStripes.png "Shader ball")

> Tip : Enter the names for input and outputs into the code easily by dragging
> their labels into the code editor. This is especially useful for color
> spline inputs, where some special syntax is required to evaluate the spline.

Adding some more features
---------------------

Let's add a bit of color and some wobble to our shader, to demonstrate a few more features of OSL :

- Add a color input and rename it to `color1`.
- Add another color input and rename it to `color2`.
- Click on the colour swatches to pick some tasteful hues.

Now update the code :

```
float vv = v + 0.05 * pnoise( u * 20, 4 );
float m = aastep( 0, sin( vv * M_PI / width ) );
stripes = mix( color1, color2, m );
```

And as before, hit <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to update the shader.

![](images/shaderBallColoredStripes.png "Shader ball")

No doubt you didn't come here to learn how to make blue and red wobbly stripes, but you are now armed with the ability to add inputs and outputs, edit code and view the results interactively, so are hopefully in a position to create the shader you do want.

> Tip : Explore the available functions in OSL and add them easily to the code by right-clicking, then browsing the _Insert_ sub-menu.

OSL resources
-------------

This short tutorial has only scratched the surface of what can be done with Open Shading Language. The following resources are a good place to learn more :

- The [language specification](https://github.com/imageworks/OpenShadingLanguage/blob/master/src/doc/osl-languagespec.pdf) (also available from _Help_ > _Open Shading Language_ > _Language Reference_)
- The [OSL mailing list](https://groups.google.com/forum/#!forum/osl-dev)

[1]: https://github.com/imageworks/OpenShadingLanguage
