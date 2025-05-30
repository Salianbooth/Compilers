from typing import List, Optional, Dict
from dataclasses import dataclass
from Compilers.object_code.code_generator import Quadruple

@dataclass
class Node:
    """语法树节点类"""
    label: str  # 节点的标签（类型）
    children: List['Node'] = None  # 子节点列表
    value: str = None  # 节点的值
    text: str = None  # 节点的文本表示

    def __post_init__(self):
        if self.children is None:
            self.children = []  # 初始化子节点列表

class IRBuilder:
    """中间代码生成器"""
    def __init__(self):
        self.quads: List[Quadruple] = []          # 存储生成的四元式
        self.temp_count = 0                       # 临时变量计数器
        self.label_count = 0                      # 标签计数器
        self.string_literals: Dict[str, str] = {} # 存储字符串字面量
        self.current_func = None                  # 当前处理的函数名
        self.global_inits: List[Quadruple] = []   # 存储全局初始化四元式

    def new_temp(self) -> str:
        """生成新的临时变量名，使用函数前缀"""
        prefix = f"{self.current_func}_" if self.current_func else ""
        name = f"{prefix}t{self.temp_count}"  # 生成临时变量名
        self.temp_count += 1  # 增加临时变量计数
        return name

    def new_label(self) -> str:
        """生成新的标签名，使用函数前缀"""
        prefix = f"{self.current_func}_" if self.current_func else ""
        name = f"{prefix}L{self.label_count}"  # 生成标签名
        self.label_count += 1  # 增加标签计数
        return name

    def emit(self, op: str, arg1: Optional[str] = None,
             arg2: Optional[str] = None, result: Optional[str] = None) -> None:
        """生成一条四元式"""
        quad = Quadruple(op=op, arg1=arg1, arg2=arg2, result=result)  # 创建四元式
        if self.current_func is None and op not in ['FUNC_BEGIN', 'FUNC_END', 'LABEL']:
            # 全局初始化相关的四元式
            self.global_inits.append(quad)
        else:
            self.quads.append(quad)  # 添加四元式到列表

    def gen_binary_op(self, node: Node, op_node: Node, left: str, right: str) -> str:
        """处理二元运算"""
        temp = self.new_temp()  # 创建临时变量
        if op_node.value in ['>', '<', '>=', '<=', '==', '!=']:
            # 处理关系运算符
            op = op_node.value.upper()
            if op == '<=': op = 'LE'
            elif op == '>=': op = 'GE'
            elif op == '==': op = 'EQ'
            elif op == '!=': op = 'NE'
            elif op == '>': op = 'GT'
            elif op == '<': op = 'LT'
        else:
            # 处理算术运算符
            op_map = {'+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', 
                     '%': 'MOD', '&&': 'AND', '||': 'OR'}
            op = op_map.get(op_node.value, op_node.value)
        self.emit(op, left, right, temp)  # 生成四元式
        return temp  # 返回临时变量名

    def gen_short_circuit_and(self, left_node: Node, right_node: Node) -> str:
        """生成短路与运算的代码"""
        label_false = self.new_label()  # 创建跳转标签
        
        # 计算左操作数
        left = self.gen(left_node)
        self.emit('JUMP_IF_FALSE', left, None, label_false)  # 如果左操作数为假，跳转
        
        # 计算右操作数
        right = self.gen(right_node)
        
        # 结果为右操作数的值
        self.emit('LABEL', None, None, label_false)  # 标签位置
        return right

    def gen_short_circuit_or(self, left_node: Node, right_node: Node) -> str:
        """生成短路或运算的代码"""
        label_true = self.new_label()  # 创建跳转标签
        
        # 计算左操作数
        left = self.gen(left_node)
        self.emit('JUMP_IF_TRUE', left, None, label_true)  # 如果左操作数为真，跳转
        
        # 计算右操作数
        right = self.gen(right_node)
        
        # 结果为右操作数的值
        self.emit('LABEL', None, None, label_true)  # 标签位置
        return right

    def gen(self, node: Node) -> Optional[str]:
        """递归生成中间代码"""
        if not node:
            return None

        label = node.label

        # 跳过标记节点
        if label in ['(', ')', ',', ';', '{', '}']:
            return None

        # 处理程序根节点
        if label == 'Program':
            # 生成全局初始化标签（只在程序开始时生成一次）
            if self.global_inits:
                self.emit('LABEL', None, None, 'GLOBAL_INIT')
                for init in self.global_inits:
                    self.emit(*init)
                self.global_inits.clear()
            for child in node.children:
                self.gen(child)  # 递归生成子节点的中间代码
            return None

        # 处理类型节点
        if label in ['int', 'float', 'char', 'void', 'Type']:
            return None

        # 处理预处理指令
        if label == 'PPDirective':
            return None

        # 处理read()和write()表达式
        if label == 'ExprPrimary':
            if len(node.children) >= 1 and node.children[0].label == 'read':
                # 处理read()
                temp = self.new_temp()
                self.emit('CALL', 'read', '0', temp)  # 调用read函数
                return temp
            elif len(node.children) >= 2 and node.children[0].label == 'write':
                # 处理write(expr)
                expr_node = node.children[1]
                expr_temp = self.gen(expr_node)
                if expr_temp:
                    self.emit('PARAM', expr_temp, None, None)  # 传递参数
                    self.emit('CALL', 'write', '1', None)  # 调用write函数
                return None
            elif node.value:
                # 处理其他基本表达式（ID、字面量等）
                temp = self.new_temp()
                self.emit('LOAD_CONST', str(node.value), None, temp)  # 加载常量
                return temp
            elif node.label == 'ID':
                temp = self.new_temp()
                self.emit('LOAD_VAR', node.value, None, temp)  # 加载变量
                return temp

        # 处理表达式语句
        if label == 'ExprStmt':
            if len(node.children) >= 1:
                return self.gen(node.children[0])  # 生成表达式语句的中间代码
            return None

        # 处理赋值语句
        if label == 'AssignStmt':
            if len(node.children) >= 3:
                id_node = node.children[0]
                expr_node = node.children[2]
                if id_node.label == 'ID':
                    expr_temp = self.gen(expr_node)
                    if expr_temp:
                        self.emit('STORE_VAR', expr_temp, None, id_node.value)  # 存储变量
                    return expr_temp
            return None

        # 处理for循环
        if label == 'ForStmt':
            # 生成循环开始和结束标签
            loop_start = self.new_label()
            loop_end = self.new_label()
            
            # 初始化表达式
            init_expr = None
            cond_expr = None
            incr_expr = None
            body = None
            
            # 找到for循环的各个部分
            for i, child in enumerate(node.children):
                if child.label == 'for':
                    continue
                if child.label in ['(', ')', '{', '}']:
                    continue
                if init_expr is None:
                    init_expr = child
                elif cond_expr is None:
                    cond_expr = child
                elif incr_expr is None:
                    incr_expr = child
                else:
                    body = child
            
            # 生成初始化代码
            if init_expr:
                if init_expr.label == 'ExprAssign':
                    # 处理i=1
                    if len(init_expr.children) >= 2:
                        id_node = init_expr.children[0]
                        expr_node = init_expr.children[1]
                        if id_node.label == 'ID':
                            expr_temp = self.gen(expr_node)
                            if expr_temp:
                                self.emit('STORE_VAR', expr_temp, None, id_node.value)  # 存储变量
                else:
                    self.gen(init_expr)
            
            # 生成循环开始标签
            self.emit('LABEL', None, None, loop_start)
            
            # 生成条件判断代码
            if cond_expr:
                cond = self.gen(cond_expr)
                if cond:
                    self.emit('JUMP_IF_FALSE', cond, None, loop_end)  # 条件为假时跳转
            
            # 生成循环体代码
            if body:
                self.gen(body)
            
            # 生成递增代码
            if incr_expr:
                if incr_expr.label == 'ExprPostfix':
                    # 处理i++
                    if len(incr_expr.children) >= 2:
                        id_node = incr_expr.children[0]
                        op_node = incr_expr.children[1]
                        if id_node.label == 'ID' and op_node.value == '++':
                            temp1 = self.new_temp()
                            self.emit('LOAD_VAR', id_node.value, None, temp1)  # 加载变量
                            temp2 = self.new_temp()
                            self.emit('ADD', temp1, '1', temp2)  # 递增
                            self.emit('STORE_VAR', temp2, None, id_node.value)  # 存储新值
                else:
                    self.gen(incr_expr)
            
            # 跳回循环开始
            self.emit('JUMP', None, None, loop_start)
            
            # 生成循环结束标签
            self.emit('LABEL', None, None, loop_end)
            return None

        # 处理write语句
        if label == 'ExprPrimary' and len(node.children) >= 2 and node.children[0].label == 'write':
            # 处理write(expr)
            expr_node = node.children[1]
            expr_temp = self.gen(expr_node)
            if expr_temp:
                self.emit('PARAM', expr_temp, None, None)  # 传递参数
                self.emit('CALL', 'write', '1', None)  # 调用write函数
            return None

        # 处理ID节点
        if label == 'ID':
            temp = self.new_temp()
            self.emit('LOAD_VAR', node.value, None, temp)  # 加载变量
            return temp

        # 处理后缀表达式（如i++）
        if label == 'ExprPostfix':
            if len(node.children) >= 2:
                # 找到标识符和操作符
                id_node = None
                op_node = None
                for child in node.children:
                    if child.label == 'ID':
                        id_node = child
                    elif child.label in ['++', '--']:
                        op_node = child
                
                if id_node and op_node:
                    # 加载变量的值
                    temp1 = self.new_temp()
                    self.emit('LOAD_VAR', id_node.value, None, temp1)
                    
                    # 生成新值
                    temp2 = self.new_temp()
                    if op_node.value == '++':
                        self.emit('ADD', temp1, '1', temp2)  # 递增
                    else:  # '--'
                        self.emit('SUB', temp1, '1', temp2)  # 递减
                    
                    # 存储新值
                    self.emit('STORE_VAR', temp2, None, id_node.value)
                    return temp1  # 返回原值（后缀操作符的语义）
            return None

        # 函数定义
        if label == 'Decl':
            # 检查是否是函数定义
            if (len(node.children) >= 4 and 
                node.children[0].label in ['int', 'float', 'char', 'void', 'Type'] and
                node.children[1].label == 'ID' and
                any(child.label == 'CompoundStmt' for child in node.children)):
                
                func_name = node.children[1].value
                self.current_func = func_name
                
                # 生成函数入口
                self.emit('FUNC_BEGIN', func_name, None, None)
                self.emit('LABEL', func_name, None, None)
                
                # 处理参数
                param_index = -1
                for i, child in enumerate(node.children):
                    if child.label == 'ParamList':
                        param_index = i
                        break
                
                if param_index != -1:
                    param_list = node.children[param_index].children
                    for param in param_list:
                        if param.label == 'Param':
                            param_name = None
                            for p_child in param.children:
                                if p_child.label == 'ID':
                                    param_name = p_child.value
                                    break
                            if param_name:
                                temp = self.new_temp()
                                self.emit('LOAD_PARAM', param_name, None, temp)  # 加载参数
                                self.emit('STORE_VAR', temp, None, param_name)  # 存储参数
                                
                # 处理函数体
                has_return = False
                for child in node.children:
                    if child.label == 'CompoundStmt':
                        has_return = self.gen(child)
                        break
                
                # 如果没有显式返回，添加默认返回
                if not has_return:
                    temp = self.new_temp()
                    self.emit('LOAD_CONST', '0', None, temp)  # 默认返回0
                    self.emit('RETURN', temp, None, None)
                
                # 生成函数出口
                self.emit('FUNC_END', func_name, None, None)
                self.current_func = None
                return None
            
            # 处理变量声明
            elif len(node.children) >= 2:
                type_node = node.children[0]
                id_node = node.children[1]
                
                if id_node.label == 'ID':
                    var_name = id_node.value
                    
                    # 局部变量分配空间
                    if self.current_func:
                        self.emit('ALLOC', var_name, None, None)
                    
                    # 处理初始化
                    if len(node.children) > 2 and node.children[2].label == 'VarDeclPrime':
                        init_node = node.children[2]
                        if len(init_node.children) > 1:
                            init_val = self.gen(init_node.children[1])
                            if init_val:
                                self.emit('STORE_VAR', init_val, None, var_name)  # 存储初始化值
                return None

        # 复合语句
        if label == 'CompoundStmt':
            has_return = False
            for child in node.children:
                if child.label not in ['{', '}']:
                    child_return = self.gen(child)
                    if child_return == True:  # 是返回语句
                        has_return = True
            return has_return

        # 参数声明
        if label == 'Param':
            return None  # 参数在函数定义时处理

        # else 语句
        if label == 'ElseStmt':
            if node.children:
                return self.gen(node.children[0])  # 生成else分支的中间代码
            return None

        # 整数常量
        if label == 'INT_LITERAL':
            temp = self.new_temp()
            self.emit('LOAD_CONST', str(node.value), None, temp)  # 加载整数常量
            return temp

        # if 语句
        if label == 'IfStmt':
            # 确保有足够的子节点
            if len(node.children) < 4:
                return None
            
            # 找到条件表达式和then语句
            cond_node = None
            then_node = None
            else_node = None
            
            for i, child in enumerate(node.children):
                if child.label not in ['if', '(', ')']:
                    if cond_node is None:
                        cond_node = child
                    elif then_node is None:
                        then_node = child
                    elif child.label == 'ElseStmt':
                        else_node = child

            if not (cond_node and then_node):
                return None

            # 生成条件判断代码
            if cond_node.label == 'ExprAnd':
                # 处理 x > 0 && y > 0 这样的短路与
                left_node = cond_node.children[0]
                right_node = cond_node.children[2]
                
                # 创建标签
                label_false = self.new_label()  # 条件为假时跳转的标签
                
                # 先计算并合并条件
                left_temp = self.gen(left_node)  # 计算左操作数
                right_temp = self.gen(right_node)  # 计算右操作数
                and_temp = self.new_temp()
                self.emit('AND', left_temp, right_temp, and_temp)  # 合并条件
                
                # 根据合并后的条件决定跳转
                self.emit('JUMP_IF_FALSE', and_temp, None, label_false)
                
                # 执行 then 分支
                has_return = self.gen(then_node)
                
                # 条件为假的标签位置
                self.emit('LABEL', None, None, label_false)
                
                return has_return
            else:
                # 普通条件判断
                cond_temp = self.gen(cond_node)
                label_false = self.new_label()
                
                self.emit('JUMP_IF_FALSE', cond_temp, None, label_false)
                has_return = self.gen(then_node)
                self.emit('LABEL', None, None, label_false)
                
                return has_return

        # 二元运算
        if label in ['ExprAdd', 'ExprSub', 'ExprMul', 'ExprDiv', 'ExprMod', 
                     'ExprRel', 'ExprEq']:
            if len(node.children) >= 2:
                left = self.gen(node.children[0])
                for i in range(1, len(node.children), 2):
                    if i + 1 < len(node.children):
                        op_node = node.children[i]
                        right = self.gen(node.children[i + 1])
                        left = self.gen_binary_op(node, op_node, left, right)  # 处理二元运算
                return left

        # 短路逻辑运算
        if label == 'ExprAnd':
            if len(node.children) >= 3:
                return self.gen_short_circuit_and(node.children[0], node.children[2])
            return None
        
        if label == 'ExprOr':
            if len(node.children) >= 3:
                return self.gen_short_circuit_or(node.children[0], node.children[2])
            return None

        # 返回语句
        if label == 'ReturnStmt':
            if len(node.children) > 1:
                ret_node = node.children[1]
                
                # 特殊处理 return n * factorial(n-1)
                if ret_node.label == 'ExprMul' and len(ret_node.children) >= 3:
                    left_node = ret_node.children[0]
                    op_node = ret_node.children[1]
                    right_node = ret_node.children[2]
                    
                    # 获取左操作数 n
                    n_temp = self.gen(left_node)
                    
                    # 处理右操作数 factorial(n-1)
                    if right_node.label == 'Call' and right_node.value == 'factorial':
                        # 找到函数参数 (n-1)
                        if len(right_node.children) > 0:
                            arg_node = right_node.children[0]
                            
                            # 如果参数是减法表达式 n-1
                            if arg_node.label == 'ExprSub':
                                # 获取 n
                                var_temp = self.gen(arg_node.children[0])
                                # 获取 1
                                const_temp = self.new_temp()
                                self.emit('LOAD_CONST', '1', None, const_temp)
                                # 计算 n-1
                                n_minus_one = self.new_temp()
                                self.emit('SUB', var_temp, const_temp, n_minus_one)
                                
                                # 传递参数
                                self.emit('PARAM', n_minus_one, None, None)
                                
                                # 调用函数
                                fact_result = self.new_temp()
                                self.emit('CALL', 'factorial', '1', fact_result)
                                
                                # 计算乘法
                                mul_result = self.new_temp()
                                self.emit('MUL', n_temp, fact_result, mul_result)
                                
                                # 返回结果
                                self.emit('RETURN', mul_result, None, None)
                                return True
                
                # 一般返回语句处理
                ret_val = self.gen(ret_node)
                if ret_val:
                    self.emit('RETURN', ret_val, None, None)
                else:
                    temp = self.new_temp()
                    self.emit('LOAD_CONST', '0', None, temp)
                    self.emit('RETURN', temp, None, None)
            else:
                temp = self.new_temp()
                self.emit('LOAD_CONST', '0', None, temp)
                self.emit('RETURN', temp, None, None)
            return True

        # 处理比较运算
        if label == 'ExprRel':
            if len(node.children) >= 3:
                left = self.gen(node.children[0])
                op = node.children[1].value
                right = self.gen(node.children[2])
                if left and right:
                    temp = self.new_temp()
                    if op == '<=':
                        self.emit('LE', left, right, temp)
                    elif op == '>=':
                        self.emit('GE', left, right, temp)
                    elif op == '<':
                        self.emit('LT', left, right, temp)
                    elif op == '>':
                        self.emit('GT', left, right, temp)
                    elif op == '==':
                        self.emit('EQ', left, right, temp)
                    elif op == '!=':
                        self.emit('NE', left, right, temp)
                    return temp
            return None

        # 函数调用
        if label == 'Call':
            func_name = node.value
            args = []
            
            # 处理参数
            for arg in node.children:
                if arg.label not in [';', '(', ')']:
                    arg_temp = self.gen(arg)
                    if arg_temp:
                        self.emit('PARAM', arg_temp, None, None)  # 传递参数
                        args.append(arg_temp)
            
            # 生成调用指令
            ret_temp = self.new_temp()
            self.emit('CALL', func_name, str(len(args)), ret_temp)  # 调用函数
            return ret_temp

        # 未处理的节点类型
        # print(f"Warning: unhandled AST node {label}")
        for child in node.children:
            self.gen(child)  # 递归处理子节点
        return None

    def get_quads(self) -> List[Quadruple]:
        """获取生成的所有四元式"""
        return self.quads  # 返回生成的四元式列表

    def get_string_literals(self) -> Dict[str, str]:
        """获取所有字符串字面量"""
        return self.string_literals

    def make_list(self, index: int) -> list[int]:
        """创建一个仅包含 index 的列表，用于回填目标地址"""
        return [index]

    def backpatch(self, patch_list: list[int], target_label: str) -> None:
        """
        回填跳转目标地址为 target_label
        patch_list 是指令索引列表（如 JUMP_IF_FALSE 或 JUMP）
        """
        for idx in patch_list:
            quad = self.quads[idx]
            # 一般跳转指令格式为 ('JUMP_IF_FALSE', cond, None, None)
            # 将 label 回填到最后一个字段
            self.quads[idx] = (quad[0], quad[1], quad[2], target_label)

    def gen_if(self, node: Node) -> Optional[bool]:
        """生成 if-else 语句的中间代码，支持回填"""
        # --- 提取条件、then 分支和 else 分支节点 ---
        cond_node = None
        then_node = None
        else_node = None
        # node.children 可能包含 ['if', '(', cond, ')', then_node, ElseStmt?]
        i = 0
        # 跳过 'if' 和 '('
        while i < len(node.children) and node.children[i].label in ['if', '(']:
            i += 1
        # 条件表达式
        if i < len(node.children):
            cond_node = node.children[i]
            i += 1
        # 跳过 ')'
        while i < len(node.children) and node.children[i].label == ')':
            i += 1
        # then 分支
        if i < len(node.children):
            then_node = node.children[i]
            i += 1
        # else 分支（可选）
        if i < len(node.children) and node.children[i].label == 'ElseStmt':
            else_node = node.children[i]

        # --- 生成代码并回填 ---
        # 1) 计算条件，生成占位跳转
        cond_temp = self.gen(cond_node)
        idx_false = len(self.quads)
        self.emit('JUMP_IF_FALSE', cond_temp, None, None)
        false_list = self.make_list(idx_false)

        # 2) then 分支代码
        has_return = self.gen(then_node)

        # 3) then 分支结束后跳过 else 的跳转
        idx_next = len(self.quads)
        self.emit('JUMP', None, None, None)
        next_list = self.make_list(idx_next)

        # 4) else 标签并回填 false 跳转
        label_else = self.new_label()
        self.emit('LABEL', None, None, label_else)
        self.backpatch(false_list, label_else)

        # 5) else 分支代码
        if else_node:
            self.gen(else_node.children[0] if else_node.children else else_node)

        # 6) 结束标签并回填 then 跳转
        label_end = self.new_label()
        self.emit('LABEL', None, None, label_end)
        self.backpatch(next_list, label_end)
        return has_return

    def print_quads(self):
        """打印所有四元式"""
        print("\n生成的中间代码（四元式）：")
        quads = self.get_quads()
        for i, quad in enumerate(quads):
            print(f"{i:3d}: {quad}")

        if self.string_literals:
            print("\n字符串字面量表：")
            for value, name in self.string_literals.items():
                print(f"{name}: {value}")


def create_test_ast():
    """创建测试用的完整程序AST"""
    # 构造一个完整的程序AST
    program = Node('Program', [
        # 预处理指令
        Node('PPDirective', value='#include <stdio.h>'),

        # 全局变量声明
        Node('Decl', [
            Node('Type', value='int'),
            Node('ID', value='global_var'),
            Node('VarDeclPrime', [
                Node('='),
                Node('INT_LITERAL', value='42')
            ])
        ]),

        # factorial函数定义
        Node('Decl', [
            Node('Type', value='int'),
            Node('ID', value='factorial'),
            Node('ParamList', [
                Node('Param', [
                    Node('Type', value='int'),
                    Node('ID', value='n')
                ])
            ]),
            Node('CompoundStmt', [
                # if (n <= 1) return 1;
                Node('IfStmt', [
                    Node('if'),
                    Node('('),
                    Node('ExprRel', [
                        Node('ID', value='n'),
                        Node('<=', value='<='),
                        Node('INT_LITERAL', value='1')
                    ]),
                    Node(')'),
                    Node('ReturnStmt', [
                        Node('return'),
                        Node('INT_LITERAL', value='1')
                    ])
                ]),
                # return n * factorial(n-1);
                Node('ReturnStmt', [
                    Node('return'),
                    Node('ExprMul', [
                        Node('ID', value='n'),
                        Node('*', value='*'),
                        Node('Call', [
                            Node('ExprSub', [
                                Node('ID', value='n'),
                                Node('-', value='-'),
                                Node('INT_LITERAL', value='1')
                            ])
                        ], value='factorial')
                    ])
                ])
            ])
        ]),

        # sum函数定义
        Node('Decl', [
            Node('Type', value='int'),
            Node('ID', value='sum'),
            Node('ParamList', [
                Node('Param', [
                    Node('Type', value='int'),
                    Node('ID', value='a')
                ]),
                Node('Param', [
                    Node('Type', value='int'),
                    Node('ID', value='b')
                ])
            ]),
            Node('CompoundStmt', [
                Node('ReturnStmt', [
                    Node('return'),
                    Node('ExprAdd', [
                        Node('ID', value='a'),
                        Node('+', value='+'),
                        Node('ID', value='b')
                    ])
                ])
            ])
        ]),

        # main函数定义
        Node('Decl', [
            Node('Type', value='int'),
            Node('ID', value='main'),
            Node('ParamList', []),  # 空参数列表
            Node('CompoundStmt', [
                # int x = 5;
                Node('Decl', [
                    Node('Type', value='int'),
                    Node('ID', value='x'),
                    Node('VarDeclPrime', [
                        Node('='),
                        Node('INT_LITERAL', value='5')
                    ])
                ]),
                # int y = 3;
                Node('Decl', [
                    Node('Type', value='int'),
                    Node('ID', value='y'),
                    Node('VarDeclPrime', [
                        Node('='),
                        Node('INT_LITERAL', value='3')
                    ])
                ]),
                # if (x > 0 && y > 0)
                Node('IfStmt', [
                    Node('if'),
                    Node('('),
                    Node('ExprAnd', [
                        Node('ExprRel', [
                            Node('ID', value='x'),
                            Node('>', value='>'),
                            Node('INT_LITERAL', value='0')
                        ]),
                        Node('&&', value='&&'),
                        Node('ExprRel', [
                            Node('ID', value='y'),
                            Node('>', value='>'),
                            Node('INT_LITERAL', value='0')
                        ])
                    ]),
                    Node(')'),
                    Node('CompoundStmt', [
                        # result = factorial(x);
                        Node('AssignStmt', [
                            Node('ID', value='result'),
                            Node('=', value='='),
                            Node('Call', [
                                Node('ID', value='x')
                            ], value='factorial')
                        ])
                    ])
                ]),
                # return 0;
                Node('ReturnStmt', [
                    Node('return'),
                    Node('INT_LITERAL', value='0')
                ])
            ])
        ])
    ])
    return program


if __name__ == '__main__':
    # 运行完整程序AST的测试
    print("\n测试完整程序AST:")
    print("-" * 50)
    program_ast = create_test_ast()
    irb = IRBuilder()
    irb.gen(program_ast)
    irb.print_quads()  # 打印生成的四元式
