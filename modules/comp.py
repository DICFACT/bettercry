"""."""

import argparse
import os


# Пробельные символы
WHITESPACES = ' \n\t'

# Импорт
IMPORT_OPENING, IMPORT_KEY, IMPORT_CLOSING = '[&]'

# Описание макросов
MACRO_OPENING, MACRO_KEY, MACRO_DEF_START, MACRO_CLOSING = '[::]'
MACRO_ARGS_OPENING, MACRO_ARGS_SEP, MACRO_ARGS_CLOSING = '(,)'

# Комментарии
COMMENT_OPENING, COMMENT_CLOSING = '[]'

# Строки
STRING_SHORTCUT_OPENING, STRING_SHORTCUT_CLOSING = '""'

# Использование макроса
MACRO_USAGE_KEY = ':'

# Shortcut для байта
BYTE_SHORTCUT = '$'

# Shortcut для логических значений
BOOL_SHORTCUT, TRUE_VALUE, FALSE_VALUE = '$TF'

# Комманды с символьным аргументом
COM_CHAR_ARG = COM_CONST, COM_PRINT = '^\''


# Команды с константным аргументом
COM_WITH_CONST_ARG = COM_GOTO, COM_BACK = 'GB'

# Команды с одним аргументом
COM_WITH_ARG = COM_ADD, COM_SUB, COM_MUL, COM_DIV, COM_MOD, COM_RANDOM,\
    COM_CMP, COM_EQL, COM_AND, COM_OR = '+-*/%N?=&|'

# Команды не принимающие аргументов
COM_WITHOUT_ARG = COM_LABEL, COM_SET, COM_INV, COM_POINTER, COM_READ, COM_ADDRESS,\
    COM_WRITE, COM_FLUSH, COM_INPUT, COM_NEXT, COM_PREV = 'LW!PRA#FI><'

# Индексинг комманд
COMS = COM_LABEL + COM_CONST + COM_PRINT + COM_GOTO + COM_BACK + COM_ADD + COM_SUB + COM_MUL + COM_DIV + COM_MOD +\
       COM_RANDOM + COM_CMP + COM_EQL + COM_SET + COM_INV + COM_POINTER + COM_READ + COM_ADDRESS +\
       COM_NEXT + COM_PREV + COM_WRITE + COM_FLUSH + COM_INPUT + COM_AND + COM_OR


def compile_code(code: str, scope: dict, is_macro: bool = False):
    """."""
    global cwd

    def byte(val: str):
        """."""
        return '0123456789ABCDEF'.index(val)
    
    length = len(code)
    i = 0

    out = bytearray()
    while i < length:
        # Skipping whitespaces
        if code[i] in WHITESPACES:
            i += 1
            continue

        # Imports
        if not is_macro and code[i:i+2] == IMPORT_OPENING + IMPORT_KEY:
            end = code.index(IMPORT_CLOSING, i + 2)
            name = code[i+2:end]
            try:
                with open(os.path.join(cwd, name)) as file:
                    out.extend(compile_code(file.read(), scope))
            except FileNotFoundError:
                with open(os.path.join('libs', name)) as file:
                    out.extend(compile_code(file.read(), scope))
            i = end + 1
            continue

        # Macro definition
        if not is_macro and code[i:i+2] == MACRO_OPENING + MACRO_KEY:
            name_end = code.index(MACRO_DEF_START, i + 2)
            name = code[i+2:name_end]

            stack = [MACRO_CLOSING]
            end = name_end + 1
            while len(stack) > 0:
                if code[end] == COMMENT_OPENING:
                    stack.append(COMMENT_CLOSING)
                elif code[end] == IMPORT_OPENING:
                    stack.append(IMPORT_CLOSING)
                elif code[end] == stack[-1]:
                    stack.pop()
                end += 1
            end -= 1
            
            # end = code.index(MACRO_CLOSING, name_end + 1)
            content = code[name_end + 1:end]
            scope[name] = compile_code(content, scope, is_macro=True)
            i = end + 1
            continue

        # Skipping comments
        if code[i] == COMMENT_OPENING:
            i = code.index(COMMENT_CLOSING, i + 1) + 1
            continue

        # Strings shortcut
        if code[i] == STRING_SHORTCUT_OPENING:
            end = code.index(STRING_SHORTCUT_CLOSING, i + 1)
            content = code[i+1:end]
            for c in content:
                out.append(COMS.index(COM_PRINT))
                out.append(ord(c) & 255)
            i = end + 1
            continue

        # Macro usage
        if code[i] == MACRO_USAGE_KEY:
            a = 1
            last_match = None
            name = ''
            while len(tuple(filter(lambda x: x.startswith(name), scope))) > 0:
                name = code[i+1:i+a+1]
                if name in scope:
                    last_match = name
                a += 1
            if last_match is None:
                raise ValueError(f'Macro "{name}" at {i} not found')
            out.extend(scope[last_match])
            i += len(last_match) + 1
            continue

        # Bool shortcut
        if code[i] == BOOL_SHORTCUT and (code[i+1] == TRUE_VALUE or code[i+1] == FALSE_VALUE and code[i+2] in WHITESPACES):
            out.append(COMS.index(COM_CONST))
            out.append([FALSE_VALUE, TRUE_VALUE].index(code[i+1]) * 0xFF)
            i += 2
            continue

        # Byte shortcut (eg. $41 ~ ^A)
        if code[i] == BYTE_SHORTCUT:
            b1 = byte(code[i+1])
            b2 = byte(code[i+2])
            out.append(COMS.index(COM_CONST))
            out.append((b1 << 4) + b2)
            i += 3
            continue

        # Commands with char args
        if code[i] in COM_CHAR_ARG:
            a = ord(code[i+1]) & 255
            out.append(COMS.index(code[i]))
            out.append(a)
            i += 2
            continue

        # Commands with constant arg
        if code[i] in COM_WITH_CONST_ARG:
            a = code[i+1]
            b = '0123456789ABCDEF'.index(a)
            out.append(COMS.index(code[i]))
            out.append(b)
            i += 2
            continue

        # Commands with args
        if code[i] in COM_WITH_ARG:
            a = code[i+1]
            b = '0123456789ABCDEF.'.index(a)
            out.append(COMS.index(code[i]))
            out.append(b)
            i += 2
            continue

        # Commands without args
        if code[i] in COM_WITHOUT_ARG:
            out.append(COMS.index(code[i]))
            out.append(0)
            i += 1
            continue

        raise ValueError(f'Unknown command! Found unknown command "{code[i]}" found at {i}.')
    return out


def main(raw_file_path, comp_file_path):
    with open(raw_file_path, 'rt') as inp, open(comp_file_path, 'wb') as out:
        out.write(compile_code(inp.read(), {}))


cwd = ''


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser('Compiles .bc files (raw BetterCry code) to .bcc that can be executed later')
    arg_parser.add_argument('infile', type=str, help='Path to file with raw BetterCry code')
    args = arg_parser.parse_args()

    cwd = os.path.split(args.infile)[0]

    outfile = os.path.splitext(args.infile)[0] + '.bcc'  # 'file.bc' -> 'file.bct' | 'file.txt' -> 'file.bcc'
    main(args.infile, outfile)

