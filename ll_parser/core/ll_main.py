# ll_main.py

from typing import List, Dict, Tuple
from collections import deque
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from Compilers.ll_parser.core.grammar_oop import Grammar, Production, load_grammar_from_file
from Compilers.ll_parser.core.first_follow import compute_first, compute_follow
from Compilers.ll_parser.core.parse_table import build_parse_table
from Compilers.ll_parser.core.parse_tree import Node, print_tree, cst_to_ast
from Compilers.manual_lexer import lexical_analysis, tokens_to_terminals


def parse_with_tree(
    tokens: List[Tuple[str, str]],  # 每项为 (终结符名称, 原始文本)
    grammar: 'Grammar',
    table: Dict[Tuple[str, str], 'Production'],
    start_symbol: str
) -> Node:
    """
    基于 LL(1) 分析表的自顶向下解析，构造并返回 CST 根节点。
    tokens: 终结符与文本对列表，不包括结束符
    grammar: Grammar 对象，包含 .nonterminals
    table: 解析表，键为 (非终结符, 终结符)
    start_symbol: 文法开始符号名称
    """
    stack_sym  = deque(['$', start_symbol])
    root       = Node(start_symbol)
    stack_node = deque([Node('$'), root])

    # 拆分出并添加结束符
    terms = [t for t,_ in tokens] + ['$']
    texts = [txt for _,txt in tokens] + ['$']
    pos = 0

    while stack_sym:
        top_sym       = stack_sym.pop()
        top_node      = stack_node.pop()
        lookahead_term = terms[pos]

        # 如果栈顶是终结符
        if top_sym not in grammar.nonterminals:
            if top_sym == lookahead_term:
                top_node.label = top_sym
                top_node.value = texts[pos]  # 赋值真实文本
                pos += 1
                continue
            else:
                raise SyntaxError(f"Unexpected token '{texts[pos]}' at position {pos}")

        # 否则是非终结符，从表中取产生式
        prod = table.get((top_sym, lookahead_term))
        if prod is None:
            raise SyntaxError(f"No rule for ({top_sym}, '{lookahead_term}')")

        # 创建子节点并压栈
        children = [Node(sym) for sym in prod.body]
        top_node.children = children
        for sym, node in zip(reversed(prod.body), reversed(children)):
            if sym != 'ε':
                stack_sym.append(sym)
                stack_node.append(node)

    return root
def build_grammar() -> Grammar:
    """
    构造并返回用于示例的 C 语言子集文法。

    返回:
        完整添加产生式但未 finalize 的 Grammar 对象。
    """
    g = Grammar()

    # 顶层程序结构
    # 在最顶层程序结构之前，允许出现预处理指令
    g.add_prod('Program', ['PPList', 'DeclList', 'StmtList'])
    # 新增 PPList 用于存放 0 或多条预处理指令
    g.add_prod('PPList', ['PPDirective', 'PPList'])
    g.add_prod('PPList', ['ε'])
    # 全局声明列表
    g.add_prod('DeclList', ['Decl', 'DeclList'])
    g.add_prod('DeclList', ['ε'])

    # 预处理指令本身
    g.add_prod('PPDirective', ['#', 'include', '<', 'ID', '.', 'ID', '>'])
    # 单个声明
    g.add_prod('Decl', ['Type', 'ID', 'DeclTail'])

    # 函数声明分支
    g.add_prod('DeclTail', ['(', 'ParamList', ')', 'CompoundStmt'])
    # 变量声明分支
    g.add_prod('DeclTail', ['VarDeclPrime'])

    # 变量声明后缀：带初值或不带初值
    g.add_prod('VarDeclPrime', ['=', 'Expr', ';'])
    g.add_prod('VarDeclPrime', [';'])

    # 基本类型
    g.add_prod('Type', ['int'])
    g.add_prod('Type', ['float'])
    g.add_prod('Type', ['void'])

    # 参数列表
    g.add_prod('ParamList', ['Param', 'ParamListTail'])
    g.add_prod('ParamList', ['ε'])
    g.add_prod('ParamListTail', [',', 'Param', 'ParamListTail'])
    g.add_prod('ParamListTail', ['ε'])
    g.add_prod('Param', ['Type', 'ID'])

    # 语句入口（支持局部声明）
    g.add_prod('Stmt', ['Decl'])
    g.add_prod('Stmt', ['AssignStmt'])
    g.add_prod('Stmt', ['ExprStmt'])
    g.add_prod('Stmt', ['CompoundStmt'])
    g.add_prod('Stmt', ['IfStmt'])
    g.add_prod('Stmt', ['WhileStmt'])
    g.add_prod('Stmt', ['ReturnStmt'])

    # 赋值语句
    g.add_prod('AssignStmt', ['ID', '=', 'Expr', ';'])
    # 表达式语句
    g.add_prod('ExprStmt', ['Expr', ';'])
    g.add_prod('ExprStmt', [';'])

    # 条件语句
    g.add_prod('IfStmt', ['if', '(', 'Expr', ')', 'Stmt', 'ElseStmt'])
    g.add_prod('ElseStmt', ['else', 'Stmt'])
    g.add_prod('ElseStmt', ['ε'])

    # 循环语句
    g.add_prod('WhileStmt', ['while', '(', 'Expr', ')', 'Stmt'])

    # 返回语句
    g.add_prod('ReturnStmt', ['return', 'Expr', ';'])

    # 复合语句（块）
    g.add_prod('CompoundStmt', ['{', 'DeclList', 'StmtList', '}'])
    g.add_prod('StmtList', ['Stmt', 'StmtList'])
    g.add_prod('StmtList', ['ε'])

    # 顶层表达式
    g.add_prod('Expr', ['ExprOr'])
    g.add_prod('ExprOr', ['ExprAnd', 'ExprOrTail'])
    g.add_prod('ExprOrTail', ['||', 'ExprAnd', 'ExprOrTail'])
    g.add_prod('ExprOrTail', ['ε'])

    g.add_prod('ExprAnd', ['ExprRel', 'ExprAndTail'])
    g.add_prod('ExprAndTail', ['&&', 'ExprRel', 'ExprAndTail'])
    g.add_prod('ExprAndTail', ['ε'])

    # 关系运算
    g.add_prod('ExprRel', ['ExprAdd', 'ExprRelTail'])
    for op in ['==', '!=', '<=', '>=', '<', '>']:
        g.add_prod('ExprRelTail', [op, 'ExprAdd', 'ExprRelTail'])
    g.add_prod('ExprRelTail', ['ε'])

    # + - * /运算
    g.add_prod('ExprAdd', ['ExprMul', 'ExprAddTail'])
    g.add_prod('ExprAddTail', ['+', 'ExprMul', 'ExprAddTail'])
    g.add_prod('ExprAddTail', ['-', 'ExprMul', 'ExprAddTail'])
    g.add_prod('ExprAddTail', ['ε'])

    g.add_prod('ExprMul', ['ExprUnary', 'ExprMulTail'])
    g.add_prod('ExprMulTail', ['*', 'ExprUnary', 'ExprMulTail'])
    g.add_prod('ExprMulTail', ['/', 'ExprUnary', 'ExprMulTail'])
    g.add_prod('ExprMulTail', ['ε'])

    # 原子表达式
    # g.add_prod('ExprPrimary', ['(', 'Expr', ')'])
    g.add_prod('ExprPrimary', ['ID'])
    g.add_prod('ExprPrimary', ['INT_LITERAL'])
    g.add_prod('ExprPrimary', ['FLOAT_LITERAL'])
    # 一元运算与类型转换
    g.add_prod('ExprUnary', ['(', 'CastOrExpr'])
    g.add_prod('ExprUnary', ['+', 'ExprUnary'])
    g.add_prod('ExprUnary', ['-', 'ExprUnary'])
    g.add_prod('ExprUnary', ['!', 'ExprUnary'])
    g.add_prod('ExprUnary', ['ExprPrimary'])

    g.add_prod('CastOrExpr', ['Type', ')', 'ExprUnary'])  # (Type)ExprUnary
    g.add_prod('CastOrExpr', ['Expr', ')'])  # (Expr)
    # g.add_prod('ExprUnary', ['(', 'Type', ')', 'ExprUnary'])
    return g


def main():
    # 加载并初始化文法
    g = Grammar()
    # 从examples目录中加载语法规则文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    grammar_file = os.path.join(current_dir, '../examples/CFG.txt')
    load_grammar_from_file(grammar_file, g)
    g.finalize(eliminate_lr=True, left_fact=True)

    # 构造 LL(1) 分析表
    table, is_ll1, G_terms = build_parse_table(g, start_symbol='Program')
    print(f"Grammar terminals: {G_terms}")
    print(f"Is LL(1): {is_ll1}")

    # 测试源程序
    sample_sources = [
        'for(i = 0;i<2;i++){}',
    ]
    for src in sample_sources:
        print('\nSource:', src)
        lexed, lex_err = lexical_analysis(src)
        if lex_err:
            print("Lexical errors:", lex_err)
            continue

        # 生成 (终结符, 文本) 对
        terms = tokens_to_terminals(lexed)
        lexemes = [lex for (_, lex) in lexed]
        pairs = list(zip(terms, lexemes))

        # 打印词法结果
        print("Tokens and lexemes:", pairs)

        try:
            # 构造 CST，转换为 AST 并打印
            cst = parse_with_tree(pairs, g, table, 'Program')
            ast = cst_to_ast(cst)
            print("-- AST --")
            print_tree(ast)
        except SyntaxError as e:
            print("Syntax error:", e)


if __name__ == '__main__':
    main()