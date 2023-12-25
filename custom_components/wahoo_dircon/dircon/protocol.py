import logging

_LOGGER = logging.getLogger(__name__)

DPKT_MESSAGE_HEADER_LENGTH = 6

DPKT_CHAR_PROP_FLAG_READ = 0x01
DPKT_CHAR_PROP_FLAG_WRITE = 0x02
DPKT_CHAR_PROP_FLAG_NOTIFY = 0x04

DPKT_MSGID_ERROR = 0xFF
DPKT_MSGID_DISCOVER_SERVICES = 0x01
DPKT_MSGID_DISCOVER_CHARACTERISTICS = 0x02
DPKT_MSGID_READ_CHARACTERISTIC = 0x03
DPKT_MSGID_WRITE_CHARACTERISTIC = 0x04
DPKT_MSGID_ENABLE_CHARACTERISTIC_NOTIFICATIONS = 0x05
DPKT_MSGID_UNSOLICITED_CHARACTERISTIC_NOTIFICATION = 0x06

DPKT_RESPCODE_SUCCESS_REQUEST = 0x00
DPKT_RESPCODE_UNKNOWN_MESSAGE_TYPE = 0x01
DPKT_RESPCODE_UNEXPECTED_ERROR = 0x02
DPKT_RESPCODE_SERVICE_NOT_FOUND = 0x03
DPKT_RESPCODE_CHARACTERISTIC_NOT_FOUND = 0x04
DPKT_RESPCODE_CHARACTERISTIC_OPERATION_NOT_SUPPORTED = 0x05
DPKT_RESPCODE_CHARACTERISTIC_WRITE_FAILED = 0x06
DPKT_RESPCODE_UNKNOWN_PROTOCOL = 0x07

DPKT_PARSE_ERROR = -20
DPKT_PARSE_WAIT = -3

DPKT_UUID_SUFFIX = [0x00, 0x00, 0x10, 0x00, 0x80, 0x00, 0x00, 0x80, 0x5F, 0x9B, 0x34, 0xFB]

class DirconPacket:

    def __init__(self):
        super().__init__()
        self._version = 1

    def build(self, id: int, *, 
        seq: int, 
        code: int = DPKT_RESPCODE_SUCCESS_REQUEST, 
        uuids: list = [], 
        data: bytearray = [],
    ):
        self._id = id
        self._seq = seq
        self._code = code
        self._uuids = uuids
        self._data = data

        return self

    def serialize_request(self) -> bytearray:
        resp = bytearray([self._version, self._id, self._seq, self._code])
        if self._id == DPKT_MSGID_DISCOVER_SERVICES:
            resp.extend([0, 0]) # Length is 0
        if self._id in [DPKT_MSGID_DISCOVER_CHARACTERISTICS, DPKT_MSGID_READ_CHARACTERISTIC, DPKT_MSGID_ENABLE_CHARACTERISTIC_NOTIFICATIONS]:
            resp.extend((len(self._uuids) * 16).to_bytes(2, "big"))
            for uuid in self._uuids:
                resp.extend(uuid.to_bytes(4, "big"))
                resp.extend(DPKT_UUID_SUFFIX)
            
        if self._id == DPKT_MSGID_WRITE_CHARACTERISTIC:
            resp.extend((16 + len(self._data)).to_bytes(2, "big"))
            resp.extend(self._uuids[0].to_bytes(4, "big"))
            resp.extend(DPKT_UUID_SUFFIX)
            resp.extend(self._data)
        return resp

    def parse_response(self, header: bytes, body: bytes):
        self._version = header[0]
        self._id = header[1]
        self._seq = header[2]
        self._code = header[3]

        self._uuids = []
        self._data = []
        if self._code != DPKT_RESPCODE_SUCCESS_REQUEST:
            return self
        if self._id == DPKT_MSGID_DISCOVER_SERVICES:
            for i in range(int(len(body) / 16)):
                first_part = int.from_bytes(body[16*i:16*i+4], 'big')
                self._uuids.append(first_part)
            return self

        if self._id == DPKT_MSGID_DISCOVER_CHARACTERISTICS:
            for i in range(int((len(body) - 16) / 17)): # Skip Service UUID, then flag + UUID
                self._data.append(body[32 + 17*i])
                first_part = int.from_bytes(body[16 + 17*i:16 + 17*i+4], 'big')
                self._uuids.append(first_part)
            return self

        if self._id in [DPKT_MSGID_READ_CHARACTERISTIC, DPKT_MSGID_UNSOLICITED_CHARACTERISTIC_NOTIFICATION, DPKT_MSGID_WRITE_CHARACTERISTIC]:
            self._uuids.append(int.from_bytes(body[:4], "big"))
            self._data = body[16:]
            return self

        _LOGGER.warn(f"parse_response(): Unknown packet: Header: {header.hex(':')}")
        _LOGGER.warn(f"parse_response(): Unknown packet: Body:   {body.hex(':')}")
        return self

    def is_success(self):
        return self._code == DPKT_RESPCODE_SUCCESS_REQUEST
    

