## Packages
You need `clang` development files from your package manager.

### Fedora
```bash
sudo dnf install clang15-devel
```

## Python
In this directory, create a virtual environment with
```bash
python3 -m venv venv
```

Activate with
```bash
source venv/bin/activate
```

Inside the virtual environment, install required packages:
```bash
pip install --upgrade -r requirements.txt
```

**N.B.** you need to have the same version of `clang` development package and `clang` the Python package.
Modify `requirements.txt` as necessary.

## Generating code
General syntax is
```bash
python3 rpc.py -i input-header [-i input-header ...] [-os output-server] [-oc output-client] [-I include-dir [-I include-dir ...]] [-w whitelist]
```

`whitelist` is a file with whitelisted functions, one per line. If none is provided, all functions are processed.
By default, server code is written to `server/generated.c` and client code is written to `client/generated.c`.

To generate code for `dxl`, `accel` and `dist`:
```bash
python3 rpc.py -i../dxl/dxl.h -i../accel/accel.h -i../dist/dist.h -I../cps/ -I/usr/lib64/clang/15.0.7/include/
```

Note that include directories for `cps.h` and `stddef.h`, `stdbool.h` etc need to be specified via the `-I` flag.
`cps.h` is located in `../cps/`, while the rest are in `/usr/lib64/clang/<version>/include/` (platform-dependent).

As a shortcut, a `Makefile` is provided which will execute the above command. Modify it as necessary, and run
```bash
make
```
in this directory.

## Limitations
- Structs in function calls must be `__attribute__((packed))`
- Only one level of pointers is supported
- C-strings are not supported (yet)
    - Can be implemented as dynamically sized arrays
- Server and client platform must have same endianness (big/little) and word size (64/32 bit)
- No checking if client and server are compatible (see TODO)

## Troubleshooting
- Header file not found
    - Make sure that `-I` flags are provided (see above)
- Some functions work while others crash
    - Make sure server and client platforms have same endianness (big/little) and word size (64/32 bit)

## TODO
- [ ] Add versioning and version checking to client and server
- [ ] Put arguments into a struct and send that (=1 write call) if no dynamically sized arrays
    - [ ] Reorganize arguments so that all dynamic arrays end up at the end. Their sizes can be in the struct
- [ ] Append all processed files into the include list (currently `dxl.h` is hardcoded)
- [ ] Test and expand supported types (`validate_args`)
- [ ] Use data from `process_doc` to reorder arguments
- [ ] Add possibility to use a blacklist instead
