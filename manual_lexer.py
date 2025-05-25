# manual_lexer.py 数字合法性校验函数（不使用正则表达式）
from typing import List, Dict, Set,Tuple
# 定义关键字及其对应的编码
# keywords = {
#     'int': 1, 'float': 2, 'double': 3, 'char': 4, 'if': 5,
#     'else': 6, 'while': 7, 'for': 8, 'return': 9, 'void': 10,
#     'string': 11, 'bool': 12, 'true': 13, 'false': 14, 'main': 15,
#     'include': 16
# }
keywords = {
    'int': 1, 'float': 2, 'double': 3, 'char': 4, 'if': 5,
    'else': 6, 'while': 7, 'for': 8, 'return': 9, 'void': 10,
    'string': 11, 'bool': 12, 'true': 13, 'false': 14,
    'include': 16, 'read': 17, 'write': 18
}

# 定义操作符及其对应的编码
operators = {
    '=': 20, '+': 21, '-': 22, '*': 23, '/': 24, '%': 25,
    '==': 26, '!=': 27, '<': 28, '>': 29, '<=': 30, '>=': 31,
    '<<': 32, '>>': 33, '&&': 34, '||': 35,
    '+=': 36, '-=': 37, '*=': 38, '/=': 39, '%=': 40,
    '++': 41, '--': 42, '!': 43, '&': 44
}
operator_chars = set(''.join(operators.keys()))

delimiter = {
    '(': 50, ')': 51, '[': 52, ']': 53, '{': 54, '}': 55,
    '.': 56, ',': 57, ';': 58, "'": 59, '#': 60, '?': 61, '"': 62,':':63
}

identifier_code = 45
integer_code = 46
float_code = 47
string_code = 48
char_code = 49

def is_valid_integer(num: str) -> bool:
    """
    判断字符串 num 是否为合法的整数（可选正负号 + 十进制数字）。
    返回 True 表示合法，False 表示不合法或空串。
    """
    if not num:
        # 空字符串不是合法整数
        return False
    if num[0] in '+-':
        # 如果以 '+' 或 '-' 开头，去掉符号部分再判断
        num = num[1:]
    # 剩余部分必须全为数字字符
    return num.isdigit()


def is_valid_decimal(num: str) -> bool:
    """
    判断字符串 num 是否为合法的无符号十进制整数（不允许前导零，除非整个数为 '0'）。
    返回 True 表示合法，False 表示不合法或空串。
    """
    if not num:
        # 空字符串非法
        return False
    if num == '0':
        # 单独的 '0' 是合法的
        return True
    if num.startswith('0'):
        # 以 '0' 开头且长度大于 1 则为前导零，非法
        return False
    # 剩余部分所有字符均为数字
    return num.isdigit()


def is_valid_hex(num: str) -> bool:
    """
    判断字符串 num 是否为合法的十六进制整数字面量。
    要求以 '0x' 或 '0X' 开头，且后面至少有一位十六进制数字。
    """
    # 首先以小写判断前缀，并且长度至少大于 2
    if not num.lower().startswith('0x') or len(num) <= 2:
        return False

    # 定义合法的十六进制数字集合（包括大小写）
    hex_digits = '0123456789abcdefABCDEF'
    # 从 num[2:] 开始，每个字符必须都在合法集合中
    for c in num[2:]:
        if c not in hex_digits:
            return False
    return True


def is_valid_octal(num: str) -> bool:
    """
    判断字符串 num 是否为合法的八进制整数字面量。
    要求以 '0' 开头（且不等于单独的 '0'），后面只能跟 0–7 这 8 个数字。
    """
    # 空串或单 '0' 不算八进制（单 '0' 由十进制函数处理）
    if not num.startswith('0') or num == '0':
        return False
    # 检查从第二个字符起，均在 '0' 至 '7' 之间
    for c in num[1:]:
        if c < '0' or c > '7':
            return False
    return True


def is_valid_float(num: str) -> bool:
    """
    判断字符串 num 是否为合法的浮点数字面量，包括：
      - 标准小数格式，如 '123.45'、'0.1'
      - 科学计数法，如 '1.23e10'、'4E-3'
    返回 True 表示合法，False 表示不合法或空串。
    """
    if not num:
        # 空字符串非法
        return False

    lower = num.lower()
    # —— 先处理科学计数法部份 ——
    if 'e' in lower:
        parts = lower.split('e')
        # 如果 e 出现多次或缺少一边（如 '1.2e' 或 'e10'），返回 False。
        if len(parts) != 2:
            # 出现多个 'e' 或缺少 'e' 后/前内容均非法
            return False
        base, exp = parts
        # 底数和指数都不能为空
        if not base or not exp:
            return False
        # 底数可以再调用 is_valid_float（递归支持带小数点的底数）
        # 指数只能是整数（允许符号）
        return is_valid_float(base) and is_valid_integer(exp)

    # —— 再处理标准小数格式 ——
    if '.' not in num:
        # 没有小数点，既不是小数也没有触发科学计数法
        return False

    # 用 partition 分隔整数部分和小数部分
    int_part, _, frac_part = num.partition('.')
    # 如果整数部分不为空，必须全为数字（允许空串，如 '.5'）
    if int_part and not int_part.isdigit():
        return False
    # 小数部分必须全为数字（允许 '0' 前导）
    if not frac_part.isdigit():
        return False

    return True

def build_error(message: str, token: str, pos: int, source_code: str) -> str:
    line = source_code.count('\n', 0, pos) + 1
    return f'第{line}行：{message} "{token}"'

def lexical_analysis(source_code: str):
    tokens = []
    errors = []
    line_number = 1  # 当前处理的行号，用于错误定位
    source_code = source_code.lstrip('\ufeff')



    i = 0  # 当前处理的字符索引
    in_multiline_comment = False  # 标记是否处于多行注释中
    comment_start_pos = 0  # 多行注释开始的位置，用于错误定位

    while i < len(source_code):
        char = source_code[i]

        # 处理空白字符（包括空格、制表符、换行符等）
        # 如果当前字符是空白符，则跳过它；若是换行符，还需要更新行号信息
        if char.isspace() or ord(char) < 32:
            if char == '\n':
                line_number += 1  # 遇到换行符时，行号加一
            i += 1  # 跳过当前空白字符
            continue

        # 检测并处理多行注释（以 /* 开始，以 */ 结束）
        if char == '/' and i + 1 < len(source_code) and source_code[i + 1] == '*':
            comment_start_pos = i  # 记录注释起始位置（用于报错提示）
            comment_start_line = line_number  # 记录注释起始行号（用于报错提示）
            in_multiline_comment = True
            i += 2  # 跳过 "/*"
            comment_closed = False  # 用于标记是否成功闭合注释

            while i < len(source_code):
                if source_code[i] == '\n':
                    line_number += 1  # 多行注释中若遇到换行，更新行号
                elif i + 1 < len(source_code) and source_code[i] == '*' and source_code[i + 1] == '/':
                    # 检测到注释闭合符 "*/"
                    in_multiline_comment = False
                    comment_closed = True
                    i += 2  # 跳过 "*/"
                    break
                i += 1  # 继续向后遍历字符

            if not comment_closed:
                # 如果注释未正确闭合，记录错误信息
                errors.append(build_error(f"多行注释未闭合（起始于第{comment_start_line}行）", "/*", comment_start_pos,
                                          source_code))
            continue  # 完成注释处理后，跳过后续分析逻辑

        # 检测并处理单行注释（以 // 开始，直到行尾）
        if char == '/' and i + 1 < len(source_code) and source_code[i + 1] == '/':
            # 从当前字符开始跳过，直到遇到换行符为止
            while i < len(source_code) and source_code[i] != '\n':
                i += 1
            continue  # 跳过注释内容，处理下一行代码

        # 如果当前字符是引号（单引号或双引号），则可能是字符或字符串字面量
        if char == '"' or char == "'":
            quote = char  # 记录引号类型，区分字符和字符串
            start = i  # 记录字面量的起始位置
            i += 1  # 跳过开头的引号

            # 处理字符字面量（例如：'a' 或 '\n'）
            if quote == "'":
                char_content = ''  # 初始化字符内容

                # 处理转义字符（例如：'\n'）
                if i < len(source_code) and source_code[i] == '\\':
                    if i + 1 < len(source_code):
                        char_content = source_code[i:i + 2]  # 获取转义序列
                        i += 2  # 跳过转义序列
                # 处理普通字符（例如：'a'）
                elif i < len(source_code):
                    char_content = source_code[i]  # 获取字符
                    i += 1  # 跳过字符

                # 检查是否有闭合的单引号
                if i < len(source_code) and source_code[i] == "'":
                    i += 1  # 跳过闭合的单引号
                    tokens.append((char_code, f"'{char_content}'"))  # 添加字符字面量到 tokens
                    continue  # 继续处理下一个字符
                else:
                    # 如果没有闭合的单引号，记录错误
                    errors.append(build_error("字符字面量未闭合或格式错误", source_code[start:i], start, source_code))
                    tokens.append((0, source_code[start:i]))  # 添加错误的字面量到 tokens
                    continue  # 继续处理下一个字符

            # 字符或字符串
            if char == '"' or char == "'":
                quote = char  # 记录当前引号类型（单引号或双引号）
                start = i  # 记录字符串开始的位置
                i += 1  # 移动到字符串内容的起始位置

                # 处理字符字面量（如 'a' 或 '\n'）
                if quote == "'":
                    char_content = ''
                    if i < len(source_code) and source_code[i] == '\\':
                        # 处理转义字符（如 '\n'）
                        if i + 1 < len(source_code):
                            char_content = source_code[i:i + 2]  # 获取转义序列
                            i += 2
                    elif i < len(source_code):
                        # 处理普通字符
                        char_content = source_code[i]
                        i += 1
                    if i < len(source_code) and source_code[i] == "'":
                        # 成功匹配到结束单引号，构造字符字面量
                        i += 1
                        tokens.append((char_code, f"'{char_content}'"))
                        continue
                    else:
                        # 未匹配到结束单引号，记录错误
                        errors.append(
                            build_error("字符字面量未闭合或格式错误", source_code[start:i], start, source_code))
                        tokens.append((0, source_code[start:i]))
                        continue

                # 处理字符串字面量（如 "hello\nworld"）
                is_closed = False
                while i < len(source_code):
                    if source_code[i] == '\n':
                        # 遇到换行符，说明字符串未闭合，记录错误
                        errors.append(build_error("字符串未闭合", source_code[start:i], start, source_code))
                        break
                    if source_code[i] == quote:
                        # 成功匹配到结束引号，标记为已闭合
                        is_closed = True
                        i += 1
                        break
                    if source_code[i] == '\\':
                        # 处理转义序列，跳过转义字符和其后的一个字符
                        i += 2
                    else:
                        # 普通字符，继续前进
                        i += 1
                if not is_closed:
                    # 如果字符串未闭合，记录错误
                    errors.append(build_error("字符串未闭合", source_code[start:i], start, source_code))
                # 无论字符串是否闭合，都将其添加到 tokens 中
                tokens.append((string_code, source_code[start:i]))
                continue

        # 数字的处理逻辑
        if char.isdigit():  # 如果当前字符是数字
            start = i  # 记录数字的起始位置
            num_str = ''  # 用来存储数字字符串
            # 标记数字的类型
            is_hex = is_oct = is_float = is_invalid = False  # 初始化各种数字类型的标记
            error_msg = ''  # 错误信息初始化

            # 检查是否为十六进制数字（以 '0x' 开头）
            if source_code[i:i + 2].lower() == '0x':  # 如果当前字符和接下来的字符是 '0x' 或 '0X'，表示十六进制
                num_str += source_code[i:i + 2]  # 将 '0x' 加入数字字符串
                i += 2  # 跳过 '0x'
                hex_start = i  # 记录十六进制数字的起始位置

                # 收集十六进制数字（包括 '0-9' 和 'a-f' 字符）
                while i < len(source_code) and (source_code[i].isdigit() or source_code[i].lower() in 'abcdef'):
                    num_str += source_code[i]
                    i += 1

                # 检查十六进制字面量是否有效
                if i < len(source_code) and source_code[i].isalnum():  # 如果数字后面跟有字母或其他数字（无效字符）
                    while i < len(source_code) and source_code[i].isalnum():
                        num_str += source_code[i]
                        i += 1
                    is_invalid = True  # 标记为无效
                    error_msg = "十六进制字面量无效"  # 设置错误信息
                elif i == hex_start:  # 如果没有找到有效的十六进制数字
                    is_invalid = True
                    error_msg = "缺少十六进制数字"  # 提示缺少十六进制数字
                elif not is_valid_hex(num_str):  # 如果不是有效的十六进制数字
                    is_invalid = True
                    error_msg = "非法的十六进制数字"  # 提示非法的十六进制数字
                else:
                    is_hex = True  # 标记为有效的十六进制数字
            else:
                # 处理其他数字类型（包括十进制、浮点数、科学计数法等）
                # 浮点数1.收集数字部分
                while i < len(source_code) and (
                        source_code[i].isdigit() or source_code[i] in ['.', 'e', 'E', '+', '-']):
                    num_str += source_code[i]  # 收集数字部分
                    i += 1

                # 如果数字后面跟有字母，说明格式无效 如果数字后面紧接着字母字符，则认为是非法数字格式。
                if i < len(source_code) and source_code[i].isalpha():
                    while i < len(source_code) and source_code[i].isalnum():
                        num_str += source_code[i]
                        i += 1
                    is_invalid = True  # 标记为无效
                    error_msg = "数字格式无效"  # 设置错误信息

                # 检查是否为八进制数字（以 '0' 开头，且没有小数点和科学计数法）
                # 如果是以 0 开头且没有小数点或科学计数法的数字，进一步验证其是否为有效的八进制数字。如果无效，则设置错误信息。
                elif num_str.startswith('0') and num_str != '0' and '.' not in num_str and 'e' not in num_str.lower():
                    if is_valid_octal(num_str):  # 判断是否为有效的八进制数
                        is_oct = True  # 标记为八进制数字
                    else:
                        is_invalid = True
                        error_msg = "非法的八进制数"  # 提示非法的八进制数
                # 检查是否为浮点数或科学计数法
                # 如果数字包含小数点（.）或指数符号（e 或 E），则尝试验证其是否为有效的浮点数。
                elif '.' in num_str or 'e' in num_str.lower():
                    if is_valid_float(num_str):  # 判断是否为有效的浮点数
                        is_float = True  # 标记为浮点数
                    else:
                        is_invalid = True
                        error_msg = "浮点数格式不完整或无效"  # 提示浮点数格式无效
                # 如果以上条件都不满足，检查是否为有效的十进制数字
                elif not is_valid_decimal(num_str):
                    is_invalid = True
                    error_msg = "十进制数字无效"  # 提示十进制数字无效

            # 记录结果
            if is_invalid:  # 如果数字无效，记录错误
                errors.append(build_error(error_msg, num_str, start, source_code))  # 记录错误信息
                tokens.append((0, num_str))  # 将无效的数字加入 token，0 表示无效 token
            elif is_hex or is_oct or not is_float:  # 如果是十六进制、八进制或者纯整数
                tokens.append((integer_code, num_str))  # 将其标记为整数
            else:  # 如果是浮点数
                tokens.append((float_code, num_str))  # 将其标记为浮点数

            continue  # 继续处理下一个字符

        # 标识符或关键字
        if char.isalpha() or char == '_':
            # 如果当前字符是字母或下划线，则可能是标识符或关键字的开头
            start = i
            while i < len(source_code) and (source_code[i].isalnum() or source_code[i] == '_'):
                # 向后遍历，只要是字母、数字或下划线，都是合法的标识符字符
                i += 1
            token = source_code[start:i]  # 提取完整的标识符字符串
            if token in keywords:
                # 如果该字符串在关键字表中，则将其作为关键字记入
                tokens.append((keywords[token], token))
            else:
                # 否则是普通标识符
                tokens.append((identifier_code, token))
            continue  # 处理下一个字符

        # 操作符
        if char in operator_chars:
            # 如果当前字符是操作符的可能字符之一（如 +、-、= 等）

            if i + 2 < len(source_code):
                seq3 = source_code[i:i + 3]  # 尝试获取三个字符组成的操作符
                if seq3 not in operators and all(c in operator_chars for c in seq3):
                    # 如果不是合法的三字符操作符，但都是操作符字符组合，视为非法操作符
                    errors.append(build_error("非法操作符", seq3, i, source_code))
                    tokens.append((0, seq3))  # 0 代表错误标记
                    i += 3
                    continue

            if i + 1 < len(source_code):
                two_char = source_code[i:i + 2]  # 尝试获取两个字符组成的操作符
                if two_char in operators:
                    # 如果是合法的双字符操作符，如 '==', '++'
                    tokens.append((operators[two_char], two_char))
                    i += 2
                    continue

            if char in operators:
                # 如果是合法的单字符操作符，如 '+'、'-'、'*'
                tokens.append((operators[char], char))
                i += 1
                continue

        # 分隔符
        if char in delimiter:
            # 如果是合法的分隔符，如 '('、')'、';'、',' 等
            tokens.append((delimiter[char], char))
            i += 1
            continue

        # 未识别符号
        errors.append(build_error("未识别的符号", char, i, source_code))
        tokens.append((0, char))
        i += 1

    # 结束后检查多行注释是否闭合
    if in_multiline_comment:
        errors.append(build_error("多行注释未闭合", "/*", comment_start_pos, source_code))

    return tokens, errors

TOKEN_NAME = {
    # 关键字: 保留原样
    **{ v: k for k, v in keywords.items() },
    # 操作符和分隔符: 保留符号本身
    **{ v: k for k, v in operators.items() },
    **{ v: k for k, v in delimiter.items() },
    # 标识符、整型、浮点型字面量: 统一大写下划线风格
    identifier_code: 'ID',
    integer_code:   'INT_LITERAL',
    float_code:     'FLOAT_LITERAL',
    string_code:    'STRING_LITERAL',
    char_code:      'CHAR_LITERAL',
    # 确保分隔符被正确映射
    50: '(',  # 左括号
    51: ')',  # 右括号
}


def tokens_to_terminals(lexed_tokens: List[Tuple[int, str]]) -> List[str]:
    """
    将 (code, lexeme) 列表转换为文法终结符列表，名称与 grammar 定义完全一致。
    缺失任何映射时抛出 KeyError。
    """
    token_map = {
        # 字面量类型
        'INT_LITERAL': 'INT_LITERAL',
        'FLOAT_LITERAL': 'FLOAT_LITERAL',
        'STRING_LITERAL': 'STRING_LITERAL',
        'CHAR_LITERAL': 'CHAR_LITERAL',
        'ID': 'ID',
        # 关键字（小写，与文法中一致）
        'int': 'int', 'float': 'float', 'void': 'void',
        'if': 'if', 'else': 'else', 'while': 'while', 'for': 'for', 'return': 'return', 'include': 'include',
        'read': 'read', 'write': 'write',  # 添加read和write的映射
        # 操作符 & 分隔符
        '=': '=', '+': '+', '-': '-', '*': '*', '/': '/', '%': '%',
        '==': '==', '!=': '!=', '<': '<', '>': '>', '<=': '<=', '>=': '>=',
        '&&': '&&', '||': '||', '!': '!', '++': '++', '--': '--',
        '(': '(', ')': ')', '{': '{', '}': '}', '[': '[', ']': ']',
        ';': ';', ',': ',', '.': '.', '#': '#'
    }

    terminals: List[str] = []
    for code, lexeme in lexed_tokens:
        # 1) code -> 名字
        name = TOKEN_NAME.get(code)
        if name and name in token_map:
            terminals.append(token_map[name])
            continue
        # 2) lexeme 兜底
        if lexeme in token_map:
            terminals.append(token_map[lexeme])
            continue
        # 3) 特殊 ε
        if lexeme == 'ε':
            terminals.append('ε')
            continue
        # 4) 报错
        raise KeyError(f"未映射的 token: code={code}, lexeme='{lexeme}'")
    return terminals

# 示例测试
if __name__ == '__main__':
    src = 'if x == 10 then y = x + 1 else y = 0'
    lexed, errs = lexical_analysis(src)
    print("Tokens:    ", lexed)
    print("Terminals: ", tokens_to_terminals(lexed))
