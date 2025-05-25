; Program: Sum of odd numbers
; Description: Calculate sum of odd numbers from 1 to N

ASSUME CS:CODE,DS:DATA,SS:STACK,ES:EXTENDED

EXTENDED SEGMENT
    DB 1024 DUP(0)
EXTENDED ENDS

STACK SEGMENT
    DB 1024 DUP(0)
STACK ENDS

DATA SEGMENT
    _buff_p DB 256 DUP (24h)
    _buff_s DB 256 DUP (0)
    _msg_p DB 0ah,'Output:',0
    _msg_s DB 0ah,'Input:',0
    next_row DB 0dh,0ah,'$'
    error DB 'input error, please re-enter: ','$'
    sum     DW 0
    N       DW 0
    i       DW 0
    T0      DW 0
    T1      DW 0
    T2      DW 0
    T3      DW 0
    T4      DW 0
    T5      DW 0
    T6      DW 0
    temp_sum DW 0   ; 新增临时变量用于保存sum值
DATA ENDS

CODE SEGMENT
START:
    ; Initialize segments
    MOV AX,DATA
    MOV DS,AX
    MOV AX,STACK
    MOV SS,AX
    MOV AX,EXTENDED
    MOV ES,AX
    MOV SP,1024
    MOV BP,SP

    ; Program start
    MOV sum, 0    ; Initialize sum
    
    ; Read input N
    CALL read
    MOV N, AX     ; N = read()
    
    ; Initialize loop counter
    MOV i, 1      ; i = 1
    
FOR_LOOP:
    ; Check loop condition i <= N
    MOV AX, i
    CMP AX, N
    JG QUIT       ; if i>N then exit loop
    
    ; Calculate i%2
    MOV AX, i
    MOV BL, 2
    DIV BL        ; result in AL, remainder in AH
    
    ; Check if i is odd
    CMP AH, 1
    JNE NEXT      ; if not odd, skip addition
    
    ; Add odd number
    MOV AX, sum
    ADD AX, i
    MOV sum, AX
    
NEXT:
    ; Update loop counter
    INC i         ; i++
    JMP FOR_LOOP
    
QUIT:
    ; Output result
    MOV AX, sum
    MOV temp_sum, AX  ; 保存sum到临时变量
    CALL write    ; call write function
    
    ; Exit program
    MOV AH, 4ch
    INT 21h

; ===== 输入函数 =====
read PROC NEAR
    PUSH BP
    MOV BP,SP
    MOV BX,OFFSET _msg_s
    CALL _print
    PUSH BX
    PUSH CX
    PUSH DX
    
    proc_pre_start:
    XOR AX,AX
    XOR BX,BX
    XOR CX,CX
    XOR DX,DX
    
    proc_judge_sign:
    MOV AH,1
    INT 21h
    CMP AL,'-'
    JNE proc_next
    MOV DX,0ffffh
    JMP proc_digit_in
    
    proc_next:
    CMP AL,30h
    JB proc_unexpected
    CMP AL,39h
    JA proc_unexpected
    SUB AL,30h
    SHL BX,1
    MOV CX,BX
    SHL BX,1
    SHL BX,1
    ADD BX,CX
    ADD BL,AL
    ADC BH,0
    
    proc_digit_in:
    MOV AH,1
    INT 21h
    CMP AL,0dh
    JE proc_save
    JMP proc_next
    
    proc_save:
    CMP DX,0ffffh
    JNE proc_result_save
    NEG BX
    
    proc_result_save:
    MOV AX,BX
    JMP proc_input_done
    
    proc_unexpected:
    CMP AL,0dh
    JE proc_save
    MOV DX,OFFSET next_row
    MOV AH,9
    INT 21h
    MOV DX,OFFSET error
    MOV AH,9
    INT 21h
    JMP proc_pre_start
    
    proc_input_done:
    POP DX
    POP CX
    POP BX
    POP BP
    RET
read ENDP

; ===== 输出函数 =====
write PROC NEAR
    ; 使用临时变量temp_sum而不是AX
    MOV BX,OFFSET _msg_p
    CALL _print
    
    MOV AX,temp_sum  ; 从临时变量加载值
    MOV BX,AX        ; 保存到BX
    
    ; 检查负数
    TEST BX,8000h
    JZ skip_neg
    NEG BX           ; 如果是负数，取绝对值
    PUSH BX          ; 保存BX
    MOV DL,'-'
    MOV AH,2
    INT 21h          ; 输出负号
    POP BX           ; 恢复BX
    
skip_neg:
    ; 将数字转换为ASCII并显示
    MOV AX,BX
    XOR CX,CX        ; 清零计数器
    MOV BX,10        ; 除数
    
conv_loop:
    XOR DX,DX
    DIV BX           ; AX / 10, 商在AX, 余数在DX
    PUSH DX          ; 保存余数（最低位数字）
    INC CX           ; 增加计数器
    TEST AX,AX       ; 检查是否还有更多位
    JNZ conv_loop    ; 如果不是零，继续循环
    
print_digits:
    POP DX           ; 取出一个数字
    ADD DL,'0'       ; 转换为ASCII
    MOV AH,2
    INT 21h          ; 显示数字
    LOOP print_digits ; 继续直到所有数字都显示完
    
    ; 输出换行
    MOV DL,13        ; CR
    MOV AH,2
    INT 21h
    MOV DL,10        ; LF
    MOV AH,2
    INT 21h
    
    RET
write ENDP

; ===== 辅助打印函数 =====
_print PROC NEAR
    MOV SI,0
    MOV DI,OFFSET _buff_p
    
    _p_lp_1:
    MOV AL,DS:[BX+SI]
    CMP AL,0
    JE _p_brk_1
    MOV DS:[DI],AL
    INC SI
    INC DI
    JMP SHORT _p_lp_1
    
    _p_brk_1:
    MOV DX,OFFSET _buff_p
    MOV AH,09h
    INT 21h
    MOV CX,SI
    MOV DI,OFFSET _buff_p
    
    _p_lp_2:
    MOV AL,24h
    MOV DS:[DI],AL
    INC DI
    LOOP _p_lp_2
    RET
_print ENDP

CODE ENDS
END START