import yaml
import sys
import re

from collections import OrderedDict


def yaml_config_to_zlib_class(raw_yaml_content):
    yaml_config = _yaml_ordered_load(raw_yaml_content)

    java_class = '''package ;

import fr.zcraft.zlib.components.configuration.Configuration;
import fr.zcraft.zlib.components.configuration.ConfigurationItem;
import fr.zcraft.zlib.components.configuration.ConfigurationSection;

import static fr.zcraft.zlib.components.configuration.ConfigurationItem.item;
import static fr.zcraft.zlib.components.configuration.ConfigurationItem.list;
import static fr.zcraft.zlib.components.configuration.ConfigurationItem.section;


/**
 * Configuration.
 *
 * FIXME Auto-generated configuration class, check if it was correctly generated (especially guessed data types).
 *
 * Nota: you can also use specific types directly in this configuration class (like ItemStack, Locale, any Enum,
 * Vector...), and even write your owns.
 * See: fr.zcraft.zlib.components.configuration.ConfigurationValueHandlers
 */
public class Config extends Configuration
{
'''

    java_class += _generate_java_config_class(yaml_config)

    java_class += '}'

    return java_class


def yaml_file_config_to_zlib_class(path):
    with open(path) as f:
        return yaml_config_to_zlib_class(f.read())


# 0: data type class
# 1: java constant name
# 2: yaml sub-path
# 3: default value (with quotes if string) or class if default is null
_SINGLE_ENTRY = '''static public final ConfigurationItem<{0}> {1} = item("{2}", {3});'''

# 0: data type class
# 1: java constant name
# 2: yaml sub-path
# 3: class type
_SINGLE_LIST_ENTRY = '''static public final ConfigurationList<{0}> {1} = list("{2}", {3});'''

# 0: data type class
# 1: java constant name
# 2: yaml sub-path
# 3: default value (with quotes if string)
_SINGLE_SECTION_ENTRY = '''public final ConfigurationItem<{0}> {1} = item("{2}", {3});'''

# 0: data type class
# 1: java constant name
# 2: yaml sub-path
# 3: class type
_SINGLE_SECTION_LIST_ENTRY = '''public final ConfigurationList<{0}> {1} = list("{2}", {3});'''

# 0: sub-class name
# 1: java constant name
# 2: yaml sub-path
# 3: class content (indented)
_SECTION_SUB_CLASS = '''static public final {0} {1} = section("{2}", {0}.class);
static public class {0} extends ConfigurationSection
{{{3}}}
'''

# 0: sub-class name
# 1: java constant name
# 2: yaml sub-path
# 3: class content (indented)
_SECTION_SUB_SUB_CLASS = '''public final {0} {1} = section("{2}", {0}.class);
static public class {0} extends ConfigurationSection
{{{3}}}
'''


def _yaml_ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    return yaml.load(stream, OrderedLoader)


def _indent(text: str, level):
    indented = ''
    for line in text.strip('\n').split('\n'):
        indented += (' ' * 4 * level) + line + '\n'

    return indented


_first_cap_re = re.compile('(.)([A-Z][a-z]+)')
_all_cap_re = re.compile('([a-z0-9])([A-Z])')


def _camel_case_to_snake_case(name):
    s1 = _first_cap_re.sub(r'\1_\2', name)
    return _all_cap_re.sub(r'\1_\2', s1).lower()


def _create_java_constant_name(name):
    return _camel_case_to_snake_case(name).upper().replace('-', '_')


def _create_java_class_name(name):
    first, *rest = name.replace('-', '_').split('_')
    return first[0].upper() + first[1:] + ''.join(word[0].upper() + word[1:] for word in rest)


def _python_to_java_type_and_repr(data):
    t = type(data)

    java_type = '?'
    java_repr = repr(data)
    is_list = False

    if t in [str, type(None)]:
        java_type = 'String'
        java_repr = '"' + (str(data) if data is not None else '') + '"'

    elif t is int:
        java_type = 'Integer'

    elif t is float:
        java_type = 'Double'

    elif t is bool:
        java_type = 'Boolean'
        java_repr = 'true' if data else 'false'

    elif t in [list, tuple, set]:
        sub_data_type = '?'

        if data:
            if t in [list, tuple]:
                sub_data_type, *_ = _python_to_java_type_and_repr(data[0])
            else:
                sub_data_type, *_ = _python_to_java_type_and_repr(data.pop())

        if t is set:
            java_type = ('List' if t in [list, tuple] else 'Set') + '<' + sub_data_type + '>'
            java_repr = 'null'
        else:
            java_type = sub_data_type
            java_repr = 'null'
            is_list = True

    elif t is set:
        java_type = 'Set<?>'
        java_repr = 'null'

    return java_type, java_repr, is_list


def _generate_java_config_class(yaml_part: dict, level=1):
    java_code = ''

    for name in yaml_part:
        item = yaml_part[name]
        t = type(item)

        if t not in [dict, OrderedDict]:
            java_type, java_repr, is_list = _python_to_java_type_and_repr(item)

            # For lists, or without non-null default value, we have to pass the class type as it cannot
            # be retrieved at runtime due to Java limitations.
            default_value = java_repr
            if is_list or java_repr is 'null':
                default_value = java_type + '.class'

            if is_list:
                java_model = _SINGLE_LIST_ENTRY if level is 1 else _SINGLE_SECTION_LIST_ENTRY
            else:
                java_model = _SINGLE_ENTRY if level is 1 else _SINGLE_SECTION_ENTRY

            java_code += java_model.format(java_type, _create_java_constant_name(name), name, default_value)

        else:
            sub_class = _generate_java_config_class(item, level + 1)
            java_model = _SECTION_SUB_CLASS if level is 1 else _SECTION_SUB_SUB_CLASS

            java_code += '\n' + java_model.format(
                    _create_java_class_name(name) + 'Section', _create_java_constant_name(name),
                    name, '\n' + sub_class
            )

        java_code += '\n'

    return _indent(java_code, 1)


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print('Usage: {0} <path to YAML config file>'.format(sys.argv[0]))
    else:
        try:
            print(yaml_file_config_to_zlib_class(sys.argv[1]))
        except FileNotFoundError as e:
            print('Cannot load file {0}'.format(sys.argv[1]), file=sys.stderr)
