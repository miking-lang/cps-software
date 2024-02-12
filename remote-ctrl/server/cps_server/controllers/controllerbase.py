import inspect
import json
import time
import traceback

from .. import slipp

def register_command(registry, argtypes=[], kind="read"):
    def regfn(f):
        registry[f.__name__] = {
            "fn": f,
            "argtypes": argtypes,
            "argnames": inspect.getargs(f.__code__).args[1:],
            "kind": kind,
        }
        return f

    return regfn


class ControllerBase:
    """
    May need this class, not sure yet.
    """
    def __init__(self, registry):
        self.__registry = registry

    def handle_incoming_packet(self, packet) -> slipp.Packet:
        """
        Handles an incoming packet.

        Cases:
          op = LSCMD:
            Return a list of all available commands, content field is
            ignored.
          otherwise:
            Interpret op as a command, content field must be properly formatted
            JSON whether or not any commands are used.
        """
        if packet.op == "LSCMD":
            return slipp.Packet(
                op="ACK", seq=packet.seq,
                contents={"commands": {
                    cmd: {
                        "argtypes": [at.__name__ for at in details["argtypes"]],
                        "kind": details["kind"]
                    }
                    for cmd, details in self.__registry.items()
                }},
            )

        # Convenience function for error packets
        def errpkt(msg):
            return slipp.Packet(
                op="NAK", seq=packet.seq,
                contents={"error": msg},
            )

        fn_info = self.__registry.get(packet.op)
        if fn_info is None:
            return errpkt(f"unrecognized command \"{packet.op}\"")

        n_args = len(fn_info["argtypes"])
        recv_args = []
        if isinstance(packet.contents, dict):
            recv_args = packet.contents.get("args", [])

        if not isinstance(recv_args, list):
            return errpkt(f"Args should be a list, got {type(recv_args)}")
        if len(recv_args) != n_args:
            return errpkt(f"Expected {n_args} args, got {len(recv_args)}")

        for i, (t_arg, v_arg) in enumerate(zip(fn_info["argtypes"], recv_args)):
            if not isinstance(v_arg, t_arg):
                return errpkt(f"Arg at index {i} is of type {type(v_arg).__name__}, expected {t_arg.__name__}")

        try:
            t_start = time.time()
            ret = fn_info["fn"](self, *recv_args)
            t_end = time.time()

            outpkg = slipp.Packet(
                op="ACK", seq=packet.seq,
                contents={
                    "data": ret,
                    "exectime": t_end - t_start,
                },
            )
        except Exception as e:
            traceback.print_exception(e)
            outpkg = errpkt(f"Error executing the command: {str(e)}")

        return outpkg
