################################################################################
#                                                                              #
#  __  __ _____ ____   ____                 _                                  #
# |  \/  |  ___|  _ \ / ___| __ _ _ __ ___ (_)_ __   __ _                      #
# | |\/| | |_  | | | | |  _ / _` | '_ ` _ \| | '_ \ / _` |                     #
# | |  | |  _| | |_| | |_| | (_| | | | | | | | | | | (_| |                     #
# |_|  |_|_|   |____/ \____|\__,_|_| |_| |_|_|_| |_|\__, |                     #
#                                                    |___/                     #
# Copyright 2021 MFDGaming                                                     #
#                                                                              #
# Permission is hereby granted, free of charge, to any person                  #
# obtaining a copy of this software and associated documentation               #
# files (the "Software"), to deal in the Software without restriction,         #
# including without limitation the rights to use, copy, modify, merge,         #
# publish, distribute, sublicense, and/or sell copies of the Software,         #
# and to permit persons to whom the Software is furnished to do so,            #
# subject to the following conditions:                                         #
#                                                                              #
# The above copyright notice and this permission notice shall be included      #
# in all copies or substantial portions of the Software.                       #
#                                                                              #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR   #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,     #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE  #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER       #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING      #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS #
# IN THE SOFTWARE.                                                             #
#                                                                              #
################################################################################

from binary_utils.binary_converter import binary_converter
from nbt_utils.constant.tag_ids import tag_ids
from nbt_utils.tag.byte_tag import byte_tag
from nbt_utils.tag.byte_array_tag import byte_array_tag
from nbt_utils.tag.compound_tag import compound_tag
from nbt_utils.tag.int_tag import int_tag
from nbt_utils.tag.int_array_tag import int_array_tag
from nbt_utils.tag.list_tag import list_tag
from nbt_utils.tag.long_tag import long_tag
from nbt_utils.tag.string_tag import string_tag
from nbt_utils.utils.nbt_le_binary_stream import nbt_le_binary_stream
import os
from pi_world.chunk import chunk
from pi_world.utils import utils
import random
import sys
import time

class world:
    def __init__(self, world_dir: str) -> None:
        self.world_dir: str = os.path.abspath(world_dir)
        self.chunks_path: str = os.path.join(self.world_dir, "chunks.dat")
        self.options_path: str = os.path.join(self.world_dir, "level.dat")
        self.entities_path: str = os.path.join(self.world_dir, "entities.dat")
        if not os.path.isdir(self.world_dir):
            os.mkdir(self.world_dir)
        if not os.path.isfile(self.options_path):
            self.create_options_file()
        if not os.path.isfile(self.entities_path):
            self.create_entities_file()
        if not os.path.isfile(self.chunks_path):
            file: object = open(self.chunks_path, "wb")
            file.write(b"\x00" * 4096)

    @staticmethod
    def get_location(x: int, z: int) -> int:
        return 4 * ((x & 31) + (z & 31) * 32)

    def get_chunk(self, x: int, z: int) -> object:
        i_chunk: object = chunk(x, z)
        file: object = open(self.chunks_path, "rb")
        index_location: int = world.get_location(x, z)
        file.seek(index_location)
        sector_count: int = binary_converter.read_unsigned_byte(file.read(1))
        offset: int = binary_converter.read_unsigned_triad_le(file.read(3))
        if sector_count == 0 and offset == 0:
            return i_chunk
        file.seek(offset << 12)
        length: int = binary_converter.read_unsigned_int_le(file.read(4))
        chunk_data: bytes = file.read(length - 4)
        file.close()
        i_chunk.deserialize(chunk_data)
        return i_chunk

    def set_chunk(self, i_chunk: object) -> None:
        chunk_data: bytes = i_chunk.serialize()
        file: object = open(self.chunks_path, "r+b")
        ccc: bytes = binary_converter.write_unsigned_int_le(len(chunk_data) + 4)
        ccc += chunk_data
        size: int = 0
        while True:
            remaining: int = size - len(ccc)
            if remaining > 0:
                ccc += b"\x00" * remaining
                break
            size += 4096
        index_location: int = world.get_location(i_chunk.x, i_chunk.z)
        index_location_data: bytes = b""
        chunks_data: bytes = b""
        offset: int = 1
        for i in range(0, 1024):
            if i == (index_location >> 2):
                sector_count: int = len(ccc) >> 12
                index_location_data += binary_converter.write_unsigned_byte(sector_count)
                index_location_data += binary_converter.write_unsigned_triad_le(offset)
                chunks_data += ccc
                offset += sector_count
            else:
                file.seek(i << 2)
                sector_count: int = binary_converter.read_unsigned_byte(file.read(1))
                chunk_offset: int = binary_converter.read_unsigned_triad_le(file.read(3))
                if sector_count > 0 and chunk_offset > 0:
                    index_location_data += binary_converter.write_unsigned_byte(sector_count)
                    index_location_data += binary_converter.write_unsigned_triad_le(offset)
                    offset += sector_count
                    file.seek(chunk_offset << 12)
                    chunks_data += file.read(sector_count << 12)
                else:
                    index_location_data += b"\x00" * 4
        file.seek(0)
        file.write(index_location_data + chunks_data)
        file.close()

    def create_options_file(self) -> None:
        stream: object = nbt_le_binary_stream()
        tag: object = compound_tag("", [
            int_tag("GameType", 0),
            long_tag("LastPlayed", int(time.time() * 1000)),
            string_tag("LevelName", "world"),
            int_tag("Platform", 2),
            long_tag("RandomSeed", random.randint(0, sys.maxsize)),
            long_tag("SizeOnDisk", 0),
            int_tag("SpawnX", 256),
            int_tag("SpawnY", 70),
            int_tag("SpawnZ", 256),
            int_tag("StorageVersion", 3),
            long_tag("Time", 0),
            long_tag("dayCycleStopTime", 0),
            int_tag("spawnMobs", 0)
        ])
        stream.write_root_tag(tag)
        result: bytes = b""
        result += binary_converter.write_unsigned_int_le(3)
        result += binary_converter.write_unsigned_int_le(len(stream.data))
        result += stream.data
        file: object = open(self.options_path, "wb")
        file.write(result)
        file.close()

    def create_entities_file(self) -> None:
        stream: object = nbt_le_binary_stream()
        tag: object = compound_tag("", [
            list_tag("Entities", []),
            list_tag("TileEntities", [])
        ])
        stream.write_root_tag(tag)
        result: bytes = b"ENT\x00"
        result += binary_converter.write_unsigned_int_le(1)
        result += binary_converter.write_unsigned_int_le(len(stream.data))
        result += stream.data
        file: object = open(self.entities_path, "wb")
        file.write(result)
        file.close()
