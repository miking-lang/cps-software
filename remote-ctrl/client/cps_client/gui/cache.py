import copy
import json
import os
import pathlib
from typing import Union, Tuple, Callable

from ._gtk4 import GLib


DEFAULTS = {
    "SERVO_ORDER": [
        "BR_INNER_SHOULDER",
        "BR_OUTER_SHOULDER",
        "BR_ELBOW",
        "FR_INNER_SHOULDER",
        "FR_OUTER_SHOULDER",
        "FR_ELBOW",
        "BL_INNER_SHOULDER",
        "BL_OUTER_SHOULDER",
        "BL_ELBOW",
        "FL_INNER_SHOULDER",
        "FL_OUTER_SHOULDER",
        "FL_ELBOW",
    ],
    "host": "localhost",
    "port": "8372",
}


class JSONParameterCache:
    """
    A class for saving and restoring cached parameters.
    """
    def __init__(self, cache_name="cps-remote-ctrl-client"):
        self.params = dict()   # Stored parameters
        self.defaults = copy.deepcopy(DEFAULTS) # Default values
        self.written_params = set()   # Parameters that have been written after loading data
        self.write_callbacks = dict() # Callbacks to be invoked when a value has changed
        self.cachedir = pathlib.Path(GLib.get_user_cache_dir()) / cache_name
        self.cachefile = self.cachedir / "parameters.json"
        os.makedirs(self.cachedir, exist_ok=True)
        if os.path.isfile(self.cachefile):
            try:
                with open(self.cachefile, "r") as f:
                    params = json.load(f)
                    self.params = params
            except Exception as e:
                print(f"Warning, could not load JSON parameters: {type(e).__name__}: {str(e)}", flush=True)

    def _sanitize_args(self, args):
        if isinstance(args, str):
            args = (args,)
        if len(args) == 0:
            raise KeyError("No arguments provided")

        for a in args:
            if "." in a:
                raise ValueError("cannot contain a . in parameter argument")

        return ".".join(list(args))


    def writeback(self):
        """Writeback parameters to file system."""
        with open(self.cachefile, "w+") as f:
            json.dump(self.params, f)

    def register_callback(self,
                          args : Union[Tuple[str], str],
                          cb : Callable[[object], None]):
        """Callbacks to be called when a value has changed."""
        args = self._sanitize_args(args)

        if args not in self.write_callbacks:
            self.write_callbacks[args] = []

        self.write_callbacks[args].append(cb)

    def get(self, args : Union[Tuple[str], str]) -> object:
        """Get a value, or its default value."""
        args = self._sanitize_args(args)

        if args not in self.params:
            if args not in self.defaults:
                raise KeyError(f"No set value or default value for {args} found")
            else:
                return self.defaults[args]
        
        return self.params[args]

    def set(self,
            args : Union[Tuple[str], str],
            value : object):
        """Set a value."""
        args = self._sanitize_args(args)
        self.params[args] = value
        self.written_params.add(args)

        if args in self.write_callbacks:
            for cb in self.write_callbacks[args]:
                cb(value)

    def set_default(self,
                    args : Union[Tuple[str], str],
                    value : object):
        """Set a default value."""
        args = self._sanitize_args(args)
        self.defaults[args] = value

    def is_set(self, args : Union[Tuple[str], str]):
        """Check if something has been set."""
        args = self._sanitize_args(args)
        return bool(args in self.written_params)
