class CamelCaseMap:
    """
    This is a custom class that allows keys to be in camel case style by converting them from underscore style, which provides dictionary-like functionality.
    """

    def __init__(self):
        """
        Initialize data to an empty dictionary
        """
        self._data = {}

    def __getitem__(self, key):
        """
        Return the value corresponding to the key
        :param key:str
        :return:str, the value corresponding to the key
        >>> camelize_map = CamelCaseMap()
        >>> camelize_map['first_name'] = 'John'
        >>> camelize_map.__getitem__('first_name')
        'John'
        """
        return self._data[self._to_camel_case(key)]