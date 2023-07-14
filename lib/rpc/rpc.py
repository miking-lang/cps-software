import click
import sys
import re
from clang.cindex import Index, Config, CursorKind, TypeKind

CLANG_LIBRARY_FILE = 'libclang.so'
CLIENT_FILE_TEMPLATE = '''\
#include <string.h>

#include "cps.h"
#include "dxl.h"
#include "rpc.h"

{fn_id_enum}

{text}
'''
SERVER_FILE_TEMPLATE = '''\
#include <stdint.h>
#include <string.h>

#include "cps.h"
#include "dxl.h"
#include "rpc.h"

{fn_id_enum}

cps_err_t cps_rpc_handle(uint32_t fn) {{
    cps_err_t ret;
    switch (fn) {{
{text}
    default:
        abort();
        break;
    }}

    return CPS_ERR_OK;
}}
'''
CLIENT_FN_TEMPLATE = '''{fn_type} {fn_name}({c_fn_args}) {{
    cps_err_t ret;

    {c_args_send}

    {c_errcode_recv_check}{c_result_recv}

    return CPS_ERR_OK;
}}'''
SERVER_CASE_TEMPLATE = '''\
    case CPS_RPC_{fn_name}: {{
        {s_args}

        {s_call}
        {s_errcode_send}{s_result_send}{s_args_free}

        break;
    }}'''

RE_ARRAYSIZE = re.compile(r'\@arraysize\s+([_a-zA-Z0-9]+)\s+([_a-zA-Z0-9]+)')
RE_PARAM_OUT = re.compile(r'\@param\s*\[.*\bout\b.*\]\s+([_a-zA-Z0-9]+)')

# helper functions
def die(s): click.echo(s, err=True); sys.exit(1)
def indent(s = '', n = 1): return (n * '    ') + s

def name(sym): return sym.spelling
def is_ptr(sym): return sym.type.kind == TypeKind.POINTER
def is_array(sym): return sym.type.kind == TypeKind.INCOMPLETEARRAY

def is_dynsize(arg):
    return arg.szvar is not None

def emit_sizeof(arg):
    if arg.szvar is not None:
        # copying data pointed to * sizevar
        return f'sizeof(*{name(arg)}) * {name(arg.szvar)}'
    elif is_ptr(arg):
        # copying data pointed to
        return f'sizeof(*{name(arg)})'
    else:
        # copying data directly
        return f'sizeof({name(arg)})'

def emit_ptr_type(arg):
    # pointer to data stored inside
    if is_ptr(arg) or is_array(arg):
        return name(deref(arg)) + ' *'
    else:
        return name(arg.type) + ' *'

def deref(arg):
    if is_array(arg):
        return arg.type.get_array_element_type()
    elif is_ptr(arg):
        return arg.type.get_pointee()
    else:
        raise

def emit_send(arg):
    if is_dynsize(arg):
        return f'cps_rpc_send_dynarray({name(arg)}, {name(arg.szvar)});'
    elif is_ptr(arg) or is_array(arg):
        return f'cps_rpc_send({name(arg)});'
    else:
        return f'cps_rpc_send(&{name(arg)});'

def emit_recv(arg):
    if is_dynsize(arg):
        return f'cps_rpc_recv_dynarray({name(arg)}, {name(arg.szvar)});'
    elif is_ptr(arg) or is_array(arg):
        return f'cps_rpc_recv({name(arg)});'
    else:
        return f'cps_rpc_recv(&{name(arg)});'

def emit_server_alloc(arg):
    if is_dynsize(arg):
        return [f'{emit_ptr_type(arg)}{name(arg)} = malloc({emit_sizeof(arg)});']
        # TODO: check malloc return for NULL
    elif is_ptr(arg) or is_array(arg):
        return [
            f'{name(deref(arg))} _{name(arg)};',
            f'{emit_ptr_type(arg)}{name(arg)} = &_{name(arg)};'
        ]
    else:
        return [f'{name(arg.type)} {name(arg)};']

def emit_server_free(arg):
    if is_dynsize(arg):
        return f'free({name(arg)});';
    else:
        return None

class Argument:
    '''
    Simple proxy over existing data to house size variable as needed.
    '''
    def __init__(self, arg):
        self.arg = arg
        self.szvar = None

    def __getattr__(self, attr):
        if attr in ['szvar']:
            return object.__getattribute__(self, attr)
        else:
            return object.__getattribute__(self.arg, attr)

class RPCCodeGenerator:
    client_data = []
    server_data = []
    fn_names = []
    content = ''
    socket_name = 'cps_rpc_client_fd'

    def __init__(self):
        Config.set_library_file(CLANG_LIBRARY_FILE)

    def fn_id_enum(self):
        lines = [indent(f'CPS_RPC_{i},') for i in sorted(self.fn_names)]
        lines[0] = lines[0][:-1] + ' = 0xA000,'
        return '\n'.join([
            'enum cps_rpc_cmd_t {',
        ] + lines + [
            '};'
        ])

    def client_code(self):
        text = '\n'.join(self.client_data)
        return CLIENT_FILE_TEMPLATE.format(text=text, fn_id_enum=self.fn_id_enum())

    def server_code(self):
        text = '\n'.join(self.server_data)
        return SERVER_FILE_TEMPLATE.format(text=text, fn_id_enum=self.fn_id_enum())

    def emit_param_decl(self, arg):
        # TODO: this information should be inside clang somewhere
        # NOTE: get_tokens() sometimes returns no tokens, which is
        # why this function works by directly extracting text
        return self.content[arg.extent.start.offset:arg.extent.end.offset]

    def process(self, file, args, whitelist):
        idx = Index.create()
        self.content = file.read()
        tu = idx.parse(file.name, args=args)
        diagnostics = list(tu.diagnostics)
        if diagnostics:
            # error messages during parsing
            for i in diagnostics: click.echo(i, err=True)
            sys.exit(1)

        # extract only function declarations from the provided file
        # check whitelist if provided
        fns = filter(lambda sym:
            sym.location.file.name == file.name and
            sym.kind == CursorKind.FUNCTION_DECL and
            (name(sym) in whitelist if whitelist is not None else True)
            , tu.cursor.get_children())
        results = map(self.process_fn, fns)
        for (c, s) in results:
            self.client_data.append(c)
            self.server_data.append(s)

    def validate_args(self, args):
        '''
        Only allow supported types.
        '''
        ok_types = [
            TypeKind.UCHAR,
            TypeKind.UINT,
            TypeKind.USHORT,
            TypeKind.ULONG,
            TypeKind.INT,
            TypeKind.BOOL,

            TypeKind.RECORD, # struct
            TypeKind.INCOMPLETEARRAY, # array
        ]

        for arg in args:
            type = arg.type.get_canonical()
            if type.kind in ok_types:
                yield Argument(arg)
            elif is_ptr(arg):
                target = type.get_pointee()
                if target == TypeKind.POINTER:
                    raise NotImplementedError('only a single level of pointers is supported')
                elif target.kind == TypeKind.SCHAR:
                    raise NotImplementedError('C-String are not supported yet')
                elif target.kind in ok_types:
                    yield Argument(arg)
                else:
                    raise NotImplementedError(f'unsupported type: {target.kind}')
            else:
                raise NotImplementedError(f'unsupported type: {type.kind}')

    def reorder_args(self, fn, args):
        if not fn.raw_comment:
            # no sizevars since no comment
            yield from args
            return

        # find all sizevars
        doc_szvars = {}
        for line in fn.raw_comment.splitlines():
            s = line.strip()
            match = RE_ARRAYSIZE.search(s)
            if not match:
                continue

            var, szvar = match.groups()
            doc_szvars[var] = szvar

        szvar2var = {}
        tmp = []
        for arg in args:
            if name(arg) in doc_szvars:
                if not (is_array(arg) or is_ptr(arg)):
                    raise ValueError('only arrays or pointers can '
                        f'have a corresponding size variable: {name(arg)}')
                tmp.append(arg)
                # szvar will be added later, once encountered
                szvar2var[doc_szvars[name(arg)]] = arg
            elif is_array(arg):
                raise ValueError('array variable does not have a '
                    f'corresponding size variable: {name(arg)}')
            elif name(arg) in doc_szvars.values():
                # a size variable itself, save and skip it
                szvar2var[name(arg)].szvar = arg
            else:
                tmp.append(arg)

        for arg in tmp:
            if arg.szvar is not None:
                yield arg.szvar
            yield arg

    def process_doc(self, fn):
        doc_copy = []
        lines = fn.raw_comment.splitlines() if fn.raw_comment else []
        for line in lines:
            s = line.strip()
            if match := RE_PARAM_OUT.search(s):
                # @param[out] <var>
                # @param[in,out] <var>
                doc_copy.append(match.group(1))

        return doc_copy

    def process_fn(self, fn):
        try:
            return self._process_fn(fn)
        except Exception as e:
            die(f'{name(fn)}: {e}')

    def _process_fn(self, fn):
        socket_name = self.socket_name
        fn_name = name(fn)
        fn_type = name(fn.result_type)

        orig_args = list(self.validate_args(fn.get_arguments()))
        args = list(self.reorder_args(fn, orig_args))

        # TODO: extract @arraysize here too
        doc_copy = self.process_doc(fn)


        ## CLIENT SIDE ##
        # use original argument order for the function since this is
        # what the caller expects
        c_fn_args = ', '.join(map(self.emit_param_decl, orig_args))

        c_args_send = ('\n' + indent()).join([
            f'uint32_t __rpc_fn_id = CPS_RPC_{fn_name};',
            f'cps_rpc_send(&__rpc_fn_id);'
        ] + list(map(emit_send, args))
        )

        c_errcode_recv_check = ('\n' + indent()).join([
            f'cps_rpc_recv(&ret);',
            'if (ret != CPS_ERR_OK) return ret;'
        ])

        args_recv_back = list(filter(lambda x: name(x) in doc_copy, args))
        c_result_recv = ('\n' + indent()).join(
            map(emit_recv, args_recv_back)
        )

        ## SERVER SIDE ##
        args_alloc = map(emit_server_alloc, args)
        args_recv = map(emit_recv, args)
        s_args = ('\n\n' + indent(n=2)).join(
            map(lambda x: ('\n' + indent(n=2)).join(x[0]) + '\n' + indent(x[1], n=2), zip(args_alloc, args_recv))
        )

        s_args_free = ('\n' + indent(n=2)).join(
            filter(lambda x: x is not None, map(emit_server_free, args))
        )
        srv_fn_args = ', '.join(map(name, orig_args))
        s_call = f'ret = {fn_name}({srv_fn_args});'
        s_errcode_send = ('\n' + indent(n=2)).join([
            'cps_rpc_send(&ret);'
        ])
        s_result_send = ('\n' + indent(n=2)).join(
            map(emit_send, args_recv_back)
        )

        ## WHITESPACE ##
        if c_result_recv != '':
            c_result_recv = '\n\n' + indent(c_result_recv)
        if s_result_send != '':
            s_result_send = ('\n' + indent('if (ret != CPS_ERR_OK) break;', n=2)
                + '\n\n' + indent(s_result_send, n=2))
        if s_args_free != '':
            s_args_free = '\n\n' + indent(s_args_free, n=2)

        # register function as processed
        self.fn_names.append(fn_name)
        return (CLIENT_FN_TEMPLATE.format(**locals()), SERVER_CASE_TEMPLATE.format(**locals()))

@click.command()
@click.option('-i', 'inputs',
    multiple=True,
    type=click.File(),
    help='Input header file.')
@click.option('-I', 'include_dirs',
    multiple=True,
    help='Include directories.')
@click.option('-os', 'server',
    default='server/generated.c', show_default=True,
    type=click.File('w'),
    help='Server code output file.')
@click.option('-oc', 'client',
    default='client/generated.c', show_default=True,
    type=click.File('w'),
    help='Client code output file.')
@click.option('-w', 'whitelist',
    type=click.File(), default=None,
    help='Whitelisted functions, one per line.')
def main(inputs, include_dirs, server, client, whitelist):
    if len(inputs) == 0:
        die('no input files provided')

    if whitelist is not None:
        whitelist = whitelist.read().splitlines()

    codegen = RPCCodeGenerator()
    # TODO: newer standard
    # TODO: better way to collect flags for clang
    args = ['-std=c99']
    args += [f'-I{i}' for i in include_dirs]
    for file in inputs:
        codegen.process(file, args, whitelist)

    code = codegen.client_code()
    client.write(code)

    code = codegen.server_code()
    server.write(code)

if __name__ == '__main__':
    main()
