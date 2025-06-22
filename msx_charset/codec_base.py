import codecs

PRINTABLE_OR_USEFUL_CTRL = (
    '\x00'  # NUL
    '\x07'  # BEL
    '\x08'  # BS
    '\x09'  # TAB
    '\x0A'  # LF
    '\x0B'  # VT
    '\x0C'  # FF
    '\x0D'  # CR
    '\x1B'  # ESC
    '\x20'  # SPACE
    '\x7F'  # DEL
)


class MSXCodecBase:
    """Base class for MSX character set codecs"""

    def __init__(self, name, custom_map, graphic_map):
        self.name = name

        # ASCII (0x00-0x7F) range mapping
        self.ascii_map = {
            i: chr(i) for i in range(0x80)
            if chr(i).isprintable() or chr(i) in PRINTABLE_OR_USEFUL_CTRL
        }

        # Character mappings
        self.char_map = {**self.ascii_map, **custom_map}
        self.char_reverse_map = {v: k for k, v in self.char_map.items()}
        self.graphic_map = graphic_map
        self.graphic_reverse_map = {v: k for k, v in graphic_map.items()}

        # Create codec info
        self.codec_info = codecs.CodecInfo(
            name=name,
            encode=self.encode,
            decode=self.decode
        )

    def encode(self, text, errors='strict'):
        """Convert UTF-8 string to MSX code byte sequence"""
        result = bytearray()
        for char in text:
            if char in self.graphic_map:
                result.extend(self.graphic_map[char])
            else:
                result.append(self.char_reverse_map.get(char, 0x3F))
        return bytes(result), len(text)

    def _decode_internal(self, codes, allow_incomplete=False):
        """Convert MSX code byte sequence to UTF-8 string"""
        result = []
        i = 0
        codes_len = len(codes)

        while i < codes_len:
            code = codes[i]

            # Handle graphic characters
            if code == 0x01:
                if i + 1 >= codes_len:
                    if allow_incomplete:
                        break
                    else:
                        result.append('?')
                        i += 1
                        continue
                next_code = codes[i + 1]
                char = self.graphic_reverse_map.get((code, next_code), '?')
                result.append(char)
                i += 2
                continue

            result.append(self.char_map.get(code, '?'))
            i += 1

        return ''.join(result), i

    def decode(self, codes, errors='strict'):
        """Convert MSX code byte sequence to UTF-8 string"""
        decoded, consumed = self._decode_internal(codes, allow_incomplete=False)
        return decoded, consumed


class MSXIncrementalDecoder(codecs.IncrementalDecoder):
    def __init__(self, codec, errors="strict"):
        super().__init__(errors)
        self.buffer = bytearray()
        self.codec = codec

    def decode(self, input, final=False):
        self.buffer.extend(input)
        decoded, consumed = self.codec._decode_internal(
            self.buffer, allow_incomplete=not final
        )
        self.buffer = self.buffer[consumed:]
        return decoded



class MSXStreamReader(codecs.StreamReader):
    def __init__(self, codec_info):
        self.codec_info = codec_info

    def decode(self, input, final=False):
        return self.codec_info.decode(input, errors='strict')[0]

    def reset(self):
        pass


class MSXStreamWriter(codecs.StreamWriter):
    def __init__(self, codec_info):
        self.codec_info = codec_info

    def encode(self, input, final=False):
        return self.codec_info.encode(input, errors='strict')[0]

    def reset(self):
        pass
