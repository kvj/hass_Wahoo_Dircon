from .dircon.client import DirconTcpClient

import logging
_LOGGER = logging.getLogger(__name__)

async def async_fetch_capabilities(host: str, port: int) -> dict | None:
    client = DirconTcpClient(host, port)
    result = {"speed": True} # Always supported

    def _parse_features(chr, data, op):
        if chr == 0x2acc:
            flag = int.from_bytes(data[:2], "little")
            flag_mapping = {
                1:  "cadence",
                2:  "distance",
                3:  "incline",
                10: "hrm",
                12: "time",
            }
            _LOGGER.debug(f"_parse_features() FTMS features flag: 0x{flag:x}")
            for key, value in flag_mapping.items():
                if flag & (1 << key) != 0:
                    _LOGGER.debug(f"_parse_features() FTMS feature: {value}")
                    result[value] = True
            flag = int.from_bytes(data[4:6], "little")
            flag_mapping = {
                0: "speed_set",
                1: "incline_set",
            }
            _LOGGER.debug(f"_parse_features() FTMS control features flag: 0x{flag:x}")
            for key, value in flag_mapping.items():
                if flag & (1 << key) != 0:
                    _LOGGER.debug(f"_parse_features() FTMS control feature: {value}")
                    result[value] = True
        if chr == 0x2a54:
            flag = int.from_bytes(data[:2], "little")
            flag_mapping = {
                0: "stride",
                1: "distance",
            }
            _LOGGER.debug(f"_parse_features() RSC features flag: 0x{flag:x}")
            for key, value in flag_mapping.items():
                if flag & (1 << key) != 0:
                    _LOGGER.debug(f"_parse_features() RSC feature: {value}")
                    result[value] = True

    client.add_chr_listener(_parse_features)

    run_result = await client.async_run([0x2acc, 0x2ad3, 0x2a54], [], False)
    return result if run_result else None

def prepare_data_client(host: str, port: int, callback) -> dict | None:
    client = DirconTcpClient(host, port)
    metric_src = {}

    def _parse_data(chr, data, op):
        result = {}
        if chr == 0x2acd:
            # 08:01:64:00:00:00:00:00:00
            flag = int.from_bytes(data[:2], "little")
            index = 2
            if flag & 1 == 0:
                result["speed"] = int.from_bytes(data[index:index+2], "little") / 100.0 # Km/h
                index += 2;
            if flag & (1 << 1): 
                index += 2
            if flag & (1 << 2):
                result["distance"] =  int.from_bytes(data[index:index+3], "little") # Meters
                index += 3
            if flag & (1 << 3):
                result["incline"] = int.from_bytes(data[index:index+2], "little") / 10.0 # % * 10
                index += 4
            if flag & (1 << 4):
                index += 4
            if flag & (1 << 5):
                index += 1
            if flag & (1 << 6):
                index += 1
            if flag & (1 << 7):
                index += 5
            if flag & (1 << 8):
                result["hrm"] = data[index] # Bpm
                index += 1
            if flag & (1 << 9):
                index += 1
            if flag & (1 << 10):
                result["time"] = int.from_bytes(data[index:index+2], "little") # Sec
                index += 2
            _LOGGER.debug(f"_parse_data() FTMS = {result}")
        if chr == 0x2a53:
            # 02:87:00:00:24:07:00:00
            flag = data[0]
            # TODO: How to be flexible?
            if metric_src.get("speed") != 0x2acd: # Only report if FTMS metric isn't available
                result["speed"] = int.from_bytes(data[1:3], "little") * 360 / 25600.0 # Km/h
            result["cadence"] = data[3] * 2 # Running - double

            index = 4
            if flag & 1:
                result["stride"] = int.from_bytes(data[index:index+2], "little") # Cm
                index += 2;
            if flag & (1 << 1): 
                if metric_src.get("distance") != 0x2acd: # Only report if FTMS metric isn't available
                    result["distance"] = int.from_bytes(data[index:index+4], "little") / 10.0 # dcm * 10
            _LOGGER.debug(f"_parse_data() RS = {result}")
        for key in result:
            metric_src[key] = chr # Save where metrics came
        if len(result):
            callback(result)
        

    client.add_chr_listener(_parse_data)

    return client

async def run_data_client(client: DirconTcpClient):
    return await client.async_run([0x2acc, 0x2ad3, 0x2a54], [0x2acd, 0x2ada, 0x2a53, 0x2ad3], True)

async def write_data_client(client: DirconTcpClient, field: int, value: float) -> bool:
    if field == "speed":
        data = [0x02]
        data.extend(int(value * 100).to_bytes(2, "little"))
        resp = await client.async_write(0x2ad9, bytes(data))
        return True
    if field == "incline":
        data = [0x03]
        data.extend(int(value * 10).to_bytes(2, "little"))
        resp = await client.async_write(0x2ad9, bytes(data))
        return True
    return False
