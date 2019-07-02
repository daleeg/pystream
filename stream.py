#!/usr/bin/env python
# -*- coding: utf-8 -*-
from functools import lru_cache
import oyaml as yaml
import struct
from collections import OrderedDict
import logging

__all__ = ["dump", "load"]

LOG = logging.getLogger(__name__)
type_map = {
    "char": "c",
    "bool": "?",
    "uint8": "B",
    "int8": "b",
    "int16": "h",
    "uint16": "H",
    "int32": "i",
    "uinit32": "I",
    "int64": "q",
    "uinit64": "Q",
    "float": "f",
    "double": "D",
    "string": "s"
}

LITTLE_ENDIAN = "little"
BIG_ENDIAN = "big"


class ParserError(Exception):
    pass


def gen_format(type_list, endian=LITTLE_ENDIAN):
    _fmt = ""
    _types = []
    if endian == LITTLE_ENDIAN:
        _fmt += "<"
    elif endian == BIG_ENDIAN:
        _fmt += ">"
    else:
        raise ParserError("bad endian")

    for _type in type_list:
        if _type in type_map:
            _fmt += type_map[_type]
            _types.append((_type, 1))
        else:
            _type = _type.replace("]", "")
            inner_type, count = _type.split("[")
            if inner_type == "char":
                inner_type = "string"
            count = int(count)
            _fmt += "{}{}".format(count, type_map[inner_type])
            _types.append((inner_type, count))
    return _fmt, _types


@lru_cache(maxsize=None)
def yaml_load(stream):
    return yaml.load(stream)


@lru_cache(maxsize=None)
def struct_parser(_struct):
    struct_info = yaml_load(_struct)
    for k, value in struct_info.items():
        _struct_name = k
        _struct_var = []
        _struct_type = []
        for var, _type in value.items():
            _struct_var.append(var)
            _struct_type.append(_type)
        _fmt, _types = gen_format(_struct_type)
        LOG.debug(_struct_name)
        LOG.debug(_struct_var)
        LOG.debug(_types)
        LOG.debug(_fmt)
        return _struct_name, _struct_var, _types, _fmt
    raise ParserError("bad yaml")


class Result(object):
    def __init__(self, name, _data):
        self._name = name
        self._data = _data

    def __getattr__(self, attr):
        if attr not in self.__dict__:
            return self._data.get(attr, None)
        return self.__dict__[attr]

    @property
    def data(self):
        return self._data

    def __repr__(self):
        r = "{}:\n".format(self._name)
        for k, v in self._data.items():
            r += "    {}: {}\n".format(k, v)
        return r


@lru_cache(maxsize=None)
def gen_result_cls(name):
    return type(name.title(), (Result,), {})


def load(stream, _struct):
    name, vars, _types, _fmt = struct_parser(_struct)
    result_list = struct.unpack(_fmt, stream)
    result = OrderedDict()
    for i, key in enumerate(vars):
        value = result_list[i]
        if _types[i][0] in ["char", "string"]:
            value = value.rstrip(b'\x00').decode()
        result[key] = value
    cls = gen_result_cls(name)
    return cls(name=name, _data=result)


def dump(result, _struct):
    if isinstance(result, Result):
        data = result.data
    else:
        data = result
    data_list = []
    _, vars, _types, _fmt = struct_parser(_struct)
    for i, var in enumerate(vars):
        value = data[var]
        if not isinstance(value, list):
            if _types[i][0] in ["char", "string"]:
                data_list.append(value.encode())
            else:
                data_list.append(value)
        else:
            value = data[var]
            if _types[i][1] != len(value):
                raise ParserError("bad data")

            data_list.extend(data[var])
    return struct.pack(_fmt, *data_list)


if __name__ == '__main__':
    command = """
    Command:
        cmd: char[5]
        param: string[8]
        code: int32
        is_active: bool
        nums: int64[4]
    """

    result = OrderedDict(cmd="open", param="hello", code=14001, is_active=True, nums=[11, 22, 33, 44])

    stream = dump(result, command)
    print(stream)
    result = load(stream, command)
    print(result)
