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
        if arg1 and not arg1.isdigit():
            if arg1.startswith('T'):
                self.used_temps.add(arg1)
            else:
                self.used_variables.add(arg1)
        if arg2 and not arg2.isdigit():
            if arg2.startswith('T'):
                self.used_temps.add(arg2)
            else:
                self.used_variables.add(arg2)
        if result:
            if result.startswith('T'):
                self.used_temps.add(result)
            else:
                self.used_variables.add(result)
        
        # 处理赋值操作
        if op == '=':
            if arg1.isdigit():  # 立即数
                instructions.extend([
                    f"MOV AX,{arg1}",
                    f"MOV {result},AX"
                ])
            else:  # 变量
                instructions.extend([
                    f"MOV AX,{arg1}",
                    f"MOV {result},AX"
                ])
        
        # 处理算术运算
        elif op in ['+', '-', '*', '/', '%']:
            if op == '+':
                instructions.extend([
                    f"MOV AX,{arg1}",
                    f"ADD AX,{arg2}",
                    f"MOV {result},AX"
                ])
            elif op == '-':
                instructions.extend([
                    f"MOV AX,{arg1}",
                    f"SUB AX,{arg2}",
                    f"MOV {result},AX"
                ])
            elif op == '*':
                if arg2.isdigit():  # 立即数乘法
                    instructions.extend([
                        f"MOV AX,{arg1}",
                        f"MUL {arg2}",
                        f"MOV {result},AX"
                    ])
                else:  # 变量乘法
                    instructions.extend([
                        f"MOV AX,{arg1}",
                        f"MUL {arg2}",
                        f"MOV {result},AX"
                    ])
            elif op == '/':
                instructions.extend([
                    f"MOV AX,{arg1}",
                    "MOV DX,0",
                    f"DIV {arg2}",
                    f"MOV {result},AX"
                ])
            elif op == '%':
                instructions.extend([
                    f"MOV AX,{arg1}",
                    "MOV DX,0",
                    f"DIV {arg2}",
                    f"MOV {result},DX"
                ])
        
        # 处理比较运算
        elif op in ['<', '<=', '>', '>=', '==', '!=']:
            label = self.new_label('LE')
            instructions.extend([
                "MOV DX,1",  # 默认结果为1
                f"MOV AX,{arg1}",
                f"CMP AX,{arg2}"
            ])
            
            # 根据比较结果设置标志位
            if op == '<':
                instructions.append(f"JL {label}")
            elif op == '<=':
                instructions.append(f"JLE {label}")
            elif op == '>':
                instructions.append(f"JG {label}")
            elif op == '>=':
                instructions.append(f"JGE {label}")
            elif op == '==':
                instructions.append(f"JE {label}")
            elif op == '!=':
                instructions.append(f"JNE {label}")
            
            instructions.extend([
                "MOV DX,0",  # 不满足条件时结果为0
                f"{label}:",
                f"MOV {result},DX"
            ])
        
        # 处理跳转指令
        elif op in ['j', 'jnz', 'jz']:
            if op == 'j':
                instructions.append(f"JMP _T{self.current_test}_LABEL{result}")
            elif op == 'jnz':
                instructions.extend([
                    f"MOV AX,{arg1}",
                    "CMP AX,0",
                    f"JNE _T{self.current_test}_LABEL{result}"
                ])
            elif op == 'jz':
                instructions.extend([
                    f"MOV AX,{arg1}",
                    "CMP AX,0",
                    f"JE _T{self.current_test}_LABEL{result}"
                ])
        
        # 处理函数调用
        elif op == 'call':
            if arg1 == 'read':
                instructions.append("CALL read")
            elif arg1 == 'write':
                instructions.append("CALL write")
            else:
                instructions.append(f"CALL {arg1}")
            if result:
                instructions.append(f"MOV {result},AX")
        
        # 处理参数传递
        elif op == 'para':
            instructions.append(f"PUSH {arg1}")
            if self.current_function:
                self.function_param_count[self.current_function] = self.function_param_count.get(self.current_function, 0) + 1
        
        # 处理函数定义
        elif op == 'fun':
            self.current_function = arg1
            self.function_local_size[arg1] = int(arg2) if arg2 else 0
            self.function_temp_count[arg1] = 0
            self.function_param_count[arg1] = 0
            instructions.extend([
                f"{arg1}: PUSH BP",
                "MOV BP,SP",
                f"SUB SP,{self.function_local_size[arg1]}"  # 为局部变量分配空间
            ])
        
        # 处理函数返回
        elif op == 'ret':
            if arg1:
                instructions.extend([
                    f"MOV AX,{arg1}",
                    "MOV SP,BP",
                    "POP BP",
                    "RET"
                ])
            else:
                instructions.extend([
                    "MOV SP,BP",
                    "POP BP",
                    "RET"
                ])
        
        return instructions
    
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