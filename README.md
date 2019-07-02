# pystream
stream load and dump by struct

# quick start

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
