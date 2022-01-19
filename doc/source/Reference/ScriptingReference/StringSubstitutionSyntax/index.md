<!-- !NO_SCROLLSPY -->

String Substitution Syntax
==========================

Substitution             | Syntax     | Example             | Result
-------------------------|------------|---------------------|-----------
Frame number             | `#`        | `image.#.exr`       | `image.1.exr`
Padded frame number      | `####`     | `image.####.exr`    | `image.0001.exr`
Home directory           | `~`        | `~/gaffer/projects` | `/home/stanley/gaffer/projects`
Context variable         | `${name}`  | `${scene:path}`     | `/world/sphere`
Environment variable     | `${name}`  | `/disk1/${USER}`    | `/disk1/stanley`
Escape special character | `\\`       | `\\$`               | `$`
