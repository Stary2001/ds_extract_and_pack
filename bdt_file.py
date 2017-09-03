import io
from binary_file import BinaryFile
from bhd5_file import BHD5File
from dcx_file import DCXFile


class BDTFile(BinaryFile):
    MAGIC_HEADER = b"BDF307D7R6"

    def extract_file(self):
        print("BDT: Reading file {}".format(self.path))

        bhd5_file = open(self.file.name.replace(".bdt", ".bhd5"), "rb")
        manifest = BHD5File(bhd5_file, bhd5_file).extract_file()
        self.consume(self.MAGIC_HEADER)
        self.consume(0x0, 6)

        for bin_data in manifest['bins']:
            for record_data in bin_data['records']:
                self.file.seek(self.to_int32(record_data['header']['record_offset']))
                data = self.read(self.to_int32(record_data['header']['record_size']))
                filepath = self.normalize_filepath(record_data['record_name'])
                record_data['actual_filename'] = filepath
                print("BDT: extracting {}".format(filepath))
                if data.startswith(DCXFile.MAGIC_HEADER):
                    with io.BytesIO(data) as dcx_buffer:
                        record_data['dcx'] = DCXFile(dcx_buffer, filepath).extract_file()
                else:
                    self.write_data(filepath, data)

        self.file.close()
        return manifest

    def create_file(self, manifest):
        print("BDT: Writing file {}".format(self.path))

        self.write(self.MAGIC_HEADER)
        self.write(bytearray(6))

        for bin_data in manifest['bins']:
            bin_data['header']['offset'] = self.int32_bytes(self.file.tell())
            for record_data in bin_data['records']:
                cur_position = self.file.tell()
                record_data['header']['record_offset'] = self.int32_bytes(cur_position)
                print("BDT: Writing data for {}".format(record_data['actual_filename']))
                if "dcx" in record_data:
                    with io.BytesIO() as dcx_buffer:
                        DCXFile(dcx_buffer, record_data['actual_filename']).create_file(record_data['dcx'])
                        dcx_buffer.seek(0)
                        self.write(dcx_buffer.read())
                else:
                    self.write(open(record_data['actual_filename'], "rb").read())
                data_size = self.file.tell() - cur_position
                record_data['header']['record_size'] = self.int32_bytes(data_size)

        self.file.close()

        bhd5_file = self.path.replace(".bdt", ".bhd5")
        BHD5File(open(bhd5_file, "wb"), bhd5_file).create_file(manifest)
