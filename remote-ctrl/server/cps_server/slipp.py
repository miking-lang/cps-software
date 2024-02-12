"""
A Simple Line Packet Protocol (SLiPP).

A SLiPP packet is a JSON blob, which can contain almost anything except for
a specific delimiter shown in the code below.

The packet format follows this structure:
  {
    "op": <str>,
    "seq": <str>,
    "timestamp": <str>,
    "contents": <arbitrary JSON>
  }

This is then encoded as utf-8 and sent.
"""

import json
import time
from datetime import datetime, timezone

# TODO: Add HMAC to messages.
#import hashlib, hmac
#HMAC_KEY = b"super-secret"
#mac = hmac.HMAC(HMAC_KEY, msg=b"some data", digestmod=hashlib.sha256)

from typing import Optional, Tuple

# The end of a packet is specified by two "Windows new line's".
DELIMITER = b"\n\r\n\r"

SLIPP_TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f %Z"


class Packet:
    def __init__(self, op: str, contents: "json" = {}, seq: str = "", timestamp : Optional[str] = None):
        """
        If timestamp is none, take current time
        """
        self.op = op
        self.seq = seq
        self.timestamp = timestamp
        self.contents = contents

    def __bytes__(self):
        return self.encode()

    def __str__(self):
        return str(self.blob)

    def __repr__(self):
        return f"Packet<op=\"{self.op}\",seq=\"{self.seq}\",timestamp=\"{self.timestamp}\"|{self.contents}>"

    @property
    def blob(self):
        """Returns the JSON blob corresponding to this packet."""
        timestamp = self.timestamp
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).strftime(SLIPP_TIME_FORMAT)

        return {
            "op": self.op,
            "seq": self.seq,
            "timestamp": timestamp,
            "contents": self.contents,
        }

    @property
    def json(self):
        return self.blob

    def encode(self) -> bytes:
        """Returns a sequence of bytes with encoded packet"""
        return json.dumps(self.blob).encode("utf-8") + DELIMITER

    @property
    def timestamp_seconds(self):
        # Get the value of the timestamp in seconds (as with time.time())
        try:
            dt = datetime.strptime(self.timestamp, SLIPP_TIME_FORMAT)
            return dt.timestamp()
        except Exception:
            return None

    @classmethod
    def decode(cls, data: bytes) -> Tuple[Optional["Packet"], Optional[str], bytes]:
        """
        Decodes a packet from a sequence of bytes, returning a packet and what
        is left from the sequence of bytes.
        """
        idx = data.find(DELIMITER)
        if idx < 0:
            return (None, None, data)

        s = data[:idx].decode("utf-8")
        data = data[idx+len(DELIMITER):]

        inblob = {}
        try:
            inblob = json.loads(s)
        except Exception:
            return (None, f"Invalid JSON", data)

        for k in ["op", "seq", "timestamp", "contents"]:
            if k not in inblob:
                return (None, f"Missing {k} value", data)

        inpkt = cls(
            op=inblob["op"],
            seq=inblob["seq"],
            timestamp=inblob["timestamp"],
            contents=inblob["contents"],
        )

        return (inpkt, "", data)
