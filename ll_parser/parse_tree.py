from typing import List, Optional, Union

class Node:
    """
    用于表示语法树节点的简易类，可用于 CST 或 AST。

    属性：
        label: 节点标签，表示非终结符或终结符。
        children: 子节点列表。
        value: 可选的节点值（如标识符文本或字面量文本）。
    """
    def __init__(self, label: str, children: Optional[List['Node']] = None, value=None):
        self.label = label
        self.children = children or []
        self.value = value

    def is_leaf(self) -> bool:
        """判断是否为叶节点（无子节点）。"""
        return not self.children

    def add_child(self, child: 'Node'):
        """添加子节点。"""
        self.children.append(child)

    def __repr__(self):
        return f"Node({self.label!r}, {self.children}, value={self.value!r})"


def print_tree(node: Node, prefix: str = '', is_last: bool = True) -> None:
    """
    以 ASCII 的方式打印语法树，叶节点展示其 value。
    """
    connector = '└─ ' if is_last else '├─ '
    # 叶节点且有 value 时，输出 "label: value"
    if node.is_leaf() and node.value is not None:
        print(f"{prefix}{connector}{node.label}: {node.value}")
    else:
        # 非叶或无 value，单独输出标签
        if node.value is not None:
            print(f"{prefix}{connector}{node.label} = {node.value}")
        else:
            print(f"{prefix}{connector}{node.label}")
    new_prefix = prefix + ('   ' if is_last else '│  ')
    for i, child in enumerate(node.children):
        print_tree(child, new_prefix, i == len(node.children) - 1)


def cst_to_ast(cst: Node) -> Optional[Union[Node, List[Node]]]:
    """
    将具体语法树（CST）转换为简化的抽象语法树（AST）。

    转换规则：
      1. 丢弃标签为 'ε' 的空节点。
      2. 跳过中间辅助节点：标签以 'Tail'、'List' 结尾或包含 "'"。
      3. 只有一个子节点时提升该子节点。
      4. 扁平化列表节点，将其子节点展开。
      5. 叶节点保留其 value。
    """
    # 丢弃空节点
    if cst.label == 'ε':
        return None

    ast_children: List[Node] = []
    for child in cst.children:
        transformed = cst_to_ast(child)
        if transformed is None:
            continue
        # 如果 helper 展开成列表
        if isinstance(transformed, list):
            ast_children.extend(transformed)
        else:
            ast_children.append(transformed)

    # 跳过中间辅助节点
    is_helper = (
        cst.label.endswith('Tail') or
        cst.label.endswith('List') or
        ("'" in cst.label)
    )
    if is_helper:
        return ast_children

    # 只有一个子节点时提升
    if len(ast_children) == 1:
        return ast_children[0]

    # 构造 AST 节点，保留 value
    return Node(cst.label, ast_children, value=cst.value)


# ---------- 以下为示例：如何构造 CST 并打印最终 AST ----------

if __name__ == '__main__':
    # 手动构造一个简单的 CST，等价于： float pi = 3.14;
    cst = Node('Decl', [
        Node('TypeSpecifier', [ Node('float', value='float') ], value=None),
        Node('ID', value='pi'),
        Node('VarDeclPrime', [
            Node('=', value='='),
            Node('FLOAT_LITERAL', value='3.14'),
            Node(';', value=';')
        ])
    ])

    # 将 CST 转为 AST
    ast = cst_to_ast(cst)

    # 打印 AST（含标签和值）
    print_tree(ast)
