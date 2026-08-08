"""Read-only доступ к named file-mappings AC Evo через Win32 API.

Игра публикует три блока:
    Local\\acevo_pmf_physics   - обновляется каждый шаг физики
    Local\\acevo_pmf_graphics  - обновляется каждый кадр (HUD-rate)
    Local\\acevo_pmf_static    - пишется один раз при загрузке сессии

Важно: mmap.mmap(tagname=...) создаёт mapping, если его нет. Нам нужно
наоборот - честно обнаружить "игра не запущена", поэтому используем
OpenFileMappingW, который вернёт NULL c ERROR_FILE_NOT_FOUND (2).
"""

from __future__ import annotations

import ctypes
import sys

_FILE_MAP_READ = 0x0004

if sys.platform != "win32":
    raise OSError("AC Evo shared memory доступен только на Windows")

PHYSICS_TAG = r"Local\acevo_pmf_physics"
GRAPHICS_TAG = r"Local\acevo_pmf_graphics"
STATIC_TAG = r"Local\acevo_pmf_static"

PHYSICS_SIZE = 4096
GRAPHICS_SIZE = 8192
STATIC_SIZE = 2048

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_OpenFileMappingW = _kernel32.OpenFileMappingW
_OpenFileMappingW.argtypes = [ctypes.c_uint32, ctypes.c_int32, ctypes.c_wchar_p]
_OpenFileMappingW.restype = ctypes.c_void_p

_MapViewOfFile = _kernel32.MapViewOfFile
_MapViewOfFile.argtypes = [
    ctypes.c_void_p, ctypes.c_uint32,
    ctypes.c_uint32, ctypes.c_uint32, ctypes.c_size_t,
]
_MapViewOfFile.restype = ctypes.c_void_p

_UnmapViewOfFile = _kernel32.UnmapViewOfFile
_UnmapViewOfFile.argtypes = [ctypes.c_void_p]
_UnmapViewOfFile.restype = ctypes.c_int32

_CloseHandle = _kernel32.CloseHandle
_CloseHandle.argtypes = [ctypes.c_void_p]
_CloseHandle.restype = ctypes.c_int32


class NamedMapping:
    def __init__(self, name: str, size: int) -> None:
        handle = _OpenFileMappingW(_FILE_MAP_READ, False, name)
        if not handle:
            err = ctypes.get_last_error()
            if err == 2:
                raise FileNotFoundError(f"shared memory не найден: {name}")
            raise OSError(err, ctypes.FormatError(err), name)
        view = _MapViewOfFile(handle, _FILE_MAP_READ, 0, 0, size)
        if not view:
            err = ctypes.get_last_error()
            _CloseHandle(handle)
            raise OSError(err, ctypes.FormatError(err), name)
        self._handle = handle
        self._view = view
        self._size = size

    def read(self) -> bytes:
        return ctypes.string_at(self._view, self._size)

    def close(self) -> None:
        if self._view:
            _UnmapViewOfFile(self._view)
            self._view = None
        if self._handle:
            _CloseHandle(self._handle)
            self._handle = None

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass


class AcevoReader:
    def __init__(self) -> None:
        self._physics: NamedMapping | None = None
        self._graphics: NamedMapping | None = None
        self._static: NamedMapping | None = None

    def open(self) -> None:
        self.close()
        self._physics = NamedMapping(PHYSICS_TAG, PHYSICS_SIZE)
        try:
            self._graphics = NamedMapping(GRAPHICS_TAG, GRAPHICS_SIZE)
            self._static = NamedMapping(STATIC_TAG, STATIC_SIZE)
        except OSError:
            self.close()
            raise

    def close(self) -> None:
        for mm in (self._physics, self._graphics, self._static):
            if mm is not None:
                mm.close()
        self._physics = self._graphics = self._static = None

    @property
    def is_open(self) -> bool:
        return self._physics is not None

    def read_physics(self) -> bytes:
        return self._physics.read()

    def read_graphics(self) -> bytes:
        return self._graphics.read()

    def read_static(self) -> bytes:
        return self._static.read()
