import re

# 定义 Token 模式及优先级，按照从高到低的顺序放置，优先匹配更复杂或更特定的模式
TOKENS = [
    # 多行注释：匹配 /* ... */ 包含换行的注释，? 为非贪婪匹配
    ('COMMENT_MULTI',         r'/\*[\s\S]*?\*/'),
    # 单行注释：匹配 // 开头直到行尾的注释
    ('COMMENT_SINGLE',        r'//.*'),
    # 预处理指令：匹配 # 开头，后跟字母或下划线开头的标识符
    ('PREPROCESSOR',          r'\#[A-Za-z_][A-Za-z0-9_]*'),
    # 错误浮点：多个小数点后可带可选科学计数法，如 1.2.3 或 1.2.3e+4
    ('INVALID_FLOAT_MULTI_DOT', r'\d+\.\d+\.\d+([eE][+-]?\d+)?'),
    # 错误八进制：以 0 开头，但包含 8 或 9
    ('INVALID_OCTAL',           r'0[0-7]*[89]\d*'),
    # 错误十六进制：0x 后跟非十六进制字符
    ('INVALID_HEX',             r'0[xX][0-9A-Fa-f]*[^0-9A-Fa-f\s]+'),
    # 数字后接字母非法：非 0x 前缀的数字后面带字母
    ('INVALID_NUMBER_ALPHA',    r'(?!0[xX])\d+(?:\.\d*)?(?:[eE][+-]?\d+)?[A-Za-z_]\w*'),
    # 合法浮点：整数/小数部分可选，带可选科学计数法
    ('FLOAT',                   r'\d*\.\d+([eE][+-]?\d+)?|\d+[eE][+-]?\d+'),
    # 合法整数：十六进制、八进制、十进制和单独 0
    ('INTEGER',                 r'0[xX][0-9A-Fa-f]+|0[0-7]+|[1-9]\d*|0'),

    # 错误多字符操作符：连续 3 个以上操作符字符
    ('INVALID_OPERATOR_MULTI',  r'[+\-*/%<>=!&]{3,}'),
    # 合法双字符操作符，如 ++, --, ==, !=, <=, >=, <<, >>, &&, ||
    ('OP',                      r'\+\+|--|\+=|-=|\*=|/=|%=|==|!=|<=|>=|<<|>>|&&|\|\|'),
    # 合法单字符操作符，如 + - * / % < > = ! &
    ('OP',                      r'[+\-*/%<>=!&]'),
    # 错误双字符操作符：长度为 2 且不在合法列表中
    ('INVALID_OPERATOR',        r'(?:[+\-*/%<>=!&]{2})'),

    # 分隔符：逗号、分号、冒号、大括号、中括号、小括号、点
    ('DELIM',                   r'[\.,;:{}\[\]\(\)]'),
    # 关键字（必须放在 IDENT 之前，保证优先匹配）
    ('KEYWORD', r'\b(?:int|char|float|double|if|else|for|while|do|return|break|continue)\b'),
    # 标识符：以字母或下划线开头，后跟字母、数字或下划线
    ('IDENT',                   r'[A-Za-z_][A-Za-z0-9_]*'),

    # 非法字符串未闭合：以双引号开始，直到行尾未闭合
    ('STRING_UNCLOSED',         r'"(?:\\.|[^"\\\n])*(?!\")'),
    # 合法字符串：双引号内可包含转义序列或非引号字符
    ('STRING',                  r'"(?:\\.|[^"\\\n])*"'),
    # 非法字符常量未闭合：单引号开始未闭合
    ('CHAR_UNCLOSED',           r"'(?:\\.|[^'\\\n])*(?!')"),
    # 合法字符常量：单引号内一个字符或转义序列
    ('CHAR',                    r"'(?:\\.|[^'\\\n])'"),

    # 空白：空格、制表、换行等
    ('WHITESPACE',              r'\s+'),
    # 兜底：匹配任意单个字符
    ('MISMATCH',                r'.'),
]


# 关键字与符号映射
KEYWORDS = {'main':1, 'int':2, 'char':3, 'if':4, 'else':5,
            'for':6, 'while':7, 'return':8, 'void':9,
            'string':10, 'bool':11}
SYMBOLS  = {
    '=':21, '==':39, '!=':40, '<':36, '>':35, '<=':38, '>=':37,
    '+':22, '++':41, '+=':43, '-':23, '--':42, '-=':44,
    '*':24, '*=':45, '/':25, '/=':46, '%':26, '%=':47,
    '<<':48, '>>':49, '&&':50, '||':51,
    '(':26, ')':27, '[':28, ']':29, '{':30, '}':31,
    ',':32, ':':33, ';':34
}

# 构造 Scanner
# 接收 TOKENS，一次性编译所有正则，达到按优先级扫描的效果。
scanner = re.Scanner([(pattern, lambda s, t, tp=tt: (tp, t)) for tt, pattern in TOKENS])


# 全局错误列表
errors = []

# Token 类——兼容 PLY 接口属性
class Token:
    def __init__(self, type_code, value, type_name):
        self.type_code = type_code
        self.value = value
        self.type = type_name
    def __repr__(self):
        return f"Token({self.type_code}, '{self.value}', {self.type})"

# LexerWrapper：模拟 PLY 的 lexer 接口
# 用于封装 re.Scanner 输出，提供与 PLY 接口一致的方法：
class LexerWrapper:
    def __init__(self):
        # 存储扫描器处理后的所有合法/非法 Token 对象
        self._tokens = []
        # 当前扫描到的 token 索引
        self._index = 0

    def input(self, code: str):
        """
        处理输入的源代码字符串，将其转换为内部统一的 Token 列表，
        并根据类型分类，处理错误和合法情况。
        """
        global errors
        errors.clear()  # 清空全局错误列表
        all_tokens, _ = scanner.scan(code)  # 调用自定义扫描器进行词法分析

        out = []  # 保存处理后的 Token 对象列表
        for tp, lexeme in all_tokens:
            # 忽略空白和注释类 token，不做进一步处理
            if tp in ('WHITESPACE', 'COMMENT_MULTI', 'COMMENT_SINGLE'):
                continue

            # 不匹配的非法字符，记录错误并加入错误 token
            if tp == 'MISMATCH':
                errors.append(f"非法字符 '{lexeme}'")
                out.append(Token(0, lexeme, 'MISMATCH'))

            # 其他非法 token 类型（如无效数字格式等）
            elif tp.startswith('INVALID'):
                errors.append(f"{tp} 错误: '{lexeme}'")
                out.append(Token(0, lexeme, tp))

            # 如果是标识符并且是关键字
            elif tp == 'IDENT' and lexeme in KEYWORDS:
                out.append(Token(KEYWORDS[lexeme], lexeme, 'KEYWORD'))

            # 普通标识符
            elif tp == 'IDENT':
                out.append(Token(45, lexeme, 'IDENTIFIER'))

            # 整型或浮点型常量
            elif tp in ('INTEGER', 'FLOAT'):
                code_map = 46 if tp == 'INTEGER' else 47  # 整数:46，浮点数:47
                out.append(Token(code_map, lexeme, tp))

            # 操作符处理
            elif tp == 'OP':
                if lexeme in SYMBOLS:
                    out.append(Token(SYMBOLS[lexeme], lexeme, 'OPERATOR'))
                else:
                    errors.append(f"未知操作符 '{lexeme}'")
                    out.append(Token(0, lexeme, 'OPERATOR'))

            # 分隔符处理
            elif tp == 'DELIM':
                out.append(Token(SYMBOLS.get(lexeme, 0), lexeme, 'DELIMITER'))

            # 字符串或字符常量
            elif tp in ('STRING', 'CHAR'):
                code_map = 49 if tp == 'STRING' else 48  # 字符串:49，字符:48
                out.append(Token(code_map, lexeme, tp))

            else:
                # 其他类型，如预处理指令等统一用 63 表示
                out.append(Token(63, lexeme, tp))

        # 更新内部 Token 缓存和索引
        self._tokens = out
        self._index = 0

    def token(self):
        """
        获取当前索引指向的 token，并将索引向后推进一位。
        如果没有更多 token，返回 None。
        """
        if self._index < len(self._tokens):
            tok = self._tokens[self._index]
            self._index += 1
            return tok
        return None


# 对外导出兼容 PLY 接口的 lexer 与 errors
lexer = LexerWrapper()

# 分析函数：返回 (tokens, errors)
def analyze(code: str):
    """
    返回:
      tokens: List[ (type_code, lexeme, type_name) ]
      errors: List[str]
    """
    lexer.input(code)
    return [(t.type_code, t.value, t.type) for t in lexer._tokens], errors
