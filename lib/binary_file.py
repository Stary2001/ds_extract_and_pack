import os
import re


class BinaryFile:
    def __init__(self, file, path, base_dir=None):
        self.file = file
        self.path = path
        self.endian = "little"
        self.base_dir = base_dir or os.path.dirname(path)

    def write(self, *args):
        for arg in args:
            self.file.write(arg)

    def write_header(self, manifest):
        self.write(*manifest['header'].values())

    def read(self, num_bytes):
        return self.file.read(num_bytes)

    def consume(self, expected_bytes, num_to_read=None):
        if num_to_read:
            expected_bytes = expected_bytes.to_bytes(num_to_read, self.endian)
        else:
            num_to_read = len(expected_bytes)
        actual_bytes = self.read(num_to_read)
        if actual_bytes != expected_bytes:
            raise ValueError("Expected {}, got {}".format(expected_bytes, actual_bytes))
        return actual_bytes

    def read_null_terminated_string(self):
        buffer = b""
        while True:
            byte = self.read(1)
            if byte == b'' or byte == b'\x00':
                break
            buffer += byte
        try:
            return buffer.decode("shift_jis")
        except UnicodeDecodeError as e:
            self.log("Failed to decode {}".format(buffer), 1)
            raise e

    def normalize_filepath(self, path):
        if path.lower().startswith("n:\\"):
            path = path[3:]

        path = path.lstrip("\\").replace("\\", "/")
        path = os.path.join(self.base_dir, path)

        # Flatten directory structure
        path = re.sub(r"((?:[^/]+/)+)FRPG/data/(Model|INTERROOT_win32)/(?:param/)?\1", r"\1", path)
        path = re.sub(r"([^/]+)/FRPG/data/Msg/Data_\1/win32", r"\1", path)
        path = re.sub(r"FRPG/Source/Shader/([^/]*)/WIN32", r"\1", path)
        path = re.sub(r"FRPG/data/Other/Rumble/", "", path)

        return os.path.normpath(path.replace("/", os.sep))

    def int32_bytes(self, i):
        return i.to_bytes(4, byteorder=self.endian)

    def to_int32(self, b):
        return int.from_bytes(b, byteorder=self.endian, signed=False)

    def log(self, msg, depth):
        prefix = ""
        if depth > 1:
            prefix += ("  " * depth) + "|- "
        prefix += self.__class__.__name__.replace("File", "")
        prefix += "(offset=" + str(self.file.tell()) + "): "
        print(prefix + msg)