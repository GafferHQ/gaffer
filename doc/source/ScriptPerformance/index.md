# Script Performance #

As with most VFX processes and software, Gaffer scripts – in both senses of your project files and the code that goes into them – are subject to performance considerations. If you're not careful, your graph can easily compute excessive recursion or unintendedly impactful processes, and the structure that brought about the drop in performance can be difficult to spot. Developing a basic understanding of how Gaffer evaluates graphs, and the complexity pitfalls users commonly encounter, can help you mitigate performance setbacks.

<!-- TOC 
    TODO: Multithreading/index.md
    TODO: DeferredExecution/index.md
-->

```eval_rst
.. toctree::
    :titlesonly:
    :maxdepth: 1

    PerformanceBestPractices/index.md
    UsingThePerformanceMonitor/index.md
```