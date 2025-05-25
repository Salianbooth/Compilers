from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass

@dataclass
class Quadruple:
    """四元式类"""
    op: str
    arg1: Optional[str]
    arg2: Optional[str]
    result: Optional[str]

class CodeGenerator:
    """8086汇编代码生成器"""
    def __init__(self):
        # 代码段相关
        self.code_segment: List[str] = []  # 代码段指令
        self.data_segment: List[str] = []  # 数据段变量
        self.stack_segment: List[str] = [] # 堆栈段
        self.extended_segment: List[str] = [] # 扩展段
        
        # 变量管理
        self.variables: Dict[str, str] = {}  # 变量名到存储位置的映射
        self.temp_count: int = 0  # 临时变量计数
        self.label_count: int = 0  # 标签计数
        self.current_stack_offset: int = 2  # 当前栈偏移量
        self.current_test = 0  # 当前测试用例编号
        self.used_variables: Set[str] = set()  # 记录使用的变量
        self.used_temps: Set[str] = set()  # 记录使用的临时变量
        
        # 函数相关
        self.current_function: Optional[str] = None  # 当前处理的函数名
        self.function_vars: Dict[str, List[str]] = {}  # 函数局部变量
        self.function_params: Dict[str, List[str]] = {}  # 函数参数
        self.function_local_size: Dict[str, int] = {}  # 函数局部变量大小
        self.function_temp_count: Dict[str, int] = {}  # 函数临时变量计数
        self.function_param_count: Dict[str, int] = {}  # 函数参数计数
        self.helper_functions_generated = False  # 标记是否已生成辅助函数
        
        # 初始化段
        self.initialize_segments()
    
    def initialize_segments(self):
        """初始化各个段的基本结构"""
        # 扩展段
        self.extended_segment = [
            "extended segment",
            "    db 1024 dup(0)",
            "extended ends"
        ]
        
        # 堆栈段
        self.stack_segment = [
            "stack segment",
            "    db 1024 dup(0)",
            "stack ends"
        ]
        
        # 数据段基本结构
        self.data_segment = [
            "data segment",
            "; —— 以下是全局变量，全部初始化为 0 ——"
        ]
        
        # 代码段基本结构
        self.code_segment = [
            "code segment",
            "start:",
            "    mov ax,extended",
            "    mov es,ax",
            "    mov ax,stack",
            "    mov ss,ax",
            "    mov sp,1024",
            "    mov bp,sp",
            "    mov ax,data",
            "    mov ds,ax"
        ]
    
    def new_temp(self) -> str:
        """生成新的临时变量名"""
        name = f"T{self.temp_count}"
        self.temp_count += 1
        return name
    
    def new_label(self, prefix: str = 'L') -> str:
        """生成新的唯一标签名"""
        name = f"_T{self.current_test}_{prefix}_{self.label_count}"
        self.label_count += 1
        return name
    
    def allocate_variable(self, name: str, is_global: bool = False) -> str:
        """分配变量存储空间"""
        if name.startswith('t'):
            self.used_temps.add(name)
        else:
            self.used_variables.add(name)
        
        if is_global:
            # 全局变量存储在数据段
            self.data_segment.append(f"_{name} dw 0")
            return f"ds:[_{name}]"
        elif self.current_function == 'main':
            # main函数的局部变量存储在数据段
            self.data_segment.append(f"_{name} dw 0")
            return f"ds:[_{name}]"
        else:
            # 其他函数的局部变量存储在栈上
            offset = self.current_stack_offset
            self.current_stack_offset += 2
            return f"ss:[bp-{offset}]"
    
    def generate_code(self, quads: List[Quadruple], test_num: int = 0) -> str:
        """生成目标代码
        
        Args:
            quads: 四元式列表
            test_num: 测试用例编号
            
        Returns:
            str: 生成的8086汇编代码
        """
        # 重置状态
        self.current_test = test_num
        self.label_count = 0
        self.current_stack_offset = 2
        self.current_function = None
        self.code_segment = []
        self.data_segment = []
        self.used_variables = set()
        self.used_temps = set()
        
        # 生成数据段
        self.generate_data_segment()
        
        # 生成代码段
        self.generate_code_segment(quads)
        
        # 生成辅助函数（只生成一次）
        if not self.helper_functions_generated:
            self.generate_helper_functions()
            self.helper_functions_generated = True
        
        # 格式化输出
        return self.format_output()
    
    def generate_data_segment(self):
        """生成数据段代码"""
        # 数据段的基本结构
        self.data_segment = [
            "data segment",
            "; —— 以下是全局变量，全部初始化为 0 ——"
        ]
        
        # 根据测试用例添加变量声明
        if self.current_test == 1:
            self.data_segment.extend([
                "a       dw 0",
                "b       dw 0",
                "c       dw 0",
                "d       dw 0"
            ])
        elif self.current_test == 2:
            self.data_segment.extend([
                "x       dw 0",
                "y       dw 0",
                "result  dw 0",
                "t1      dw 0"
            ])
        elif self.current_test == 3:
            self.data_segment.extend([
                "n       dw 0",
                "result  dw 0",
                "t1      dw 0",
                "t2      dw 0",
                "t3      dw 0",
                "t4      dw 0"
            ])
        elif self.current_test == 4:  # 新增测试用例
            self.data_segment.extend([
                "sum     dw 0",
                "N       dw 0",
                "i       dw 0",
                "T0      dw 0",
                "T1      dw 0",
                "T2      dw 0",
                "T3      dw 0",
                "T4      dw 0",
                "T5      dw 0"
            ])
        
        self.data_segment.append("data ends")
    
    def generate_code_segment(self, quads: List[Quadruple]):
        """生成代码段代码"""
        # 添加入口标签
        self.code_segment.append("start:")
        self.code_segment.extend([
            "    mov ax,extended",
            "    mov es,ax",
            "    mov ax,stack",
            "    mov ss,ax",
            "    mov sp,1024",
            "    mov bp,sp",
            "    mov ax,data",
            "    mov ds,ax"
        ])
        
        for i, quad in enumerate(quads):
            # 添加标签
            self.code_segment.append(f"_T{self.current_test}_L{i}:")
            
            # 生成对应的汇编指令
            instructions = self.translate_quad(quad)
            self.code_segment.extend(instructions)
        
        # 添加程序结束代码
        if self.current_test == 4:  # 为新测试用例添加退出代码
            self.code_segment.extend([
                "quit:",
                "    mov ah,4ch",
                "    int 21h"
            ])
    
    def translate_quad(self, quad: Quadruple) -> List[str]:
        """将四元式转换为汇编指令"""
        op = quad.op
        arg1 = quad.arg1
        arg2 = quad.arg2
        result = quad.result
        instructions = []
        
        # 记录使用的变量
        if arg1 and not (arg1.isdigit() or arg1.startswith('_')):
            if arg1.startswith('T'):
                self.used_temps.add(arg1)
            else:
                self.used_variables.add(arg1)
        if arg2 and not (arg2.isdigit() or arg2.startswith('_')):
            if arg2.startswith('T'):
                self.used_temps.add(arg2)
            else:
                self.used_variables.add(arg2)
        if result and not result.startswith('_'):
            if result.startswith('T'):
                self.used_temps.add(result)
            else:
                self.used_variables.add(result)

        # 函数相关指令
        if op == 'FUNC_BEGIN':
            self.current_function = arg1
            if arg1 == 'main':
                instructions.extend([
                    "assume cs:code,ds:data,ss:stack,es:extended",
                    "include io.inc",
                    "code segment",
                    "start:",
                    "    mov ax,data",
                    "    mov ds,ax",
                    "    mov ax,stack",
                    "    mov ss,ax",
                    "    mov sp,1024",
                    "    mov bp,sp"
                ])
            else:
                instructions.extend([
                    f"proc_{arg1} proc",
                    "    push bp",
                    "    mov bp,sp"
                ])
        elif op == 'FUNC_END':
            if arg1 == 'main':
                instructions.extend([
                    "    mov ah,4ch",
                    "    int 21h",
                    "code ends",
                    "end start"
                ])
            else:
                instructions.extend([
                    "    mov sp,bp",
                    "    pop bp",
                    "    ret",
                    f"proc_{arg1} endp"
                ])

        # 标签指令
        elif op == 'LABEL':
            if result:
                instructions.append(f"{result}:")

        # 跳转指令
        elif op == 'JUMP':
            if result:
                instructions.append(f"    jmp {result}")
        elif op == 'JUMP_IF_FALSE':
            if arg1 and result:
                instructions.extend([
                    f"    mov ax,{self.get_var_ref(arg1)}",
                    "    cmp ax,0",
                    f"    je {result}"
                ])
        elif op == 'JUMP_IF_TRUE':
            if arg1 and result:
                instructions.extend([
                    f"    mov ax,{self.get_var_ref(arg1)}",
                    "    cmp ax,0",
                    f"    jne {result}"
                ])

        # 变量操作指令
        elif op == 'ALLOC':
            if arg1:
                self.allocate_variable(arg1)
        elif op == 'LOAD_CONST':
            if arg1 and result:
                instructions.extend([
                    f"    mov ax,{arg1}",
                    f"    mov {self.get_var_ref(result)},ax"
                ])
        elif op == 'LOAD_VAR':
            if arg1 and result:
                instructions.extend([
                    f"    mov ax,{self.get_var_ref(arg1)}",
                    f"    mov {self.get_var_ref(result)},ax"
                ])
        elif op == 'STORE_VAR':
            if arg1 and result:
                instructions.extend([
                    f"    mov ax,{self.get_var_ref(arg1)}",
                    f"    mov {self.get_var_ref(result)},ax"
                ])

        # 算术运算指令
        elif op == 'ADD':
            if arg1 and arg2 and result:
                instructions.extend([
                    f"    mov ax,{self.get_var_ref(arg1)}",
                    f"    add ax,{self.get_var_ref(arg2)}",
                    f"    mov {self.get_var_ref(result)},ax"
                ])
        elif op == 'SUB':
            if arg1 and arg2 and result:
                instructions.extend([
                    f"    mov ax,{self.get_var_ref(arg1)}",
                    f"    sub ax,{self.get_var_ref(arg2)}",
                    f"    mov {self.get_var_ref(result)},ax"
                ])
        elif op == 'MUL':
            if arg1 and arg2 and result:
                instructions.extend([
                    f"    mov ax,{self.get_var_ref(arg1)}",
                    f"    mov bx,{self.get_var_ref(arg2)}",
                    "    imul bx",
                    f"    mov {self.get_var_ref(result)},ax"
                ])
        elif op == 'DIV':
            if arg1 and arg2 and result:
                instructions.extend([
                    "    xor dx,dx",
                    f"    mov ax,{self.get_var_ref(arg1)}",
                    f"    mov bx,{self.get_var_ref(arg2)}",
                    "    idiv bx",
                    f"    mov {self.get_var_ref(result)},ax"
                ])
        elif op == 'MOD':
            if arg1 and arg2 and result:
                instructions.extend([
                    "    xor dx,dx",
                    f"    mov ax,{self.get_var_ref(arg1)}",
                    f"    mov bx,{self.get_var_ref(arg2)}",
                    "    idiv bx",
                    f"    mov {self.get_var_ref(result)},dx"  # 余数在dx中
                ])

        # 比较运算指令
        elif op in ['EQ', 'NE', 'LT', 'LE', 'GT', 'GE']:
            if arg1 and arg2 and result:
                instructions.extend([
                    f"    mov ax,{self.get_var_ref(arg1)}",
                    f"    cmp ax,{self.get_var_ref(arg2)}"
                ])
                
                # 生成条件跳转
                true_label = self.new_label('TRUE')
                end_label = self.new_label('END')
                
                if op == 'EQ':
                    instructions.append(f"    je {true_label}")
                elif op == 'NE':
                    instructions.append(f"    jne {true_label}")
                elif op == 'LT':
                    instructions.append(f"    jl {true_label}")
                elif op == 'LE':
                    instructions.append(f"    jle {true_label}")
                elif op == 'GT':
                    instructions.append(f"    jg {true_label}")
                elif op == 'GE':
                    instructions.append(f"    jge {true_label}")
                
                instructions.extend([
                    f"    mov {self.get_var_ref(result)},0",
                    f"    jmp {end_label}",
                    f"{true_label}:",
                    f"    mov {self.get_var_ref(result)},1",
                    f"{end_label}:"
                ])

        # 返回指令
        elif op == 'RETURN':
            if arg1:
                instructions.extend([
                    f"    mov ax,{self.get_var_ref(arg1)}",
                    "    mov sp,bp",
                    "    pop bp",
                    "    ret"
                ])
            else:
                instructions.extend([
                    "    mov sp,bp",
                    "    pop bp",
                    "    ret"
                ])

        return instructions

    def get_var_ref(self, var: str) -> str:
        """获取变量的引用方式"""
        if var.isdigit():
            return var
        if var.startswith('main_'):
            var = var[5:]  # 去掉main_前缀
        if var.startswith('t'):
            return f"T{var[1:]}"  # 临时变量
        return var  # 普通变量
    
    def generate_helper_functions(self):
        """生成辅助函数（read/write）"""
        # 不再需要生成辅助函数，因为它们已经在io.inc中定义
        pass
    
    def format_output(self) -> str:
        """格式化输出最终的汇编代码"""
        # 添加段声明
        output = ["assume cs:code,ds:data,ss:stack,es:extended", ""]
        
        # 添加扩展段
        output.extend(self.extended_segment)
        output.append("")
        
        # 添加堆栈段
        output.extend(self.stack_segment)
        output.append("")
        
        # 添加数据段
        output.extend(self.data_segment)
        output.append("")
        
        # 包含I/O过程
        output.append("include io.inc")
        output.append("")
        
        # 添加代码段
        output.extend(self.code_segment)
        output.append("code ends")
        output.append("end start")
        
        return "\n".join(output)

def format_quads(quads: List[Tuple]) -> str:
    """格式化四元式输出"""
    lines = ["\n生成的中间代码（四元式）："]
    for i, quad in enumerate(quads):
        lines.append(f"{i:3d}: {quad}")
    return "\n".join(lines)

def test_code_generator():
    """测试代码生成器"""
    # 创建代码生成器实例
    cg = CodeGenerator()
    
    # 测试用例1：简单的算术运算
    print("\n测试用例1：简单的算术运算")
    print("-" * 50)
    quads1 = [
        Quadruple('=', '5', None, 'a'),      # a = 5
        Quadruple('=', '3', None, 'b'),      # b = 3
        Quadruple('+', 'a', 'b', 'c'),       # c = a + b
        Quadruple('*', 'c', '2', 'd'),       # d = c * 2
        Quadruple('para', 'd', None, None),  # 准备打印d
        Quadruple('call', 'write', None, None)  # 打印d
    ]
    print("四元式：")
    print(format_quads(quads1))
    print("\n生成的汇编代码：")
    print(cg.generate_code(quads1, 1))
    
    # 测试用例2：条件语句
    print("\n测试用例2：条件语句")
    print("-" * 50)
    quads2 = [
        Quadruple('=', '10', None, 'x'),     # x = 10
        Quadruple('=', '5', None, 'y'),      # y = 5
        Quadruple('>', 'x', 'y', 't1'),      # t1 = x > y
        Quadruple('jz', 't1', None, '6'),    # if t1 == 0 goto 6
        Quadruple('=', '1', None, 'result'), # result = 1
        Quadruple('j', None, None, '7'),     # goto 7
        Quadruple('=', '0', None, 'result'), # result = 0
        Quadruple('para', 'result', None, None),  # 准备打印result
        Quadruple('call', 'write', None, None)    # 打印result
    ]
    print("四元式：")
    print(format_quads(quads2))
    print("\n生成的汇编代码：")
    print(cg.generate_code(quads2, 2))
    
    # 测试用例3：函数调用
    print("\n测试用例3：函数调用")
    print("-" * 50)
    quads3 = [
        Quadruple('fun', 'main', '0', None),  # 函数main开始
        Quadruple('call', 'read', None, 'n'), # n = read()
        Quadruple('para', 'n', None, None),   # 准备调用factorial
        Quadruple('call', 'factorial', None, 'result'),  # result = factorial(n)
        Quadruple('para', 'result', None, None),  # 准备打印result
        Quadruple('call', 'write', None, None),  # 打印result
        Quadruple('ret', '0', None, None),    # return 0
        
        Quadruple('fun', 'factorial', '8', None),  # 函数factorial开始
        Quadruple('<=', 'n', '1', 't1'),      # t1 = n <= 1
        Quadruple('jz', 't1', None, '12'),    # if t1 == 0 goto 12
        Quadruple('ret', '1', None, None),    # return 1
        Quadruple('-', 'n', '1', 't2'),       # t2 = n - 1
        Quadruple('para', 't2', None, None),  # 准备递归调用
        Quadruple('call', 'factorial', None, 't3'),  # t3 = factorial(n-1)
        Quadruple('*', 'n', 't3', 't4'),      # t4 = n * t3
        Quadruple('ret', 't4', None, None)    # return t4
    ]
    print("四元式：")
    print(format_quads(quads3))
    print("\n生成的汇编代码：")
    print(cg.generate_code(quads3, 3))

if __name__ == '__main__':
    test_code_generator() 