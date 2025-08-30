
import os


def longPathCheck(the_path, update_path_if_long=True, return_islong=False):
    """Check for windows paths with lengths over 256 characters.
    
    Check if a path is longer than the maximum length allowed standardly on
    Windows computers. If the path exceeds the allowed length and 
    update_path_if_long and the OS is Windows the path will be prepended
    with the extended path chars.

    Args:
        the_path(str): the file path to check for length.
        update_path_if_long(bool)=True: if True the path will be updated to
            include the Windows extented path characters (\\?\).
    """
    is_windows = os.name == 'nt'
    is_over_256 = False
    new_path = the_path
    if len(the_path) > 255:
        is_over_256 = True
        if is_windows and update_path_if_long:
            # Don't add it twice
            if not the_path[:4] == '\\\\?\\':
                new_path = '\\\\?\\' + the_path
    if return_islong:
        return new_path, is_over_256
    else:
        return new_path
        