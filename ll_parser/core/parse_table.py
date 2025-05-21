# parse_table.py
from typing import Dict, List, Tuple, Set, Any
from Compilers.ll_parser.core.grammar_oop import Grammar, Production
from Compilers.ll_parser.core.first_follow import compute_first, compute_follow

def build_parse_table(
    grammar: Grammar,
    start_symbol: str
) -> Tuple[Dict[Tuple[str, str], Production], bool, List[str]]:
    """
    构建给定文法的 LL(1) 预测分析表。

    返回值：
        table: 字典映射 (非终结符, 终结符) -> 对应的产生式 Production
        is_LL1: 如果文法是 LL(1) 无冲突，则为 True；否则为 False
        terminals: 包含所有终结符及结束标记 '$' 的列表
    """
    # 1. 计算 FIRST 和 FOLLOW 集
    firsts: Dict[str, Set[str]] = compute_first(grammar)
    follows: Dict[str, Set[str]] = compute_follow(grammar, firsts, start_symbol)

    # 2. 获取所有非终结符和终结符列表，终结符列表末尾添加 '$'
    nonterminals: List[str] = list(grammar.nonterminals)
    terminals: List[str] = list(grammar.terminals) + ['$']

    # 初始化预测分析表和 LL(1) 标志
    table: Dict[Tuple[str, str], Production] = {}
    is_LL1 = True

    # 辅助函数：计算符号序列的 FIRST 集合
    def first_of_sequence(seq: List[str]) -> Set[str]:
        """
        对于符号序列 X1 X2 ... Xn，返回其 FIRST 集合。
        包括：
          - 若 X1 能推导出终结符 t，则 t ∈ FIRST(seq)
          - 若所有 Xi 均能推出 ε，则 ε ∈ FIRST(seq)
        """
        result: Set[str] = set()
        for symbol in seq:
            # 如果是空串 ε，则包含 ε 并结束
            if symbol == 'ε':
                result.add('ε')
                break
            # 如果是终结符，加入并结束
            if symbol in grammar.terminals:
                result.add(symbol)
                break
            # 否则为非终结符，将 FIRST(symbol) \ {ε} 并入结果
            result |= (firsts[symbol] - {'ε'})
            # 如果该非终结符不能推导 ε，结束；否则继续下一个符号
            if 'ε' not in firsts[symbol]:
                break
        else:
            # 如果循环完整执行，说明所有符号都能推出 ε
            result.add('ε')
        return result

    # 3. 填充预测分析表
    for head, prods in grammar.productions.items():  # 遍历每个非终结符（如 E）及其所有产生式
        for prod in prods:  # 循环每个产生式（如 E → T E'）
            # 计算产生式右部的 FIRST 集（比如 T E' 的 FIRST）
            first_set = first_of_sequence(prod.body)

            # 规则一：处理 FIRST 集中的终结符（除 ε 外）
            for terminal in (first_set - {'ε'}):  # 比如当 FIRST={id} 时
                key = (head, terminal)  # 表格坐标：如 (E, id)
                if key in table:  # 如果格子已有内容 → 冲突！
                    is_LL1 = False
                else:
                    table[key] = prod  # 填入产生式

            # 规则二：处理 ε 情况
            if 'ε' in first_set:  # 如果产生式可以推导出空
                for terminal in follows[head]:  # 遍历 FOLLOW 集合（如 FOLLOW(E')={$}）
                    key = (head, terminal)  # 对应坐标：如 (E', $)
                    if key in table:  # 格子已被占用 → 冲突！
                        is_LL1 = False
                    else:
                        table[key] = prod  # 填入产生式

    return table, is_LL1, terminals