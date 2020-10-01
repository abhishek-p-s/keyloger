#!/usr/bin/env python

from time import sleep
from os import path
from sys import argv
import pyautogui


class Pynputter(object):
    """
    This is the primary entry point into this module for people
    using Pynputter. It expects to receive a procedure in the form
    of a:
        - List
        - String of Text
        - File
    Please refer to the following site to see how to assemble the
    information in a easy to create and maintain format for running
    your procedures.

    Optionally, you may also include a data table in the following
    formats:
        - List
        - String of Text
        - File
    """
    def __init__(self, procedure, data_table=None):
        procedure_converter_factory = ProcedureConverterFactory()
        procedure_converter = procedure_converter_factory(procedure)
        self.procedure = procedure_converter.return_procedure()

        data_converter_factory = DataConverterFactory()
        data_converter = data_converter_factory(data_table)
        self.data_set = data_converter.return_data_set()

    def __call__(self):
        builder = ProcedureBuilder(self.procedure, self.data_set)
        procedure_set = builder.build_procedure_set()
        procedure_commander = ProcedureCommander(procedure_set)
        procedure_commander.execute()


class BaseConverterFactory(object):
    """
    The standard methods and static methods required by the
    converter factories in order to discern which type
    of object should be returned.
    """
    @staticmethod
    def _is_list(input_object):
        return isinstance(input_object, list)

    @staticmethod
    def _is_file(input_object):
        return path.isfile(input_object)


class DataConverterFactory(BaseConverterFactory):
    """
    Factory that takes incoming procedure formats and
    return the correct instantiated object to handle
    the conversion.
    """
    def __call__(self, data_table):
        if data_table is None:
            return NoData()
        elif self._is_list(data_table):
            return DataFromList(data_table)
        elif self._is_file(data_table):
            return DataFromFile(data_table)
        else:
            return DataFromText(data_table)


class ProcedureConverterFactory(BaseConverterFactory):
    """
    Factory that takes incoming procedure formats and
    return the correct instantiated object to handle
    the conversion.
    """
    def __call__(self, procedure):
        if self._is_list(procedure):
            return ProcedureFromList(procedure)
        elif self._is_file(procedure):
            return ProcedureFromFile(procedure)
        else:
            return ProcedureFromText(procedure)


class NoData(object):
    def __init__(self):
        self.name = 'NoData'

    def return_data_set(self):
        return None


class DataFromList(object):
    """
    This class converts data received from a list into the
    the dictionary that is required for input commands.
    """
    def __init__(self, data_list):
        self.data_list = data_list
        self.name = 'DataFromList'
        self.headers = []
        self.data_dictionary = {}
        self.height = len(self.data_list)
        self.width = len(self.data_list[0])

    def _set_headers(self):
        for header in range(0, self.width):
            self.headers.append(self.data_list[0][header])

    def _read_all_table_rows_except_headers(self):
        for row in range(1, self.height):
            self._read_all_column_values_except_the_keys(row)

    def _read_all_column_values_except_the_keys(self, row):
        key = self.data_list[row][0]
        temp_dict = {}

        for column in range(1, self.width):
            header = self.headers[column]
            temp_dict[header] = self.data_list[row][column]

        self.data_dictionary[key] = temp_dict

    def return_data_set(self):
        self._set_headers()
        self._read_all_table_rows_except_headers()

        return self.data_dictionary


class DataFromText(object):
    """
    This class converts data received from a string of text into the
    the dictionary that is required for input commands.
    """
    def __init__(self, data_text, delimiter=','):
        self.data_text = data_text
        self.data_list = []
        self.delimiter = delimiter
        self.name = 'DataFromText'

    @staticmethod
    def _clean_value_in_line(value):
        return_value = str(value).strip()
        return return_value

    def _clean_line(self, line):
        working_line = []

        for value in line:
            cleaned_value = self._clean_value_in_line(value)
            working_line.append(cleaned_value)

        if working_line != ['']:
            self.data_list.append(working_line)

    def _split_each_line(self, text_split_by_line):
        for line in text_split_by_line:
            split_line_by_delimiter = str(line).split(self.delimiter)

            self._clean_line(split_line_by_delimiter)

    def return_data_set(self):
        text_split_by_line = str(self.data_text).split('\n')
        self._split_each_line(text_split_by_line)
        list_to_dict = DataFromList(self.data_list)
        data_set = list_to_dict.return_data_set()
        return data_set


class DataFromFile(object):
    """
    This class converts data received from a file into the
    the dictionary that is required for input commands.
    """
    def __init__(self, data_location):
        self._data = ''
        self._data_list = []
        self._data_location = data_location
        self.name = 'DataFromFile'

    def _import_data(self):
        with open(self._data_location, 'r') as data_file:
            for row in data_file:
                self._data_list.append(row)
        self._data = ''.join(self._data_list)

    def return_data_set(self):
        self._import_data()
        data_from_text = DataFromText(self._data)
        data_set = data_from_text.return_data_set()
        return data_set


class ProcedureFromList(object):
    """
    Class which is supposed to handle converting an
    incoming format into the procedure list. This
    particular class happens to handle the scenario
    which requires no converting.
    """
    def __init__(self, procedure_list):
        self.procedure_list = procedure_list
        self.name = 'ProcedureFromList'

    def return_procedure(self):
        return self.procedure_list


class BaseInterpreter(object):
    """
    This class is the base interpreter which contains all of
    the methods and static methods that all interpreters
    need in order to do their job. It is the template.
    """
    @staticmethod
    def _purge(line, _purge_characters):
        for _purge_character in _purge_characters:
            line = line.replace(_purge_character, '')
        return line

    @staticmethod
    def _remove_parenthesis(line):
        cleaned_line = line.strip()
        if '(' in cleaned_line:
            if cleaned_line[0] == '(':
                cleaned_line = cleaned_line[1:]
        if ')' in cleaned_line:
            if cleaned_line[-1] == ')':
                cleaned_line = cleaned_line[:-1]
        return cleaned_line

    def _remove_quotes(self, text):
        cleaned_text = text.strip()
        first_character = cleaned_text[0]

        if first_character == '"' or first_character == "'":
            cleaned_text = self._purge(text, first_character)

        return cleaned_text

    @staticmethod
    def clean_number(number):
        number_list = []
        number_type = 'int'

        for character in str(number):
            if character == '.' and number_type == 'int':
                number_list.append(character)
                number_type = 'float'
            elif character.isdigit():
                number_list.append(character)

        joined_number = ''.join(number_list)

        if joined_number == '':
            return_number = None
        elif number_type == 'int':
            return_number = int(joined_number)
        elif number_type == 'float':
            return_number = float(joined_number)
        else:
            return_number = None

        return return_number

    def _new_command(self, new_line, line, multiple=False):
        line = self._remove_parenthesis(line)

        command_contents = line.split(',')
        command_action = command_contents[0]
        command_action = self._remove_quotes(command_action)

        if multiple:
            command_action_list = command_action.split(' + ')
            new_line.append(command_action_list)
        else:
            new_line.append(command_action)

        if len(command_contents) > 1:
            command_attribute = command_contents[1]
            command_attribute = self.clean_number(command_attribute)

            if command_attribute is not None:
                new_line.append(command_attribute)

        return new_line


class PrintInterpreter(BaseInterpreter):
    def __init__(self, line):
        self.line = line
        self.name = 'PrintInterpreter'

    def interpret(self):
        new_line = ['print']
        stripped_line = self.line[5:].strip()
        return self._new_command(new_line, stripped_line)


class PressInterpreter(BaseInterpreter):
    def __init__(self, line):
        self.line = line
        self.name = 'PressInterpreter'

    def interpret(self):
        new_line = ['press']
        stripped_line = self.line[5:].strip()
        is_multiple = ' + ' in self.line

        return self._new_command(new_line, stripped_line,
                                 multiple=is_multiple)


class PauseInterpreter(BaseInterpreter):
    def __init__(self, line):
        self.line = line
        self.name = 'PauseInterpreter'

    def interpret(self):
        new_line = ['pause']
        cleaned_line = self.line[5:].strip()
        cleaned_line = self._remove_parenthesis(cleaned_line)
        cleaned_line = cleaned_line.strip()

        if cleaned_line == '':
            new_line.append(1)
        else:
            pause_length = self.clean_number(cleaned_line)
            new_line.append(pause_length)

        return new_line


class InputInterpreter(BaseInterpreter):
    def __init__(self, line):
        self.line = line
        self.name = 'InputInterpreter'

    def interpret(self):
        new_line = ['input']
        stripped_line = self.line[5:].strip()

        return self._new_command(new_line, stripped_line)


class CommentsInterpreter(BaseInterpreter):
    def __init__(self, line):
        self.name = 'CommentsInterpreter'
        self.line = line

    def interpret(self):
        return None


class EmptyLineInterpreter(BaseInterpreter):
    def __init__(self, line):
        self.name = 'EmptyLineInterpreter'
        self.line = line

    def interpret(self):
        return None


class InterpreterFactory(object):
    """
    Factory which receives strings of text and determines
    which object should interpret the text into the cleaned
    up list item to be appended to the procedure list.
    """
    def __init__(self):
        self.line_start = ''
        self.first_character = ''

    def _set_line_characteristics(self, line):
        lower_case_line = str(str(line).lower()).strip()

        if len(lower_case_line) > 5:
            self.line_start = lower_case_line[:5]
            self.first_character = lower_case_line[0]
        else:
            self.line_start = ''
            self.first_character = ''

    def __call__(self, line):
        self._set_line_characteristics(line)

        if self.line_start == 'print':
            return PrintInterpreter(line)
        elif self.line_start == 'press':
            return PressInterpreter(line)
        elif self.line_start == 'pause':
            return PauseInterpreter(line)
        elif self.line_start == 'input':
            return InputInterpreter(line)
        elif self.first_character == '#':
            return CommentsInterpreter(line)
        else:
            return EmptyLineInterpreter(line)


class ProcedureFromText(object):
    """
    This class takes an incoming string of text and
    converts it into the procedure list.
    """
    def __init__(self, procedure_text):
        self.procedure_text = procedure_text
        self.name = 'ProcedureFromText'
        self.processed_list = []

    def return_procedure(self):
        self._interpret_text()
        return self.processed_list

    def _interpret_text(self):
        interpreter_factory = InterpreterFactory()
        split_text = []
        split_text = self.procedure_text.split('\n')
        for line in split_text:
            interpreter = interpreter_factory(line)
            interpreted_line = interpreter.interpret()
            self.processed_list.append(interpreted_line)


class ProcedureFromFile(object):
    """
    This class takes an incoming file and converts it
    into the procedure list.
    """
    def __init__(self, procedure_location):
        self._procedure_location = procedure_location
        self.name = 'ProcedureFromFile'
        self.instructions = ''
        self._instruction_list = []
        self.processed_procedure = []

    def import_instructions(self):
        with open(self._procedure_location, 'r') as procedure_file:
            for row in procedure_file:
                self._instruction_list.append(row)
        self.instructions = ''.join(self._instruction_list)

    def convert_instructions_from_text_to_list(self):
        converter = ProcedureFromText(self.instructions)
        self.processed_procedure = converter.return_procedure()

    def return_procedure(self):
        self.import_instructions()
        self.convert_instructions_from_text_to_list()
        return self.processed_procedure


class ProcedureBuilder(object):
    """
    This class builds the procedure set which will be
    run by the ProcedureCommander. It is expected that it will
    receive the list of commands to be executed in the form
    of a list
    """
    def __init__(self, procedure, data_set):
        self.procedure = procedure
        self.data_set = data_set
        self.command_factory = CommandFactory()
        self.procedure_set = []

    def _build_procedure_for_each_data_record(self):
        if self.data_set is None:
            self._build_procedure_for_each_action(data=None)
        else:
            for data_row in self.data_set:
                self._build_procedure_for_each_action(data_row)

    def _build_procedure_for_each_action(self, data):
        for procedure_row in self.procedure:
            if procedure_row is not None:
                self._add_command_to_procedure_set(procedure_row, data)

    def _add_command_to_procedure_set(self, procedure, data):
        if data is None:
            command = self.command_factory(procedure, None)
        else:
            command = self.command_factory(procedure, self.data_set[data])
        self.procedure_set.append(command)

    def build_procedure_set(self):
        self._build_procedure_for_each_data_record()
        return self.procedure_set


class CommandFactory(object):
    """
    Factory which returns the correctly instantiated
    command object to the caller.
    """
    def __call__(self, instruction_list, data=None):
        if instruction_list[0] == 'input' and data is not None:
            return InputCommand(instruction_list, data)
        elif instruction_list[0] == 'press':
            return PressCommand(instruction_list, data)
        elif instruction_list[0] == 'print':
            return PrintCommand(instruction_list, data)
        elif instruction_list[0] == 'pause':
            return PauseCommand(instruction_list, data)
        else:
            return UnknownCommand(instruction_list, data)

class TypeField(object):
    def __init__(self, instruction, data):
        self.instruction = instruction
        self.data = data
        self.has_tab = False
        self.value_to_print = ''
        self.instruction_length = 0

    def _set_field(self, value, length):
        if length is not None:
            if len(value) < length:
                self.value_to_print = value
                self.has_tab = True
            elif len(value) > length:
                self.value_to_print = value[:length]
            else:
                self.value_to_print = value
        else:
            self.value_to_print = value

    def _set_length(self, instruction):
        if len(instruction) == 3:
            self.instruction_length = int(instruction[2])
        else:
            self.instruction_length = None

    def _print_value(self):
        pyautogui.typewrite(self.value_to_print)

    def _add_tab(self):
        if self.has_tab:
            pyautogui.press('tab')


class PrintCommand(TypeField):
    def __init__(self, instruction, data):
        TypeField.__init__(self, instruction, data)
        self.name = 'PrintCommand'

        self._set_input__print_value(instruction)
        self._set_length(instruction)
        self._set_field(self.input_value_to_print, self.instruction_length)

    def _set_input__print_value(self, instruction):
        self.input_value_to_print = instruction[1]

    def execute(self):
        self._print_value()
        self._add_tab()


class InputCommand(TypeField):
    def __init__(self, instruction, data):
        TypeField.__init__(self, instruction, data)
        self.data_set = data
        self.name = 'InputCommand'

        self.set_input__print_value(instruction)
        self._set_length(instruction)
        self._set_field(self.input_value_to_print, self.instruction_length)

    def set_input__print_value(self, instruction):
        self.input_value_to_print = self.data_set.get(instruction[1])

    def execute(self):
        self._print_value()
        self._add_tab()


class PauseCommand(object):
    def __init__(self, instruction, data):
        self.instruction = instruction
        self.data_set = data
        self.pause_length = 0
        self.name = 'PauseCommand'

        self.set_pause()

    def set_pause(self):
        if len(self.instruction) == 1:
            self.pause_length = 1
        else:
            self.pause_length = int(self.instruction[1])

    def execute(self):
        for pause in range(0, self.pause_length):
            sleep(1)


class PressCommand(object):
    def __init__(self, instruction, data):
        self.instruction = instruction
        self.data_set = data
        self.keys = self.instruction[1]

        if len(instruction) == 3:
            self.presses = int(self.instruction[2])
        else:
            self.presses = 1

        self.name = 'PressCommand'

    def execute(self):
        for press in range(0, self.presses):
            if not isinstance(self.keys, list):
                pyautogui.press(self.keys)
            elif len(self.keys) == 2:
                pyautogui.hotkey(self.keys[0], self.keys[1])
            elif len(self.keys) == 3:
                pyautogui.hotkey(self.keys[0], self.keys[1], self.keys[2])
            elif len(self.keys) == 4:
                pyautogui.hotkey(self.keys[0], self.keys[1], self.keys[2],
                                 self.keys[4])
            elif len(self.keys) == 5:
                pyautogui.hotkey(self.keys[0], self.keys[1], self.keys[2],
                                 self.keys[3], self.keys[4])


class UnknownCommand(object):
    def __init__(self, instruction, data):
        self.instruction = instruction
        self.data_set = data
        self.name = 'UnknownCommand'

    def execute(self):
        pass


class ProcedureCommander(object):
    """
    This Command object iterates through the list of
    command objects and calls their execute command.
    """
    def __init__(self, procedure_set):
        self.procedure_set = procedure_set

    def execute(self):
        for command in self.procedure_set:
            command.execute()


if __name__ == "__main__":
    procedure = argv[1]
    if len(argv) > 2:
        data_set = argv[2]
    else:
        data_set = None

    pynputter = Pynputter(procedure, data_set)
    pynputter()
