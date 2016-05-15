import re

from pathlib import Path

import sys


class Colors:
    HEADER = '\033[95m'
    OK_BLUE = '\033[94m'
    OK_GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


class I:
    """Interaction-related methods"""

    @staticmethod
    def title(title_text: str):
        print(Colors.BOLD + '\n' + title_text + '\n' + Colors.RESET)

    @staticmethod
    def ask(question: str, default: str = None, show_default: bool = True):
        while True:
            answer = input(question + (' [' + default + ']' if default and show_default else '') + ' ')
            if answer:
                return answer
            elif default is not None:
                return default

    @classmethod
    def ask_bool(cls, question: str, default: bool):
        options_invite, default_str = ('[Yn]', 'y') if default else ('[yN]', 'n')

        while True:
            answer = cls.ask(question + ' ' + options_invite, default=default_str, show_default=False).lower()
            if answer in ['y', 'n']:
                return answer == 'y'


class StringUtils:
    _first_cap_re = re.compile('(.)([A-Z][a-z]+)')
    _all_cap_re = re.compile('([a-z0-9])([A-Z])')

    @classmethod
    def camel_case_to_snake_case(cls, camel_name):
        s1 = StringUtils._first_cap_re.sub(r'\1_\2', camel_name)
        return StringUtils._all_cap_re.sub(r'\1_\2', s1).lower()

    @staticmethod
    def create_java_class_name(raw_name):
        first, *rest = raw_name.replace('-', '_').replace(' ', '_').split('_')
        return first[0].upper() + first[1:] + ''.join(word[0].upper() + word[1:] for word in rest)

    @staticmethod
    def indent(text: str, level):
        indented = ''
        for line in text.strip('\n').split('\n'):
            indented += (' ' * 4 * level) + line + '\n'

        return indented


class BukkitPluginGenerator:
    MAVEN_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>{groupId}</groupId>
    <artifactId>{artifactId}</artifactId>
    <version>{version}</version>

    <packaging>jar</packaging>

    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <maven.compiler.source>{java_version}</maven.compiler.source>
        <maven.compiler.target>{java_version}</maven.compiler.target>
    </properties>
{build}
    <repositories>
        <repository>
            <id>spigot-repo</id>
            <url>https://hub.spigotmc.org/nexus/content/groups/public/</url>
        </repository>{zlib_repo}
    </repositories>

    <dependencies>
        <dependency>
            <groupId>org.bukkit</groupId>
            <artifactId>bukkit</artifactId>
            <version>1.9-R0.1-SNAPSHOT</version>
        </dependency>{zlib_dependency}
    </dependencies>
</project>
'''

    MAVEN_ZLIB_SHADING_TEMPLATE = '''
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-shade-plugin</artifactId>
                <version>2.3</version>
                <configuration>
                    <minimizeJar>true</minimizeJar>
                    <artifactSet>
                        <includes>
                            <include>fr.zcraft:zlib</include>
                        </includes>
                    </artifactSet>
                    <relocations>
                        <relocation>
                            <pattern>fr.zcraft.zlib</pattern>
                            <shadedPattern>{pckg}.zlib</shadedPattern>
                        </relocation>
                    </relocations>
                </configuration>
                <executions>
                    <execution>
                        <phase>package</phase>
                        <goals>
                            <goal>shade</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
'''

    MAVEN_ZLIB_REPO_TEMPLATE = '''
        <repository>
            <id>zDevelopers</id>
            <url>http://maven.carrade.eu/artifactory/snapshots</url>
        </repository>'''

    MAVEN_ZLIB_DEPENDENCY_TEMPLATE = '''
        <dependency>
            <groupId>fr.zcraft</groupId>
            <artifactId>zlib</artifactId>
            <version>0.99-SNAPSHOT</version>
        </dependency>'''

    MAIN_CLASS_TEMPLATE = '''package {package};

{imports}


public final class {class_name} extends {base_class}
{{
    private static {class_name} instance;

    @Override
    public void onEnable()
    {{
        instance = this;{on_enable}
    }}

    public static {class_name} get()
    {{
        return instance;
    }}
}}
'''

    LISTENER_TEMPLATE = '''package {package};

import org.bukkit.event.Listener;
{imports}

public final class {class_name} {extends}implements Listener
{{
    // TODO implement events listeners
}}
'''

    COMMAND_ZLIB_TEMPLATE = '''package {package};

import fr.zcraft.zlib.components.commands.Command;
import fr.zcraft.zlib.components.commands.CommandException;
import fr.zcraft.zlib.components.commands.CommandInfo;

import java.util.List;


@CommandInfo (name = "{sub_command_name}", usageParameters = "")
public final class {class_name} extends Command
{{
    @Override
    protected void run() throws CommandException
    {{
        // TODO implement command /{command_name} {sub_command_name}
    }}

    @Override
    protected List<String> complete() throws CommandException
    {{
        // TODO implement auto-completion for /{command_name} {sub_command_name}
        return null;
    }}
}}
'''

    COMMAND_BUKKIT_TEMPLATE = '''package {package};

import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabCompleter;

import java.util.List;


public class {class_name} implements CommandExecutor, TabCompleter
{{
    @Override
    public boolean onCommand(CommandSender sender, Command cmd, String label, String[] args)
    {{
        // TODO implement command /{command_name}
    }}

    @Override
    public List<String> onTabComplete(CommandSender sender, Command cmd, String label, String[] args)
    {
        // TODO implement auto-completion for /{command_name}
        return null;
    }
}}
'''

    def __init__(self, folder: Path, name: str, package: str, main_class: str, version: str, author: str = None,
                 website: str = None, description: str = None, load_at_startup: bool = False, zlib: bool = True,
                 java_version: str = '1.7', stdout=None, stderr=None):
        self.folder = folder

        self.name = name
        self.package = package
        self.main_class = main_class
        self.version = version
        self.author = author
        self.website = website
        self.description = description

        self.load_at_startup = load_at_startup
        self.zlib = zlib

        self.java_version = java_version

        self.listeners = []
        self.commands = []

        self.stdout = stdout
        self.stderr = stderr

        self._folder_main = self.folder / 'src/main'
        self._folder_java = self._folder_main / 'java'
        self._folder_resources = self._folder_main / 'resources'

        self._folder_root_package = self._folder_java / (self.package.replace('.', '/'))
        self._folder_commands = self._folder_root_package / 'commands'
        self._folder_listeners = self._folder_root_package / 'listeners'

    def add_command(self, command):
        self.commands.append(command)

    def add_listener(self, listener: str):
        self.listeners.append(listener)

    def generate(self):
        self._save_file('pom.xml', self._generate_maven())
        self._save_file('plugin.yml', self._generate_plugin_yml(), self._folder_resources)

        self._save_file(self.main_class + '.java', self._generate_main_class(), self._folder_root_package)

        self._generate_listeners()
        self._generate_commands()

    def _save_file(self, relative_name: str, content: str, root: Path = None):
        if root is None:
            root = self.folder

        file_path = root / relative_name
        parent = file_path.parent

        if not parent.exists():
            file_path.parent.mkdir(parents=True)
        elif not parent.is_dir():
            if self.stderr:
                self.stderr.write(
                        Colors.FAIL + 'Cannot create folder {0}: a non-folder file already exists' + Colors.RESET)
            return

        file_path.touch(exist_ok=True)
        with file_path.open(mode='w') as f:
            f.write(content)

        if self.stdout:
            self.stdout.write('Wrote file {0}\n'.format(str(file_path)))

    def _generate_maven(self):
        artifact = StringUtils.create_java_class_name(self.name)
        group = self.package.replace('.' + artifact, '')

        return self.MAVEN_TEMPLATE.format(
                groupId=group,
                artifactId=artifact,
                version=self.version,
                java_version=self.java_version,
                build=self.MAVEN_ZLIB_SHADING_TEMPLATE.format(pckg=self.package) if self.zlib else '',
                zlib_repo=self.MAVEN_ZLIB_REPO_TEMPLATE if self.zlib else '',
                zlib_dependency=self.MAVEN_ZLIB_DEPENDENCY_TEMPLATE if self.zlib else ''
        )

    def _generate_plugin_yml(self):
        plugin_yml = '''name: {0}\nversion: {1}\nmain: {2}.{3}\n''' \
            .format(self.name, self.version, self.package, self.main_class)

        if self.author or self.website or self.description:
            plugin_yml += '\n'
            if self.description:
                plugin_yml += 'description: {0}\n'.format(self.description)
            if self.author:
                plugin_yml += 'author: {0}\n'.format(self.author)
            if self.website:
                plugin_yml += 'website: {0}\n'.format(self.website)

        if self.load_at_startup:
            plugin_yml += '\nload: STARTUP\n'

        if self.commands:
            plugin_yml += '\ncommands:\n'
            for command in self.commands:
                plugin_yml += '    {0}:\n        description: {1}\n'.format(command['name'], command['description'])

        return plugin_yml

    def _generate_main_class(self):
        on_enable = ''
        imports = []

        if self.zlib:
            components = []

            base_class = 'ZPlugin'
            imports.append('fr.zcraft.zlib.core.ZPlugin')

            if self.commands:
                components.append('Commands.class')
                imports.append('fr.zcraft.zlib.components.commands.Commands')

            for listener in self.listeners:
                components.append(listener + '.class')
                imports.append(self.package + '.listeners.' + listener)

            on_enable = 'loadComponents(' + ', '.join(components) + ');\n'

            if self.commands:
                on_enable += '\n'
                for command in self.commands:
                    sub_commands_classes = []

                    for sub_command_name in command['sub_commands']:
                        class_name = self.__generate_zlib_command_class_name(command['name'], sub_command_name)
                        sub_commands_classes.append(class_name + '.class')
                        imports.append(self.package + '.commands.' + command['name'].lower() + '.' + class_name)

                    on_enable += 'Commands.register("{name}"{sub_commands});\n'.format(
                            name=command['name'],
                            sub_commands=', ' + ', '.join(sub_commands_classes) if command['sub_commands'] else ''
                    )
        else:
            base_class = 'JavaPlugin'
            imports.append('org.bukkit.plugin.java.JavaPlugin')

            for listener in self.listeners:
                imports.append(self.package + '.listeners.' + listener)
                on_enable += 'getServer().getPluginManager().registerEvents(new {0}(), this);\n'.format(listener)

            if self.commands:
                on_enable += '\n'
                for command in self.commands:
                    class_name = self.__generate_bukkit_command_class_name(command['name'])
                    imports.append(self.package + '.commands.' + class_name)
                    on_enable += 'getCommand("{0}").setExecutor(new {1}());\n'.format(command['name'], class_name)

        return self.MAIN_CLASS_TEMPLATE.format(
                package=self.package,
                class_name=self.main_class,
                base_class=base_class,
                imports='\n'.join('import {0};'.format(class_name) for class_name in imports),
                on_enable='\n\n' + StringUtils.indent(on_enable.strip(), 2) if on_enable else ''
        )

    def _generate_listeners(self):
        for listener in self.listeners:
            self._save_file(listener + '.java', self._generate_listener(listener), self._folder_listeners)

    def _generate_listener(self, listener):
        return self.LISTENER_TEMPLATE.format(
                package=self.package + '.listeners',
                imports='import fr.zcraft.zlib.core.ZLibComponent;\n' if self.zlib else '',
                class_name=listener,
                extends='extends ZLibComponent ' if self.zlib else ''
        )

    def _generate_commands(self):
        for command in self.commands:
            if self.zlib:
                package_folder = self._folder_commands / command['name'].lower()

                for sub_command in command['sub_commands']:
                    self._save_file(self.__generate_zlib_command_class_name(command['name'], sub_command) + '.java',
                                    self._generate_command_zlib(command['name'], sub_command), package_folder)

            else:
                self._save_file(self.__generate_bukkit_command_class_name(command['name']) + '.java',
                                self._generate_command_bukkit(command['name']), self._folder_commands)

    def _generate_command_zlib(self, command_name, sub_command_name):
        return self.COMMAND_ZLIB_TEMPLATE.format(
            package=self.package + '.commands.' + command_name.lower(),
            command_name=command_name,
            sub_command_name=sub_command_name,
            class_name=self.__generate_zlib_command_class_name(command_name, sub_command_name)
        )

    def _generate_command_bukkit(self, command_name):
        return self.COMMAND_BUKKIT_TEMPLATE.format(
            package=self.package + '.commands',
            command_name=command_name,
            class_name=self.__generate_bukkit_command_class_name(command_name)
        )

    @staticmethod
    def __generate_zlib_command_class_name(command_name: str, sub_command_name: str):
        return command_name.capitalize() + sub_command_name.capitalize() + 'Command'

    @staticmethod
    def __generate_bukkit_command_class_name(command_name: str):
        return command_name.capitalize() + 'Command'


if __name__ == '__main__':
    print(Colors.HEADER + 'Bukkit plugin bootstrap generator' + Colors.RESET)

    I.title('The basics')

    name = I.ask('What\'s your plugin name?')
    version = I.ask('What\'s your plugin version?', '1.0')
    author = I.ask('What\'s your name?', '')
    website = I.ask('Enter the plugin\'s website, if it exists.', '')
    description = I.ask('Enter a short description if you want.', '')

    I.title('Technical basics')

    java_version = I.ask('Enter the Java version you want to use (1.7 or 1.8).', '1.7')
    package = I.ask('What package do you want to use?')
    main_class = I.ask('Enter the name of your main class.', StringUtils.create_java_class_name(name))
    load_at_startup = I.ask_bool('Do you want your plugin to be loaded at startup? '
                                 'Required if you plan to alter the map generation.', False)
    zlib = I.ask_bool('Do you plan to use zLib?', True)

    I.title('Listeners generation')

    listeners = []
    if I.ask_bool('Do you want us to add listeners for you?', True):
        print()
        while True:
            listener = I.ask('Enter a listener name. An empty name ends.', '')
            if not listener:
                break

            listeners.append(listener)

    I.title('Commands')

    commands = []
    if I.ask_bool('Do you want us to add commands for you?', True):
        while True:
            command_name = I.ask('\nEnter the name of a command. An empty name ends.', '')
            if not command_name:
                break

            if command_name.startswith('/'):
                command_name = command_name[1:]

            command_description = I.ask('Enter a short description, if you want.', '')

            sub_commands = []
            if zlib:
                sub_commands_raw = I.ask('Enter the name of the /{0} sub-commands, '
                                         'space-separated.'.format(command_name), '').split()
                for sub_command in sub_commands_raw:
                    sub_commands.append(sub_command.strip())

            commands.append({
                'name': command_name,
                'description': command_description,
                'sub_commands': sub_commands
            })

    I.title('Files location')

    current_directory = Path('.')
    folder_full = None
    while True:
        folder = I.ask('Type the folder where the plugin will be generated.', name.lower().replace(' ', '_'))
        folder_full = current_directory / folder
        if folder_full.exists():
            print(Colors.FAIL + 'Error: please select another directory as {0} already exists.'.format(
                    str(folder_full)) + Colors.RESET)
        else:
            break

    I.title('Generating...')

    generator = BukkitPluginGenerator(
            folder=folder_full,
            name=name, package=package, main_class=main_class, version=version,
            author=author, website=website, description=description, load_at_startup=load_at_startup, zlib=zlib,
            java_version=java_version, stdout=sys.stdout, stderr=sys.stderr
    )

    [generator.add_listener(listener) for listener in listeners]
    [generator.add_command(command) for command in commands]

    generator.generate()

    print(Colors.BOLD + '\nDone.' + Colors.RESET)
