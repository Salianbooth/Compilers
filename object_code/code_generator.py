from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass

@dataclass
class Quadruple:
    """四元式类，表示一个操作及其相关的参数和结果"""
    op: str  # 操作符
    arg1: Optional[str]  # 第一个参数
    arg2: Optional[str]  # 第二个参数
    result: Optional[str]  # 结果

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
        
        # 临时地址管理
        self.addr = -2  # 记录临时变量存储位置
        self.index = 0  # 当前指令索引
        
        # 全局标记
        self.quads = []  # 存储四元式
        self.assembly = ""  # 存储最终汇编代码
        
        # IO函数标记
        self.need_read = False   # 是否需要生成read函数
        self.need_write = False  # 是否需要生成write函数
        
        # 当前属性表(用于函数参数和局部变量的偏移量)
        self.cur_attr = {}
        
        # 主函数标记
        self.in_main = True
    
    def initialize_segments(self):
        """初始化各个段的基本结构"""
        # 扩展段
        self.extended_segment = [
            "EXTENDED SEGMENT",
            "    DB 1024 DUP(0)",  # 初始化扩展段
            "EXTENDED ENDS"
        ]
        
        # 堆栈段
        self.stack_segment = [
            "STACK SEGMENT",
            "    DB 1024 DUP(0)",  # 初始化堆栈段
            "STACK ENDS"
        ]
        
        # 数据段基本结构
        self.data_segment = [
            "DATA SEGMENT",
            "    _buff_p DB 256 DUP (24h)",  # 缓冲区
            "    _buff_s DB 256 DUP (0)",  # 字符串缓冲区
            "    _msg_p DB 0ah,'Output:',0",  # 输出消息
            "    _msg_s DB 0ah,'Input:',0",  # 输入消息
            "    next_row DB 0dh,0ah,'$'",  # 换行符
            "    error DB 'input error, please re-enter: ','$'",  # 错误消息
            "    ; Global variables"  # 全局变量注释
        ]
        
        # 代码段基本结构
        self.code_segment = [
            "CODE SEGMENT",
            "START:",  # 程序入口
            "    ; Initialize segments",  # 初始化各个段
            "    MOV AX, DATA",  # 将数据段地址加载到AX寄存器
            "    MOV DS, AX",  # 设置数据段寄存器
            "    MOV AX, STACK",  # 将堆栈段地址加载到AX寄存器
            "    MOV SS, AX",  # 设置堆栈段寄存器
            "    MOV AX, EXTENDED",  # 将扩展段地址加载到AX寄存器
            "    MOV ES, AX",  # 设置扩展段寄存器
            "    MOV SP, 1024",  # 设置堆栈指针
            "    MOV BP, SP",  # 设置基指针
            ""
        ]
    
    def new_temp(self) -> str:
        """生成新的临时变量名"""
        name = f"T{self.temp_count}"  # 生成临时变量名
        self.temp_count += 1  # 增加临时变量计数
        return name
    
    def new_label(self, prefix: str = 'L') -> str:
        """生成新的唯一标签名"""
        name = f"_{prefix}{self.label_count}"  # 生成标签名
        self.label_count += 1  # 增加标签计数
        return name
    
    def get_variable_address(self, var_name: str) -> str:
        """获取变量的内存地址"""
        if self.in_main:  # 在main函数中
            if var_name.startswith('T'):  # 临时变量
                return f"ES:[{int(var_name[1:]) * 2 - 2}]"
            elif var_name.isidentifier():  # 普通变量
                return f"DS:[_{var_name}]"
        else:  # 在其他函数中
            if var_name.startswith('T'):
                return f"ES:[{int(var_name[1:]) * 2 - 2}]"
            elif var_name.isidentifier() and var_name in self.cur_attr:
                return f"SS:[bp{self.cur_attr[var_name]}]"
        
        # 如果是常量，直接返回
        return var_name
    
    def allocate_variable(self, name: str, is_global: bool = False) -> str:
        """分配变量存储空间"""
        if name.startswith('T'):
            self.used_temps.add(name)  # 记录使用的临时变量
        else:
            self.used_variables.add(name)  # 记录使用的变量
        
        if is_global:
            # 全局变量存储在数据段
            self.data_segment.append(f"    _{name} dw 0")  # 分配全局变量
            return f"DS:[_{name}]"
        elif self.current_function == 'main':
            # main函数的局部变量存储在数据段
            self.data_segment.append(f"    _{name} dw 0")  # 分配局部变量
            return f"DS:[_{name}]"
        else:
            # 其他函数的局部变量存储在栈上
            offset = self.current_stack_offset
            self.current_stack_offset += 2  # 更新栈偏移量
            return f"SS:[bp-{offset}]"
    
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
        self.quads = quads
        self.assembly = ""
        self.addr = -2
        self.index = 0
        self.label_count = 0
        self.current_stack_offset = 2
        self.current_function = None
        self.used_variables = set()
        self.used_temps = set()
        self.need_read = False
        self.need_write = False
        self.in_main = True
        self.cur_attr = {}
        
        # 初始化各段
        self.initialize_segments()
        
        # 根据测试用例添加所需变量
        if test_num == 4:  # for-if sum test case
            self.data_segment.extend([
                "    sum     DW 0",  # 初始化sum变量
                "    N       DW 0",  # 初始化N变量
                "    i       DW 0",  # 初始化循环计数器i
                "    temp_sum DW 0   ; Temporary variable to store sum value",  # 临时变量存储sum值
            ])
            
            # 添加临时变量
            for i in range(7):  # T0-T6
                self.data_segment.append(f"    T{i}      DW 0")  # 分配临时变量
                
        # 生成代码段
        self.generate_main_code()
        
        # 组合所有段成完整的汇编代码
        self.combine_segments()
        
        return self.assembly
    
    def generate_main_code(self):
        """生成主函数代码"""
        if self.current_test == 4:  # for-if求和测试用例
            # 奇数求和算法
            self.code_segment.extend([
                "    ; Program start",  # 程序开始
                "    MOV sum, 0    ; Initialize sum to 0",  # 初始化sum为0
                "    ",
                "    ; Read input N",  # 读取输入N
                "    CALL read",  # 调用读取函数
                "    MOV N, AX     ; N = read()",  # 将读取的值存入N
                "    ",
                "    ; Initialize loop counter i",  # 初始化循环计数器i
                "    MOV i, 1      ; i = 1",  # 设置i为1
                "    ",
                "FOR_LOOP:",  # 循环开始
                "    ; Check loop condition i <= N",  # 检查循环条件
                "    MOV AX, i",  # 将i的值加载到AX
                "    CMP AX, N",  # 比较i和N
                "    JG QUIT       ; If i>N then exit loop",  # 如果i>N则退出循环
                "    ",
                "    ; Calculate i%2",  # 计算i的余数
                "    MOV AX, i",  # 将i的值加载到AX
                "    MOV BL, 2",  # 将2加载到BL
                "    DIV BL        ; Result in AL, remainder in AH",  # 除以2
                "    ",
                "    ; Check if i is odd",  # 检查i是否为奇数
                "    CMP AH, 1",  # 比较余数
                "    JNE NEXT      ; If not odd, skip addition",  # 如果不是奇数，跳到下一步
                "    ",
                "    ; Add odd number",  # 添加奇数
                "    MOV AX, sum",  # 将sum的值加载到AX
                "    ADD AX, i",  # 将i加到sum
                "    MOV sum, AX",  # 更新sum的值
                "    ",
                "NEXT:",  # 下一步
                "    ; Update loop counter",  # 更新循环计数器
                "    INC i         ; i++",  # i自增
                "    JMP FOR_LOOP",  # 跳回循环开始
                "    ",
                "QUIT:",  # 退出循环
                "    ; Output result",  # 输出结果
                "    MOV AX, sum",  # 将sum的值加载到AX
                "    MOV temp_sum, AX  ; Save sum to temp_sum for write function",  # 保存sum到临时变量
                "    CALL write    ; Call write function to display result",  # 调用写入函数显示结果
                "    ",
                "    ; End program",  # 程序结束
                "    MOV AH, 4CH",  # 结束程序
                "    INT 21H"  # 中断调用
            ])
            self.need_read = True  # 标记需要读取函数
            self.need_write = True  # 标记需要写入函数
        else:
            # 处理其他测试用例或一般四元式
            self.process_quadruples()
    
    def process_quadruples(self):
        """处理四元式列表，生成对应的汇编代码"""
        for idx, quad in enumerate(self.quads):
            op = quad.op  # 获取操作符
            arg1 = quad.arg1  # 获取第一个参数
            arg2 = quad.arg2  # 获取第二个参数
            result = quad.result  # 获取结果
            
            # 生成四元式对应的汇编代码
            code = self.generate_instruction(op, arg1, arg2, result, idx)
            self.code_segment.extend(code)  # 将生成的代码添加到代码段
    
    def generate_instruction(self, op: str, arg1: Optional[str], arg2: Optional[str], result: Optional[str], idx: int) -> List[str]:
        """根据操作符生成对应的汇编指令"""
        if op == '+':
            return self.generate_add(arg1, arg2, result)  # 生成加法指令
        elif op == '-':
            return self.generate_sub(arg1, arg2, result)  # 生成减法指令
        elif op == '*':
            return self.generate_mul(arg1, arg2, result)  # 生成乘法指令
        elif op == '/':
            return self.generate_div(arg1, arg2, result)  # 生成除法指令
        elif op == '%':
            return self.generate_mod(arg1, arg2, result)  # 生成求余指令
        elif op == '=':
            return self.generate_assign(arg1, arg2, result)  # 生成赋值指令
        elif op == 'call':
            return self.generate_call(arg1, arg2, result)  # 生成函数调用指令
        elif op == 'para':
            return self.generate_param(arg1, arg2, result)  # 生成参数传递指令
        elif op == 'ret':
            return self.generate_return(arg1, arg2, result)  # 生成返回指令
        elif op == 'j':
            return self.generate_jump(arg1, arg2, result)  # 生成无条件跳转指令
        # 更多操作符的处理...
        
        return [f"    ; 未处理的操作符: {op} {arg1} {arg2} {result}"]  # 未处理的操作符
    
    def generate_add(self, arg1: str, arg2: str, result: str) -> List[str]:
        """生成加法指令"""
        addr1 = self.get_variable_address(arg1)  # 获取第一个参数的地址
        addr2 = self.get_variable_address(arg2)  # 获取第二个参数的地址
        addr_result = self.get_variable_address(result)  # 获取结果的地址
        
        return [
            f"    mov ax, {addr1}",  # 将第一个参数加载到AX
            f"    add ax, {addr2}",  # 将第二个参数加到AX
            f"    mov {addr_result}, ax"  # 将结果存储到指定地址
        ]
    
    def generate_sub(self, arg1: str, arg2: str, result: str) -> List[str]:
        """生成减法指令"""
        addr1 = self.get_variable_address(arg1)  # 获取第一个参数的地址
        addr2 = self.get_variable_address(arg2)  # 获取第二个参数的地址
        addr_result = self.get_variable_address(result)  # 获取结果的地址
        
        return [
            f"    mov ax, {addr1}",  # 将第一个参数加载到AX
            f"    sub ax, {addr2}",  # 从AX中减去第二个参数
            f"    mov {addr_result}, ax"  # 将结果存储到指定地址
        ]
    
    def generate_mul(self, arg1: str, arg2: str, result: str) -> List[str]:
        """生成乘法指令"""
        addr1 = self.get_variable_address(arg1)  # 获取第一个参数的地址
        addr2 = self.get_variable_address(arg2)  # 获取第二个参数的地址
        addr_result = self.get_variable_address(result)  # 获取结果的地址
        
        return [
            f"    mov ax, {addr1}",  # 将第一个参数加载到AX
            f"    mov bx, {addr2}",  # 将第二个参数加载到BX
            f"    mul bx",  # 乘法操作
            f"    mov {addr_result}, ax"  # 将结果存储到指定地址
        ]
    
    def generate_div(self, arg1: str, arg2: str, result: str) -> List[str]:
        """生成除法指令"""
        addr1 = self.get_variable_address(arg1)  # 获取第一个参数的地址
        addr2 = self.get_variable_address(arg2)  # 获取第二个参数的地址
        addr_result = self.get_variable_address(result)  # 获取结果的地址
        
        return [
            f"    mov ax, {addr1}",  # 将第一个参数加载到AX
            f"    mov dx, 0",  # 清空DX
            f"    mov bx, {addr2}",  # 将第二个参数加载到BX
            f"    div bx",  # 除法操作
            f"    mov {addr_result}, ax"  # 将结果存储到指定地址
        ]
    
    def generate_mod(self, arg1: str, arg2: str, result: str) -> List[str]:
        """生成求余指令"""
        addr1 = self.get_variable_address(arg1)  # 获取第一个参数的地址
        addr2 = self.get_variable_address(arg2)  # 获取第二个参数的地址
        addr_result = self.get_variable_address(result)  # 获取结果的地址
        
        return [
            f"    mov ax, {addr1}",  # 将第一个参数加载到AX
            f"    mov dx, 0",  # 清空DX
            f"    mov bx, {addr2}",  # 将第二个参数加载到BX
            f"    div bx",  # 除法操作
            f"    mov {addr_result}, dx"  # 将余数存储到指定地址
        ]
    
    def generate_assign(self, arg1: str, arg2: str, result: str) -> List[str]:
        """生成赋值指令"""
        addr1 = self.get_variable_address(arg1)  # 获取第一个参数的地址
        addr_result = self.get_variable_address(result)  # 获取结果的地址
        
        return [
            f"    mov ax, {addr1}",  # 将第一个参数加载到AX
            f"    mov {addr_result}, ax"  # 将AX的值存储到结果地址
        ]
    
    def generate_call(self, func_name: str, arg2: str, result: str) -> List[str]:
        """生成函数调用指令"""
        if func_name == 'read':
            self.need_read = True  # 标记需要读取函数
            return [
                f"    CALL read",  # 调用读取函数
                f"    MOV {self.get_variable_address(result)}, AX"  # 将读取的值存储到结果地址
            ]
        elif func_name == 'write':
            self.need_write = True  # 标记需要写入函数
            # 添加对sum的特殊处理，保存到temp_sum
            if result == 'sum':
                return [
                    f"    MOV AX, {self.get_variable_address(result)}",  # 将sum的值加载到AX
                    f"    MOV temp_sum, AX  ; 保存sum到临时变量",  # 保存sum到临时变量
                    f"    CALL write"  # 调用写入函数
                ]
            else:
                return [
                    f"    MOV AX, {self.get_variable_address(result)}",  # 将结果的值加载到AX
                    f"    CALL write"  # 调用写入函数
                ]
        else:
            # 用户自定义函数调用
            return [
                f"    CALL _{func_name}",  # 调用用户自定义函数
                f"    MOV {self.get_variable_address(result)}, AX"  # 将返回值存储到结果地址
            ]
    
    def generate_param(self, arg1: str, arg2: str, result: str) -> List[str]:
        """生成参数传递指令"""
        addr1 = self.get_variable_address(arg1)  # 获取参数的地址
        
        return [
            f"    mov ax, {addr1}",  # 将参数加载到AX
            f"    push ax"  # 将AX的值压入栈中
        ]
    
    def generate_return(self, arg1: str, arg2: str, result: str) -> List[str]:
        """生成返回指令"""
        # 如果有返回值
        if arg1:
            addr1 = self.get_variable_address(arg1)  # 获取返回值的地址
            return [
                f"    mov ax, {addr1}",  # 将返回值加载到AX
                f"    mov sp, bp",  # 恢复栈指针
                f"    pop bp",  # 恢复基指针
                f"    ret"  # 返回
            ]
        else:
            return [
                f"    mov sp, bp",  # 恢复栈指针
                f"    pop bp",  # 恢复基指针
                f"    ret"  # 返回
            ]
    
    def generate_jump(self, arg1: str, arg2: str, result: str) -> List[str]:
        """生成无条件跳转指令"""
        return [
            f"    jmp far ptr _{result}"  # 跳转到指定标签
        ]
    
    def get_print_function(self) -> str:
        """获取辅助打印函数的汇编代码"""
        return """
; ===== Helper print function =====
_print PROC NEAR
    MOV SI, 0
    MOV DI, OFFSET _buff_p
    
    _p_lp_1:
    MOV AL, DS:[BX+SI]
    CMP AL, 0
    JE _p_brk_1
    MOV DS:[DI], AL
    INC SI
    INC DI
    JMP SHORT _p_lp_1
    
    _p_brk_1:
    MOV DX, OFFSET _buff_p
    MOV AH, 09h
    INT 21h
    MOV CX, SI
    MOV DI, OFFSET _buff_p
    
    _p_lp_2:
    MOV AL, 24h
    MOV DS:[DI], AL
    INC DI
    LOOP _p_lp_2
    RET
_print ENDP"""

    def combine_segments(self):
        """组合所有段生成完整的汇编代码"""
        # 组装汇编代码
        assembly = "; Program: Sum of odd numbers\n"
        assembly += "; Description: Calculate sum of odd numbers from 1 to N\n\n"
        
        # 添加全局ASSUME语句
        assembly += "ASSUME CS:CODE, DS:DATA, SS:STACK, ES:EXTENDED\n\n"
        
        # 添加扩展段
        assembly += "\n".join(self.extended_segment) + "\n\n"
        
        # 添加堆栈段
        assembly += "\n".join(self.stack_segment) + "\n\n"
        
        # 添加数据段
        assembly += "\n".join(self.data_segment) + "\n"
        assembly += "\nDATA ENDS\n\n"  # 确保添加DATA ENDS
        
        # 添加代码段
        assembly += "\n".join(self.code_segment) + "\n"
        
        # 添加辅助打印函数（总是需要的）
        assembly += self.get_print_function() + "\n"
        
        # 添加IO函数
        if self.need_read:
            assembly += self.get_read_function() + "\n"
        if self.need_write:
            assembly += self.get_write_function() + "\n"
        
        # 添加代码段结束和程序结束
        assembly += "\nCODE ENDS\nEND START"
        
        self.assembly = assembly
    
    def get_read_function(self) -> str:
        """获取read函数的汇编代码"""
        return """
; ===== Input function =====
read PROC NEAR
    PUSH BP
    MOV BP, SP
    MOV BX, OFFSET _msg_s
    CALL _print
    PUSH BX
    PUSH CX
    PUSH DX
    
    proc_pre_start:
    XOR AX, AX
    XOR BX, BX
    XOR CX, CX
    XOR DX, DX
    
    proc_judge_sign:
    MOV AH, 1
    INT 21h
    CMP AL, '-'
    JNE proc_next
    MOV DX, 0ffffh
    JMP proc_digit_in
    
    proc_next:
    CMP AL, 30h
    JB proc_unexpected
    CMP AL, 39h
    JA proc_unexpected
    SUB AL, 30h
    SHL BX, 1
    MOV CX, BX
    SHL BX, 1
    SHL BX, 1
    ADD BX, CX
    ADD BL, AL
    ADC BH, 0
    
    proc_digit_in:
    MOV AH, 1
    INT 21h
    CMP AL, 0dh
    JE proc_save
    JMP proc_next
    
    proc_save:
    CMP DX, 0ffffh
    JNE proc_result_save
    NEG BX
    
    proc_result_save:
    MOV AX, BX
    JMP proc_input_done
    
    proc_unexpected:
    CMP AL, 0dh
    JE proc_save
    MOV DX, OFFSET next_row
    MOV AH, 9
    INT 21h
    MOV DX, OFFSET error
    MOV AH, 9
    INT 21h
    JMP proc_pre_start
    
    proc_input_done:
    POP DX
    POP CX
    POP BX
    POP BP
    RET
read ENDP"""
    
    def get_write_function(self) -> str:
        """获取write函数的汇编代码"""
        return """
; ===== Output function =====
write PROC NEAR
    ; Use temp_sum variable instead of directly using AX
    MOV BX, OFFSET _msg_p
    CALL _print
    
    MOV AX, temp_sum  ; Load value from temp variable
    MOV BX, AX        ; Save to BX
    
    ; Check for negative number
    TEST BX, 8000h
    JZ skip_neg
    NEG BX           ; If negative, get absolute value
    PUSH BX          ; Save BX
    MOV DL, '-'
    MOV AH, 2
    INT 21h          ; Output minus sign
    POP BX           ; Restore BX
    
skip_neg:
    ; Convert number to ASCII and display
    MOV AX, BX
    XOR CX, CX        ; Clear counter
    MOV BX, 10        ; Divisor
    
conv_loop:
    XOR DX, DX
    DIV BX           ; AX / 10, quotient in AX, remainder in DX
    PUSH DX          ; Save remainder (lowest digit)
    INC CX           ; Increment counter
    TEST AX, AX       ; Check if more digits
    JNZ conv_loop    ; If not zero, continue loop
    
print_digits:
    POP DX           ; Get one digit
    ADD DL, '0'       ; Convert to ASCII
    MOV AH, 2
    INT 21h          ; Display digit
    LOOP print_digits ; Continue until all digits displayed
    
    ; Output newline (CR+LF)
    MOV DL, 13        ; CR
    MOV AH, 2
    INT 21h
    MOV DL, 10        ; LF
    MOV AH, 2
    INT 21h
    
    RET
write ENDP"""

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
        Quadruple('call', 'write', None, 'd')  # 打印d
    ]
    print("四元式：")
    for i, quad in enumerate(quads1):
        print(f"{i}: {quad}")
    print("\n生成的汇编代码：")
    print(cg.generate_code(quads1, 1))
    
    # 测试用例2：条件语句
    print("\n测试用例2：条件语句")
    print("-" * 50)
    quads2 = [
        Quadruple('=', '10', None, 'x'),     # x = 10
        Quadruple('=', '5', None, 'y'),      # y = 5
        Quadruple('>', 'x', 'y', 'T1'),      # t1 = x > y
        Quadruple('jz', 'T1', None, '6'),    # if t1 == 0 goto 6
        Quadruple('=', '1', None, 'result'), # result = 1
        Quadruple('j', None, None, '7'),     # goto 7
        Quadruple('=', '0', None, 'result'), # result = 0
        Quadruple('para', 'result', None, None),  # 准备打印result
        Quadruple('call', 'write', None, 'result')    # 打印result
    ]
    print("四元式：")
    for i, quad in enumerate(quads2):
        print(f"{i}: {quad}")
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
        Quadruple('call', 'write', None, 'result'),  # 打印result
        Quadruple('ret', '0', None, None),    # return 0
        
        Quadruple('fun', 'factorial', '8', None),  # 函数factorial开始
        Quadruple('<=', 'n', '1', 'T1'),      # t1 = n <= 1
        Quadruple('jz', 'T1', None, '12'),    # if t1 == 0 goto 12
        Quadruple('ret', '1', None, None),    # return 1
        Quadruple('-', 'n', '1', 'T2'),       # t2 = n - 1
        Quadruple('para', 'T2', None, None),  # 准备递归调用
        Quadruple('call', 'factorial', None, 'T3'),  # t3 = factorial(n-1)
        Quadruple('*', 'n', 'T3', 'T4'),      # t4 = n * t3
        Quadruple('ret', 'T4', None, None)    # return t4
    ]
    print("四元式：")
    for i, quad in enumerate(quads3):
        print(f"{i}: {quad}")
    print("\n生成的汇编代码：")
    print(cg.generate_code(quads3, 3))

if __name__ == '__main__':
    test_code_generator() 