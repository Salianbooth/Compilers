from typing import Dict, List, Tuple, Optional, Any
import os

from manual_lexer import lexical_analysis, tokens_to_terminals
from ll_parser.core.ll_main import parse_with_tree
from ll_parser.core.grammar_oop import Grammar, load_grammar_from_file
from ll_parser.core.parse_table import build_parse_table
from ll_parser.core.parse_tree import cst_to_ast
from semantic_analyzer import run_semantic_analysis
from ir_generator import IRBuilder


class Compiler:
    """
    编译器类，集成词法分析、语法分析、语义分析和中间代码生成
    """
    def __init__(self):
        # 初始化语法分析相关组件
        self.grammar = Grammar()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cfg_path = os.path.join(current_dir, 'll_parser', 'examples', 'CFG.txt')
        load_grammar_from_file(cfg_path, self.grammar)
        self.grammar.finalize(eliminate_lr=True, left_fact=True)
        self.table, self.is_ll1, self.terminals = build_parse_table(self.grammar, start_symbol='Program')
        
    def run_lexical_analysis(self, source_code: str, mode: str = '手动') -> Tuple[List, List[str]]:
        """
        运行词法分析
        
        参数:
            source_code: 源代码
            mode: 分析模式，'手动'或'自动'
            
        返回:
            tokens: 词法单元列表
            errors: 错误信息列表
        """
        if mode == '手动':
            return lexical_analysis(source_code)
        else:
            # 如果需要自动模式，可以在这里添加
            from auto_lexer import analyze
            return analyze(source_code)
    
    def run_syntax_analysis(self, tokens: List) -> Tuple[Any, Any]:
        """
        运行语法分析
        
        参数:
            tokens: 词法分析得到的词法单元列表
            
        返回:
            cst: 具体语法树
            ast: 抽象语法树
        """
        # 把 tokens 拆成两并行数组
        terms_only = tokens_to_terminals(tokens)
        lexemes_only = [lexeme for (_, lexeme) in tokens]
        term_pairs = list(zip(terms_only, lexemes_only))
        
        # 语法分析
        cst = parse_with_tree(term_pairs, self.grammar, self.table, 'Program')
        ast = cst_to_ast(cst)
        
        return cst, ast
    
    def run_semantic_analysis(self, ast: Any) -> Dict:
        """
        运行语义分析
        
        参数:
            ast: 抽象语法树
            
        返回:
            symbol_tables: 符号表
        """
        return run_semantic_analysis(ast)
    
    def run_ir_generation(self, ast: Any) -> Tuple[List, Dict]:
        """
        运行中间代码生成
        
        参数:
            ast: 抽象语法树
            
        返回:
            quads: 四元式列表
            string_literals: 字符串字面量表
        """
        irb = IRBuilder()
        irb.gen(ast)
        return irb.get_quads(), irb.get_string_literals()
    
    def compile(self, source_code: str, mode: str = '手动') -> Dict:
        """
        完整的编译过程
        
        参数:
            source_code: 源代码
            mode: 词法分析模式
            
        返回:
            result: 包含编译过程各阶段结果的字典
        """
        result = {}
        
        # 词法分析
        tokens, lex_errors = self.run_lexical_analysis(source_code, mode)
        result['tokens'] = tokens
        result['lex_errors'] = lex_errors
        
        if lex_errors:
            result['status'] = 'failed'
            result['error'] = f"词法分析错误: {lex_errors}"
            return result
        
        try:
            # 语法分析
            cst, ast = self.run_syntax_analysis(tokens)
            result['cst'] = cst
            result['ast'] = ast
            
            # 语义分析
            symbol_tables = self.run_semantic_analysis(ast)
            result['symbol_tables'] = symbol_tables
            
            # 中间代码生成
            quads, string_literals = self.run_ir_generation(ast)
            result['quads'] = quads
            result['string_literals'] = string_literals
            
            result['status'] = 'success'
            return result
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            return result


def format_quads(quads):
    """格式化四元式输出"""
    lines = ["\n生成的中间代码（四元式）："]
    for i, quad in enumerate(quads):
        lines.append(f"{i:3d}: {quad}")
    return "\n".join(lines)


def format_string_literals(string_literals):
    """格式化字符串字面量表输出"""
    if not string_literals:
        return ""
    
    lines = ["\n字符串字面量表："]
    for value, name in string_literals.items():
        lines.append(f"{name}: {value}")
    return "\n".join(lines)


if __name__ == '__main__':
    # 测试编译器
    compiler = Compiler()
    
    # 测试源代码
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
    
    result = compiler.compile(test_code)
    
    if result['status'] == 'success':
        print("编译成功！")
        print("\n词法分析结果:")
        for i, (syn, tok) in enumerate(result['tokens']):
            print(f"{i}: {tok} ({syn})")
        
        print("\n中间代码生成结果:")
        print(format_quads(result['quads']))
        print(format_string_literals(result['string_literals']))
    else:
        print(f"编译失败: {result['error']}") 