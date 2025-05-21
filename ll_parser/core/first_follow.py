# first_follow.py
from typing import Dict, Set, List
from Compilers.ll_parser.core.grammar_oop import Grammar


def compute_first(grammar: Grammar) -> Dict[str, Set[str]]:
    """
    计算给定文法中每个非终结符 A 的 FIRST 集合。
    FIRST(A) 包含：
      1. 能够出现在 A 推导的任意串最前面的终结符。
      2. 如果 A 能推导出空串，则包含 'ε'。

    算法思路：
      - 初始化所有非终结符的 FIRST 集为空集。
      - 不断遍历产生式，往 FIRST 集中添加符合规则的符号，直到不再变化。
    参数：
      grammar: 已完成 finalize() 的 Grammar 对象。
    返回：
      Dict[str, Set[str]]，键为非终结符，值为其 FIRST 集。
    """
    # 初始化 FIRST 字典，非终结符对应空集
    FIRST: Dict[str, Set[str]] = {A: set() for A in grammar.nonterminals}

    changed = True
    # 使用固定点算法，不断迭代直到 FIRST 集不再发生改变
    while changed:
        changed = False
        # 遍历文法中所有产生式
        for A, prods in grammar.productions.items():
            for prod in prods:
                # 对产生式 A -> X1 X2 ... Xn，依次处理每个符号 Xi
                for X in prod.body:
                    # 如果 Xi 是终结符或 ε，直接加入 FIRST(A)，并停止当前产生式的遍历
                    if X not in grammar.nonterminals:
                        if X not in FIRST[A]:
                            FIRST[A].add(X)
                            changed = True
                        break
                    # 如果 Xi 是非终结符，则将 FIRST(X)
                    #（去除 ε）并入 FIRST(A)
                    before = len(FIRST[A])
                    FIRST[A] |= (FIRST[X] - {'ε'})
                    # 如果 X 可推出空串，继续检查下一个符号；否则停止
                    if 'ε' in FIRST[X]:
                        # 标记集合变化
                        if len(FIRST[A]) != before:
                            changed = True
                        continue
                    # Xi 不能推出 ε，停止当前产生式
                    if len(FIRST[A]) != before:
                        changed = True
                    break
                else:
                    # 如果产生式所有符号均可推出 ε，则 ε 属于 FIRST(A)
                    if 'ε' not in FIRST[A]:
                        FIRST[A].add('ε')
                        changed = True
    return FIRST


def compute_follow(grammar: Grammar,
                   FIRST: Dict[str, Set[str]],
                   start_symbol: str) -> Dict[str, Set[str]]:
    """
    计算给定文法中每个非终结符 A 的 FOLLOW 集合。
    FOLLOW(A) 包含：
      1. 能够出现在任意产生式中 A 之后紧跟的终结符。
      2. 如果在右侧 A 到串末尾，或后续符号均可推导 ε，则包含 '$'（输入结束符）。

    算法思路：
      - 初始化所有非终结符的 FOLLOW 集为空集，起始符号的 FOLLOW 集包含 '$'。
      - 使用固定点算法，从右到左遍历产生式右部，维护一个暂记符号集 trailer。
      - 将 trailer（去除 ε）并入当前非终结符的 FOLLOW，更新 trailer 为
        * 如果当前符号可推 ε，trailer ∪ FIRST(X) 去除 ε
        * 否则 trailer = FIRST(X)
      - 直到所有 FOLLOW 集稳定。
    参数：
      grammar: 已完成 finalize() 的 Grammar 对象。
      FIRST: 调用 compute_first 得到的 FIRST 集映射。
      start_symbol: 文法的起始符号，通常为 'Program'。
    返回：
      Dict[str, Set[str]]，键为非终结符，值为其 FOLLOW 集。
    """
    # 初始化 FOLLOW 字典
    FOLLOW: Dict[str, Set[str]] = {A: set() for A in grammar.nonterminals}
    # 起始符号包含结束符号 '$'
    FOLLOW[start_symbol].add('$')

    changed = True
    # 固定点迭代
    while changed:
        changed = False
        # 遍历所有产生式 A -> α
        for A, prods in grammar.productions.items():
            for prod in prods:
                # trailer 保存产生式右侧当前符号右边的 FIRST/FOLLOW 信息
                # 临时集合，记录当前符号右侧的所有可能的后继符号。
                trailer = FOLLOW[A].copy()
                # 从右向左处理每个符号 X
                for X in reversed(prod.body):
                    if X in grammar.nonterminals:
                        before = len(FOLLOW[X])
                        # 将 trailer 中的符号（去 ε）并入 FOLLOW(X)
                        FOLLOW[X] |= (trailer - {'ε'})
                        # 如果 X 能推出 ε，则 trailer ∪= FIRST(X) 去 ε
                        if 'ε' in FIRST[X]:
                            trailer |= (FIRST[X] - {'ε'})
                        else:
                            # 否则 trailer 重置为 FIRST(X)
                            trailer = FIRST[X].copy()
                        if len(FOLLOW[X]) != before:
                            changed = True
                    else:
                        # X 是终结符或 ε，则重置 trailer 为 {X}
                        trailer = {X}
    return FOLLOW
