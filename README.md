# Code generation tools

In this repository you'll find code generation tools related to zLib and Bukkit plugins development.

## Plugins bootstrap generator

This script will generate a basic Bukkit plugin in the given directory. Useful if you are too lazy to create the first classes and configuration files by hand.  
All the script is in a single file without any extra dependency. Python 3 is required.

Usage:
```bash
python3 plugin_bootstrap.py
```

or, if you don't want to download the script (but [check it before](https://raw.githubusercontent.com/zDevelopers/zLib-CodeGen-Utils/master/plugin_bootstrap.py)!):
```bash
python3 <(curl -s https://raw.githubusercontent.com/zDevelopers/zLib-CodeGen-Utils/master/plugin_bootstrap.py)
```

A few questions will be asked, then the plugin will be generated in the specified directory, ready to be compiled (and modified, of course).

These features are supported.

- Creation of the `pom.xml` file with dependencies.
- Creation of the `plugin.yml` file, with various options.
- Creation of the main class, with static accessor to retrieve the plugin's instance everywhere.
- Creation of listeners, pre-registered in the main class.
- Creation of commands, registered in the `plugin.yml` file and in the main class, with the commands classes pre-generated.
- Support of [zLib](https://github.com/zDevelopers/zLib): if enabled (you'll be asked), you'll have the dependency added in the `pom.xml`, and the code generated in the zLib way.
- Creation of a `.gitignore` file.

These features are not supported.

- Permissions generation in the `plugin.yml` file.
- zLib configuration classes generation (see below for that).


## zLib configuration class generator

This script generates a zLib Config class from a `config.yml` file.
All the script is in a single file. Python 3 and PyYAML are required.

Usage:

```bash
python3 gen_zlib_config.py path/to/config.yml > Config.java
```
