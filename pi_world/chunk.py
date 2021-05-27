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

from pi_world.utils import utils

class chunk:
    def __init__(self, x: int, z: int, blocks: list = [], data: list = [], sky_light: list = [], block_light: list = [], biomes: list = []) -> None:
        self.x: int = x
        self.z: int = z
        if len(blocks) == 32768:
            self.blocks: list = blocks
        else:
            self.blocks: list = [0] * 32768
        if len(data) == 16384:
            self.data: list = data
        else:
            self.data: list = [0] * 16384
        if len(sky_light) == 16384:
            self.sky_light: list = sky_light
        else:
            self.sky_light: list = [255] * 16384
        if len(block_light) == 16384:
            self.block_light: list = block_light
        else:
            self.block_light: list = [0] * 16384
        if len(biomes) == 256:
            self.biomes: list = biomes
        else:
            self.biomes: list = [0] * 256

    @staticmethod
    def get_index(x: int, y: int, z: int) -> int:
        return (x << 11) + (z << 7) + y

    @staticmethod
    def get_biome_index(x: int, z: int) -> int:
        return (z << 4) + x

    def get_block(self, x: int, y: int, z: int) -> int:
        return self.blocks[chunk.get_index(x, y, z)]

    def set_block(self, x: int, y: int, z: int, block_id: int) -> None:
        self.blocks[chunk.get_index(x, y, z)] = block_id

    def get_data(self, x: int, y: int, z: int) -> int:
        return utils.nibble_4(self.data, chunk.get_index(x, y, z))

    def set_data(self, x: int, y: int, z: int, data: int) -> None:
        utils.set_nibble_4(self.data, chunk.get_index(x, y, z), data)

    def get_sky_light(self, x: int, y: int, z: int) -> int:
        return utils.nibble_4(self.sky_light, chunk.get_index(x, y, z))

    def set_sky_light(self, x: int, y: int, z: int, light_level: int) -> None:
        utils.set_nibble_4(self.sky_light, chunk.get_index(x, y, z), light_level)

    def get_block_light(self, x: int, y: int, z: int) -> int:
        return utils.nibble_4(self.block_light, chunk.get_index(x, y, z))

    def set_block_light(self, x: int, y: int, z: int, light_level: int) -> None:
        utils.set_nibble_4(self.block_light, chunk.get_index(x, y, z), light_level)

    def get_biome(self, x: int, z: int) -> int:
        return self.biomes[chunk.get_biome_index(x, z)]

    def set_biome(self, x: int, z: int, biome: int) -> None:
        self.biomes[chunk.get_biome_index(x, z)] = biome

    def serialize(self) -> bytes:
        return bytes(self.blocks) + bytes(self.data) + bytes(self.sky_light) + bytes(self.block_light) + bytes(self.biomes)

    def deserialize(self, chunk_data: bytes) -> None:
        self.blocks: list = list(chunk_data[0:32768])
        self.data: list = list(chunk_data[32768:32768 + 16384])
        self.sky_light: list = list(chunk_data[49152:49152 + 16384])
        self.block_light: list = list(chunk_data[65536:65536 + 16384])
        self.biomes: list = list(chunk_data[81920:81920 + 256])

    def network_serialize(self) -> bytes:
        result: bytes = b""
        for z in range(0, 16):
            for x in range(0, 16):
                result += b"\xff"
                for k in range(0, 8):
                    index: int = chunk.get_index(x, (k << 4), z)
                    result += bytes(self.blocks[index:index + 16])
                    result += bytes(self.data[(index >> 1):(index >> 1) + 8])
        return result
