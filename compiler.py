from typing import Dict, List, Tuple, Any
import os

from Compilers.lexer.manual_lexer import lexical_analysis, tokens_to_terminals
from Compilers.ll_parser.core.ll_main import parse_with_tree
from Compilers.ll_parser.core.grammar_oop import Grammar, load_grammar_from_file
from Compilers.ll_parser.core.parse_table import build_parse_table
from Compilers.ll_parser.core.parse_tree import cst_to_ast
from Compilers.semantic.semantic_analyzer import run_semantic_analysis
from Compilers.middle_code.ir_generator import IRBuilder


class Compiler:
    """
    编译器类，集成词法分析、语法分析、语义分析和中间代码生成
    """

    def __init__(self):
        # 创建 Grammar 对象，用于存储文法定义
        self.grammar = Grammar()
        # 获取当前文件所在目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建文法文件路径 (CFG.txt 位于 ll_parser/examples 目录下)
        cfg_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'll_parser', 'examples', 'CFG.txt'
        )
        # 从文件加载文法规则到 Grammar 对象中
        load_grammar_from_file(cfg_path, self.grammar)
        # 对文法进行后处理：消除左递归、左公因子化
        self.grammar.finalize(eliminate_lr=True, left_fact=True)
        # 构建 LL(1) 分析表，返回分析表、是否为 LL1 文法标志以及文法终结符集合
        self.table, self.is_ll1, self.terminals = build_parse_table(
            self.grammar,
            start_symbol='Program'
        )

    def run_lexical_analysis(self, source_code: str, mode: str = '手动') -> Tuple[List, List[str]]:
        """
        运行词法分析

        参数:
            source_code: 源代码字符串
            mode: 分析模式，'手动' 或 '自动'

        返回:
            tokens: 词法单元列表，每个元素为 (token_type, lexeme)
            errors: 错误信息列表
        """
        if mode == '手动':
            # 调用用户手写的词法分析器实现
            return lexical_analysis(source_code)
        else:
            # 如果需要自动模式，则动态导入并调用自动词法分析器
            from Compilers.lexer.auto_lexer import analyze
            return analyze(source_code)

    def run_syntax_analysis(self, tokens: List) -> Tuple[Any, Any]:
        """
        运行语法分析，生成具体语法树 (CST) 和抽象语法树 (AST)

        参数:
            tokens: 词法单元列表

        返回:
            cst: 具体语法树节点
            ast: 抽象语法树节点
        """
        # 将 tokens 拆分成只含终结符和词素的平行列表
        terms_only = tokens_to_terminals(tokens)  # 提取 token_type
        lexemes_only = [lexeme for (_, lexeme) in tokens]  # 提取实际字符
        term_pairs = list(zip(terms_only, lexemes_only))  # 组成 (token_type, lexeme) 对列表

        # 使用 LL(1) 分析表解析，生成具体语法树 (CST)
        cst = parse_with_tree(
            term_pairs,
            self.grammar,
            self.table,
            'Program'
        )
        # 将 CST 转换为简化后的抽象语法树 (AST)
        ast = cst_to_ast(cst)

        return cst, ast

    def run_semantic_analysis(self, ast: Any) -> Dict:
        """
        运行语义分析，构建符号表并进行类型检查

        参数:
            ast: 抽象语法树

        返回:
            symbol_tables: 包含各作用域符号信息的字典
        """
        return run_semantic_analysis(ast)

    def run_ir_generation(self, ast: Any) -> Tuple[List, Dict]:
        """
        运行中间代码生成，输出四元式和字符串字面量表

        参数:
            ast: 抽象语法树

        返回:
            quads: 四元式列表，每个四元式为 (op, arg1, arg2, result)
            string_literals: 字符串字面量映射表，key 为值，value 为临时变量名
        """
        # 创建 IRBuilder 实例并生成中间表示
        irb = IRBuilder()
        irb.gen(ast)
        # 获取生成的四元式列表和字符串字面量表
        return irb.get_quads(), irb.get_string_literals()

    def compile(self, source_code: str, mode: str = '手动') -> Dict:
        """
        完整的编译流程：包括词法、语法、语义分析以及中间代码生成

        参数:
            source_code: 待编译源代码
            mode: 词法分析模式，默认 '手动'

        返回:
            result: 字典，包含各阶段结果或错误信息
        """
        result = {}

        # 1. 词法分析阶段
        tokens, lex_errors = self.run_lexical_analysis(source_code, mode)
        result['tokens'] = tokens
        result['lex_errors'] = lex_errors

        # 如果词法阶段有错误，则直接返回失败状态
        if lex_errors:
            result['status'] = 'failed'
            result['error'] = f"词法分析错误: {lex_errors}"
            return result

        try:
            # 2. 语法分析阶段
            cst, ast = self.run_syntax_analysis(tokens)
            result['cst'] = cst
            result['ast'] = ast

            # 3. 语义分析阶段
            symbol_tables = self.run_semantic_analysis(ast)
            result['symbol_tables'] = symbol_tables

            # 4. 中间代码生成阶段
            quads, string_literals = self.run_ir_generation(ast)
            result['quads'] = quads
            result['string_literals'] = string_literals

            # 如果所有阶段成功，则返回 success
            result['status'] = 'success'
            return result
        except Exception as e:
            # 捕获任意阶段异常，返回失败并携带异常信息
            result['status'] = 'failed'
            result['error'] = str(e)
            return result


def format_quads(quads):
    """格式化四元式输出，使其更易阅读"""
    lines = ["\n生成的中间代码（四元式）："]
    for i, quad in enumerate(quads):
        # 使用索引对每个四元式编号
        lines.append(f"{i:3d}: {quad}")
    return "\n".join(lines)


def format_string_literals(string_literals):
    """格式化字符串字面量表输出"""
    if not string_literals:
        return ""

    lines = ["\n字符串字面量表："]
    for value, name in string_literals.items():
        # name 为临时变量名，value 为字面量值
        lines.append(f"{name}: {value}")
    return "\n".join(lines)


if __name__ == '__main__':
    # 实例化 Compiler
    compiler = Compiler()

    # 示例测试代码，包含变量声明、条件分支和返回语句
    test_code = """
    int main() {
        int x = 10;
        int y = x + 5;

        if (x > 5) {
            y = 1;
        } else {
            y = 0;
        }

        return 0;
    }
    """

    # 执行编译流程
    result = compiler.compile(test_code)

    if result['status'] == 'success':
        print("编译成功！")
        print("\n词法分析结果:")
        # 打印每个 token 的类型及对应词素
        for i, (syn, tok) in enumerate(result['tokens']):
            print(f"{i}: {tok} ({syn})")

        print("\n中间代码生成结果:")
        print(format_quads(result['quads']))
        print(format_string_literals(result['string_literals']))
    else:
        # 若失败，输出错误信息
        print(f"编译失败: {result['error']}")
