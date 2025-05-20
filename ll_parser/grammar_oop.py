#grammar_oop.py
from typing import List, Dict, Set

class Production:
    def __init__(self, head: str, body: List[str]):
        self.head = head
        self.body = body

    def __repr__(self):
        rhs = ' '.join(self.body) or 'ε'
        return f"{self.head} → {rhs}"


class Grammar:
    def __init__(self):
        # 存储所有产生式，键为非终结符，值为对应的 Production 列表
        self.productions: Dict[str, List[Production]] = {}
        # 非终结符集合
        self.nonterminals: Set[str] = set()
        # 终结符集合
        self.terminals: Set[str] = set()
        # 在 finalize 前暂存所有产生式右部，用于后续统一分类
        self._pending_bodies: List[List[str]] = []

    def add_prod(self, head: str, body: List[str]):
        """
        添加一条产生式，不立即判断终结符/非终结符
        head: 产生式左侧（非终结符）
        body: 产生式右侧符号列表，空列表表示 ε
        """
        prod = Production(head, body)
        # 将产生式加入字典
        self.productions.setdefault(head, []).append(prod)
        # 记录 head 为非终结符
        self.nonterminals.add(head)
        # 暂存 body，待 finalize 分类
        self._pending_bodies.append(body)

    def finalize(self,
                 eliminate_lr: bool = True,
                 left_fact: bool = True):
        """
        在所有产生式添加完成后调用：
        1) 消除直接左递归
        2) 提取左公因子
        3) 根据暂存的 body 分类终结符
        """
        if eliminate_lr:
            self._eliminate_direct_left_recursion()
        if left_fact:
            self._left_factor_all()

        # 将所有右侧符号分类：非 pending 且非非终结符的视为终结符
        all_rhs_syms = {sym for body in self._pending_bodies for sym in body}
        for sym in all_rhs_syms:
            if sym != 'ε' and sym not in self.nonterminals:
                self.terminals.add(sym)

    def _eliminate_direct_left_recursion(self):
        """
        消除所有非终结符的直接左递归：
        A → A α | β  转换为
        A → β A'
        A' → α A' | ε
        """
        new_bodies: Dict[str, List[List[str]]] = {}
        for A, prods in list(self.productions.items()):
            # alpha 保存所有左递归产生式去掉首符号后的部分。
            # A → A a | A b，则 alpha = [['a'], ['b']]。
            # beta 保存所有非左递归产生式的右侧。
            # 若 A → c | d，则 beta = [['c'], ['d']]。
            alpha, beta = [], []
            # 区分左递归产生式（形如 A → A ...）和非左递归产生式
            for p in prods:
                if p.body and p.body[0] == A:
                    # 去掉首符后的 α
                    alpha.append(p.body[1:])
                else:
                    beta.append(p.body)
            if alpha:
                # 构造新的非终结符 A'
                # 在原非终结符后添加 '（如 A'），若存在冲突则继续添加（如 A''>）。
                Aprime = A + "'"
                while Aprime in self.productions or Aprime in new_bodies:
                    Aprime += "'"
                # A -> β Aprime
                new_bodies[A] = [b + [Aprime] for b in beta]
                # Aprime -> α Aprime | ε
                new_bodies[Aprime] = [a + [Aprime] for a in alpha] + [['ε']]
            else:
                # 无左递归，保留原产生式
                new_bodies[A] = [p.body for p in prods]

        # 重建 productions
        self._rebuild_from_bodies(new_bodies)

    def _left_factor_all(self):
        """
        反复进行左公因子提取，直到所有非终结符没有可提取的公因子
        """
        while True:
            # 标记本轮循环是否进行了左因子提取。若没有，则终止循环。
            changed = False
            # 当前所有产生式右部映射
            bodies_map = {A: [p.body for p in ps]
                          for A, ps in self.productions.items()}

            for A, bodies in bodies_map.items():
                # 按首符号分组
                groups: Dict[str, List[List[str]]] = {}
                # 根据产生式右部的首符号 b[0] 分组。例如：
                # A → aB | aC | d 分组为 {'a': [['a','B'], ['a','C']], 'd': [['d']]}。
                for b in bodies:
                    key = b[0] if b else 'ε'
                    groups.setdefault(key, []).append(b)

                for key, group in groups.items():
                    # 找到首符相同且多于一条的组
                    if key != 'ε' and len(group) > 1:
                        # 新非终结符 A'
                        Aprime = A + "'"
                        while Aprime in bodies_map:
                            Aprime += "'"
                        # A 的新产生式：保留其他组 + 提取公因子项
                        others = [b for b in bodies if b[0] != key]
                        bodies_map[A] = others + [[key, Aprime]]
                        # Aprime 的产生式：去掉首符后的剩余，否则 ε
                        bodies_map[Aprime] = [(b[1:] or ['ε']) for b in group]
                        changed = True
                        break
                if changed:
                    break

            if not changed:
                break
            # 若有变动，则重建 productions 继续下一轮
            self._rebuild_from_bodies(bodies_map)

    def _rebuild_from_bodies(self,
                             bodies_map: Dict[str, List[List[str]]]):
        """
        根据给定的 bodies_map 重置 productions、nonterminals、terminals
        保证后续算法操作的是最新产生式集
        """
        # 清空原有数据
        self.productions.clear()
        self.nonterminals.clear()
        self.terminals.clear()
        pending = self._pending_bodies
        self._pending_bodies = []
        # 重新添加产生式
        for head, bodies in bodies_map.items():
            for body in bodies:
                self.add_prod(head, body)
        # 恢复 pending bodies
        self._pending_bodies = pending

    def all_prods(self) -> List[Production]:
        """返回所有 Production 对象列表"""
        return [p for ps in self.productions.values() for p in ps]

    def __repr__(self):
        # 以每行一个产生式格式化输出文法
        return '\n'.join(map(repr, self.all_prods()))


def load_grammar_from_file(filepath: str, grammar: Grammar) -> None:
        """
        从文件读取文法规则，每行格式:
          Head → alt1 | alt2 | ...
        然后自动调用 grammar.add_prod
        """
        with open(filepath, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # 拆分 head 和 rhs
                if '→' in line:
                    head, rhs = line.split('→', 1)
                elif '->' in line:
                    head, rhs = line.split('->', 1)
                else:
                    continue
                head = head.strip()
                # 每个备选分支
                alts = [alt.strip() for alt in rhs.split('|')]
                for alt in alts:
                    if alt == 'ε':
                        symbols: List[str] = []
                    else:
                        # 按空白拆分，同时去除多余的单引号
                        tokens = alt.split()
                        symbols = [tok.strip("'\" ") for tok in tokens]
                    grammar.add_prod(head, symbols)
