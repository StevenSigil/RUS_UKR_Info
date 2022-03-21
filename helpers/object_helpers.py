def search_list_for_obj(lst: list, key: str, value: str):
    import re

    def testKeyInObj(k, obj):
        return bool(k in obj.keys())

    # match any value if none is passed - ie: search for obj's with 'key'
    if value == None:
        ret_lst = [el for el in lst if testKeyInObj(key, el)]
    else:
        ret_lst = [el for el in lst if testKeyInObj(key, el) and el[key] == value]

    if len(ret_lst) == 1:
        return ret_lst[0]
    print('\nFOUND MULTIPLE OR ZERO OBJECTS IN LIST!')
    return ret_lst
