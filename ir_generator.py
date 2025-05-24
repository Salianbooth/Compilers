from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass

@dataclass
class Node:
    """语法树节点类"""
    label: str
    children: List['Node'] = None
    value: str = None
    text: str = None

    def __post_init__(self):
        if self.children is None:
            self.children = []

# 使用四元式 (Quadruple) 表示 IR： (op, arg1, arg2, result)
Quadruple = Tuple[str, Optional[str], Optional[str], Optional[str]]

class IRBuilder:
    """中间代码生成器"""
    def __init__(self):
        self.quads: List[Quadruple] = []  # 存储生成的四元式
        self.temp_count = 0               # 临时变量计数器
        self.label_count = 0              # 标签计数器
        self.string_literals: Dict[str, str] = {}  # 存储字符串字面量

    def new_temp(self) -> str:
        """生成新的临时变量名"""
        name = f"t{self.temp_count}"
        self.temp_count += 1
        return name

    def new_label(self) -> str:
        """生成新的标签名"""
        name = f"L{self.label_count}"
        self.label_count += 1
        return name

    def emit(self, op: str,
             arg1: Optional[str] = None,
             arg2: Optional[str] = None,
             result: Optional[str] = None) -> None:
        """生成一条四元式"""
        self.quads.append((op, arg1, arg2, result))

    def gen(self, node: Node) -> Optional[str]:
        """递归生成中间代码"""
        if not node:
            return None

        label = node.label

        # 整数常量
        if label == 'INT_LITERAL':
            temp = self.new_temp()
            self.emit('LOAD_CONST', str(node.value), None, temp)
            return temp

        # 字符串常量
        if label == 'STRING_LITERAL':
            if node.value not in self.string_literals:
                self.string_literals[node.value] = f"str{len(self.string_literals)}"
            temp = self.new_temp()
            self.emit('LOAD_STR', self.string_literals[node.value], None, temp)
            return temp

        # 变量引用
        if label == 'ID':
            temp = self.new_temp()
            self.emit('LOAD_VAR', node.value, None, temp)
            return temp

        # 二元运算
        if label in ['ExprAdd', 'ExprSub', 'ExprMul', 'ExprDiv', 'ExprMod', 
                    'ExprRel', 'ExprEq', 'ExprAnd', 'ExprOr']:
            left, op_node, right = node.children
            t1 = self.gen(left)
            t2 = self.gen(right)
            temp = self.new_temp()
            self.emit(op_node.value, t1, t2, temp)
            return temp

        # 赋值语句
        if label == 'AssignStmt':
            var_node, _, expr_node = node.children
            rhs = self.gen(expr_node)
            self.emit('ASSIGN', rhs, None, var_node.value)
            return None

        # 函数调用
        if label == 'Call':
            func_name = node.value
            arg_temps = []
            for arg in node.children:
                arg_temps.append(self.gen(arg))
            # 生成参数四元式
            for at in arg_temps:
                self.emit('PARAM', at, None, None)
            temp = self.new_temp()
            self.emit('CALL', func_name, str(len(arg_temps)), temp)
            return temp

        # if 语句
        if label == 'IfStmt':
            _, _, cond_node, _, then_node, else_node = node.children
            cond_temp = self.gen(cond_node)
            label_else = self.new_label()
            label_end = self.new_label()
            # 条件跳转
            self.emit('JZ', cond_temp, None, label_else)
            # then 分支
            self.gen(then_node)
            self.emit('JMP', None, None, label_end)
            # else 分支
            self.emit('LABEL', None, None, label_else)
            self.gen(else_node)
            # 结束标签
            self.emit('LABEL', None, None, label_end)
            return None

        # while 语句
        if label == 'WhileStmt':
            _, _, cond_node, _, body_node = node.children
            start_label = self.new_label()
            end_label = self.new_label()
            # 循环开始
            self.emit('LABEL', None, None, start_label)
            cond_temp = self.gen(cond_node)
            self.emit('JZ', cond_temp, None, end_label)
            # 循环体
            self.gen(body_node)
            self.emit('JMP', None, None, start_label)
            # 循环结束
            self.emit('LABEL', None, None, end_label)
            return None

        # 复合语句
        if label == 'CompoundStmt':
            for child in node.children:
                self.gen(child)
            return None

        # 其他情况递归处理子节点
        for child in node.children:
            self.gen(child)
        return None

    def get_quads(self) -> List[Quadruple]:
        """获取生成的所有四元式"""
        return self.quads

    def get_string_literals(self) -> Dict[str, str]:
        """获取所有字符串字面量"""
        return self.string_literals

    def print_quads(self):
        """打印所有四元式"""
        print("\n生成的中间代码（四元式）：")
        for i, quad in enumerate(self.quads):
            print(f"{i:3d}: {quad}")

        if self.string_literals:
            print("\n字符串字面量表：")
            for value, name in self.string_literals.items():
                print(f"{name}: {value}")

def create_test_ast():
    """创建测试用的语法树"""
    # 测试用例1：简单的赋值和算术运算
    test1 = Node('CompoundStmt', [
        Node('AssignStmt', [
            Node('ID', value='x'),
            Node('=', value='='),
            Node('INT_LITERAL', value='10')
        ]),
        Node('AssignStmt', [
            Node('ID', value='y'),
            Node('=', value='='),
            Node('ExprAdd', [
                Node('ID', value='x'),
                Node('+', value='+'),
                Node('INT_LITERAL', value='5')
            ])
        ])
    ])

    # 测试用例2：if语句
    test2 = Node('CompoundStmt', [
        Node('AssignStmt', [
            Node('ID', value='x'),
            Node('=', value='='),
            Node('INT_LITERAL', value='10')
        ]),
        Node('IfStmt', [
            Node('if'),
            Node('('),
            Node('ExprRel', [
                Node('ID', value='x'),
                Node('>', value='>'),
                Node('INT_LITERAL', value='5')
            ]),
            Node(')'),
            Node('CompoundStmt', [
                Node('AssignStmt', [
                    Node('ID', value='y'),
                    Node('=', value='='),
                    Node('INT_LITERAL', value='1')
                ])
            ]),
            Node('CompoundStmt', [
                Node('AssignStmt', [
                    Node('ID', value='y'),
                    Node('=', value='='),
                    Node('INT_LITERAL', value='0')
                ])
            ])
        ])
    ])

    # 测试用例3：while循环
    test3 = Node('CompoundStmt', [
        Node('AssignStmt', [
            Node('ID', value='sum'),
            Node('=', value='='),
            Node('INT_LITERAL', value='0')
        ]),
        Node('AssignStmt', [
            Node('ID', value='i'),
            Node('=', value='='),
            Node('INT_LITERAL', value='1')
        ]),
        Node('WhileStmt', [
            Node('while'),
            Node('('),
            Node('ExprRel', [
                Node('ID', value='i'),
                Node('<=', value='<='),
                Node('INT_LITERAL', value='10')
            ]),
            Node(')'),
            Node('CompoundStmt', [
                Node('AssignStmt', [
                    Node('ID', value='sum'),
                    Node('=', value='='),
                    Node('ExprAdd', [
                        Node('ID', value='sum'),
                        Node('+', value='+'),
                        Node('ID', value='i')
                    ])
                ]),
                Node('AssignStmt', [
                    Node('ID', value='i'),
                    Node('=', value='='),
                    Node('ExprAdd', [
                        Node('ID', value='i'),
                        Node('+', value='+'),
                        Node('INT_LITERAL', value='1')
                    ])
                ])
            ])
        ])
    ])

    # 测试用例4：函数调用
    test4 = Node('CompoundStmt', [
        Node('AssignStmt', [
            Node('ID', value='x'),
            Node('=', value='='),
            Node('INT_LITERAL', value='5')
        ]),
        Node('AssignStmt', [
            Node('ID', value='result'),
            Node('=', value='='),
            Node('Call', [
                Node('ID', value='x')
            ], value='factorial')
        ])
    ])

    return [test1, test2, test3, test4]

if __name__ == '__main__':
    # 运行所有测试用例
    test_cases = create_test_ast()
    
    for i, test_ast in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print("-" * 50)
        irb = IRBuilder()
        irb.gen(test_ast)
        irb.print_quads() 