# ll_main.py

from typing import List, Dict, Tuple

from Compilers.ll_parser import Grammar, Production ,load_grammar_from_file
from Compilers.ll_parser import compute_first, compute_follow
from Compilers.ll_parser import build_parse_table
from Compilers.ll_parser import Node, print_tree, cst_to_ast

from manual_lexer import lexical_analysis, tokens_to_terminals


def parse_with_tree(
        tokens: List[str],
        grammar: Grammar,
        table: Dict[Tuple[str, str], Production],
        start_symbol: str
) -> Node:
    """
    使用 LL(1) 预测分析表对输入符号串进行语法分析，并构建具体语法树（CST）。

    参数:
        tokens: 词法分析后得到的终结符串列表，不含结束符 '$'。
        grammar: 文法对象，用于区分非终结符和终结符。
        table: LL(1) 预测分析表，键为 (非终结符, 终结符)，值为对应产生式。
        start_symbol: 文法的起始符号（例如 'Program'）。

    返回:
        构建完成的语法树根节点（Node）。

    异常:
        如果遇到无法匹配的符号或产生式，抛出 SyntaxError。
    """
    # 初始化符号栈和节点栈，符号栈底为 '$'
    stack_sym = ['$', start_symbol]
    root = Node(start_symbol)
    stack_node = [Node('$'), root]

    # 为 tokens 添加结束符 '$'
    tokens = tokens + ['$']
    pos = 0  # 输入指针

    # 当符号栈非空时，不断匹配
    while stack_sym:
        top_sym = stack_sym.pop()
        top_node = stack_node.pop()
        lookahead = tokens[pos]

        # 如果栈顶是终结符或 '$'
        if top_sym not in grammar.nonterminals:
            if top_sym == lookahead:
                # 匹配成功，将节点标签设为当前终结符，然后前移
                top_node.label = lookahead
                pos += 1
                continue
            else:
                # 匹配失败，抛出语法错误
                raise SyntaxError(f"Unexpected token '{lookahead}' at position {pos}")

        # 对于非终结符，从预测表中查产生式
        prod = table.get((top_sym, lookahead))
        if prod is None:
            raise SyntaxError(f"No rule for ({top_sym}, '{lookahead}')")

        # 根据产生式右部创建子节点
        children = [Node(sym) for sym in prod.body]
        top_node.children = children

        # 将产生式右部符号和对应节点逆序压入栈中，跳过 ε
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
    """
    程序入口：
      1. 构建文法并消除左递归、提取左公因子
      2. 构建 LL(1) 预测分析表
      3. 对一系列示例源代码进行词法分析、语法分析，生成并打印 AST
    """
    # 1. 构建并准备文法
    # g = build_grammar()
    print("=========g1========")
    g1 = Grammar();
    load_grammar_from_file('CFG.txt', g1)
    print(g1)

    print("=========g2========")
    g2 = build_grammar();
    print(g2)

    # g.finalize(eliminate_lr=True, left_fact=True)
    #
    # # 2. 构建预测分析表
    # table, is_ll1, terminals = build_parse_table(g, start_symbol='Program')
    # print(f"Terminals: {terminals}")  # 打印所有终结符
    #
    # # 示例输入
    #
    #
    # lexed, _ = lexical_analysis('int z = 1 + 2 * (3 - 4) / 5;')
    # terms = tokens_to_terminals(lexed)
    # # 期望的终结符序列（不含尾 '$'）
    # expected = ['int', 'ID', '=', 'INT_LITERAL', '+', 'INT_LITERAL', '*', '(', 'INT_LITERAL',
    #             '-', 'INT_LITERAL', ')', '/', 'INT_LITERAL', ';']
    # assert terms == expected, f"映射结果不符: {terms}"
    # tree = parse_with_tree(terms, g, table, 'Program')
    # ast_tree = cst_to_ast(tree)
    # print("-- AST --")
    # print_tree(ast_tree)

if __name__ == '__main__':
    main()
