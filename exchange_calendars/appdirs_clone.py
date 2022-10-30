# Clone of 'appdirs' module user_cache_dir() functionality: https://github.com/ActiveState/appdirs
# Copyright (c) 2005-2010 ActiveState Software Inc.
# Copyright (c) 2013 Eddy Petrișor

import os
import sys

PY3 = sys.version_info[0] == 3

if PY3:
    unicode = str

if sys.platform.startswith('java'):
    import platform
    os_name = platform.java_ver()[3][0]
    if os_name.startswith('Windows'):  # "Windows XP", "Windows 7", etc.
        system = 'win32'
    elif os_name.startswith('Mac'):  # "Mac OS X", etc.
        system = 'darwin'
    else:  # "Linux", "SunOS", "FreeBSD", etc.
        # Setting this to "linux2" is not ideal, but only Windows or Mac
        # are actually checked for and the rest of the module expects
        # *sys.platform* style strings.
        system = 'linux2'
else:
    system = sys.platform


def _get_win_folder_from_registry(csidl_name):
    """This is a fallback technique at best. I'm not sure if using the
    registry for this guarantees us the correct answer for all CSIDL_*
    names.
    """
    if PY3:
        import winreg as _winreg
    else:
        import _winreg

    shell_folder_name = {
        "CSIDL_APPDATA": "AppData",
        "CSIDL_COMMON_APPDATA": "Common AppData",
        "CSIDL_LOCAL_APPDATA": "Local AppData",
    }[csidl_name]

    key = _winreg.OpenKey(
        _winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
    )
    dir, type = _winreg.QueryValueEx(key, shell_folder_name)
    return dir


def _get_win_folder_with_ctypes(csidl_name):
    import ctypes

    csidl_const = {
        "CSIDL_APPDATA": 26,
        "CSIDL_COMMON_APPDATA": 35,
        "CSIDL_LOCAL_APPDATA": 28,
    }[csidl_name]

    buf = ctypes.create_unicode_buffer(1024)
    ctypes.windll.shell32.SHGetFolderPathW(None, csidl_const, None, 0, buf)

    # Downgrade to short path name if have highbit chars. See
    # <http://bugs.activestate.com/show_bug.cgi?id=85099>.
    has_high_char = False
    for c in buf:
        if ord(c) > 255:
            has_high_char = True
            break
    if has_high_char:
        buf2 = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(buf.value, buf2, 1024):
            buf = buf2

    return buf.value


def _get_win_folder_with_jna(csidl_name):
    import array
    from com.sun import jna
    from com.sun.jna.platform import win32

    buf_size = win32.WinDef.MAX_PATH * 2
    buf = array.zeros('c', buf_size)
    shell = win32.Shell32.INSTANCE
    shell.SHGetFolderPath(None, getattr(win32.ShlObj, csidl_name), None, win32.ShlObj.SHGFP_TYPE_CURRENT, buf)
    dir = jna.Native.toString(buf.tostring()).rstrip("\0")

    # Downgrade to short path name if have highbit chars. See
    # <http://bugs.activestate.com/show_bug.cgi?id=85099>.
    has_high_char = False
    for c in dir:
        if ord(c) > 255:
            has_high_char = True
            break
    if has_high_char:
        buf = array.zeros('c', buf_size)
        kernel = win32.Kernel32.INSTANCE
        if kernel.GetShortPathName(dir, buf, buf_size):
            dir = jna.Native.toString(buf.tostring()).rstrip("\0")

    return dir


def _get_win_folder_from_environ(csidl_name):
    env_var_name = {
        "CSIDL_APPDATA": "APPDATA",
        "CSIDL_COMMON_APPDATA": "ALLUSERSPROFILE",
        "CSIDL_LOCAL_APPDATA": "LOCALAPPDATA",
    }[csidl_name]

    return os.environ[env_var_name]


if system == "win32":
    try:
        from ctypes import windll
    except ImportError:
        try:
            import com.sun.jna
        except ImportError:
            try:
                if PY3:
                    import winreg as _winreg
                else:
                    import _winreg
            except ImportError:
                _get_win_folder = _get_win_folder_from_environ
            else:
                _get_win_folder = _get_win_folder_from_registry
        else:
            _get_win_folder = _get_win_folder_with_jna
    else:
        _get_win_folder = _get_win_folder_with_ctypes


def _user_cache_dir():
    # Copied from 'appdirs' module to avoid adding as dependency
    if system == "win32":
        path = os.path.normpath(_get_win_folder("CSIDL_LOCAL_APPDATA"))
    elif system == 'darwin':
        path = os.path.expanduser('~/Library/Caches')
    else:
        path = os.getenv('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
    return path
