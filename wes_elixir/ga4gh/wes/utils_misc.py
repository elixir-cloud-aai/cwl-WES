from json import decoder, loads


def immutable_multi_dict_to_nested_dict(multi_dict):
    '''Convert ImmutableMultiDict to nested dictionary'''

    # Convert ImmutableMultiDict to flat dictionary
    nested_dict = multi_dict.to_dict(flat=True)

    # Iterate over key in dictionary
    for key in nested_dict:

        # Try to decode JSON string; ignore JSONDecodeErrors
        try:
            nested_dict[key] = loads(nested_dict[key])

        except decoder.JSONDecodeError:
            pass

    # Return formatted request dictionary
    return nested_dict