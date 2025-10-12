"""Тестирование библиотеки."""

from importlib import import_module

from readme_generator.objects.module import ModuleParser
from readme_generator.objects.objects import ObjectParser

module = ModuleParser(import_module('test_module'))
processed_objects: list[ObjectParser] = [module]
while processed_objects:
    processed_object = processed_objects.pop()
    for class_item in processed_object.classes:
        print(class_item)
        processed_objects.append(class_item)
    for function in processed_object.functions:
        print(function)
        processed_objects.append(function)
