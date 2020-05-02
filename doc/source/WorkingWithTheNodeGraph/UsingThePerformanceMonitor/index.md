<!-- !NO_SCROLLSPY -->

# Using the Performance Monitor #

Gaffer contains a built-in performance monitor, which can help diagnose and optimize a node graph's performance. With the monitor active, performance statistics will be sent to the standard output (stdout) during dispatched renders.

> Note :
> Performance statistics using the performance monitor cannot be generated for IPR rendering.

To turn on the performance monitor:

1. Create a StandardOptions node.

2. In the Graph Editor, connect the StandardOptions node just prior to your script's render task node.

3. In the Node Editor, with the StandardOptions node still selected, navigate to _Statistics_ > _Settings_.

4. Toggle the Performance Monitor plug's switch, and then check its box.

    ![](images/nodeEditorWindowPerformanceMonitor.png "The performance monitor, activated")

When you dispatch your script to the renderer, performance data will output to the stdout in your terminal. If you are dispatching to a render farm, the farm will receive the stdout.

As an alternative, the [stats app](../../Reference/CommandLineReference/stats.md) allows the same monitoring to be performed from the command line, without the need to dispatch the script.


## Annotating scripts with performance data ##

The stats app can generate annotations that display per-node performance and Context data by using the built-in `-annotatedScript` option. This feature will make a copy of the monitored script and add each node's performance statistics as graph metadata.
To annotate a script with performance data, use the following command:
```
gaffer stats <script> -performanceMonitor -annotatedScript <annotatedScript>
```
If you'd like the annotations to contain information about the number of [Contexts](../Contexts/index.md) used, replace `-performanceMonitor` with `-contextMonitor`.
For more details on the stats app's command-line options, see the [stats app reference](../../Reference/CommandLineReference/stats.md).



## See also ##

- [Performance Best Practices](../PerformanceBestPractices/index.md)
- [Stats App](../../Reference/CommandLineReference/stats.md)
