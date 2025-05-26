; Program: Sum of odd numbers
; Description: Calculate sum of odd numbers from 1 to N

ASSUME CS:CODE, DS:DATA, SS:STACK, ES:EXTENDED

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
    ; Global variables
    sum     DW 0
    N       DW 0
    i       DW 0
    temp_sum DW 0   ; Temporary variable to store sum value
    T0      DW 0
    T1      DW 0
    T2      DW 0
    T3      DW 0
    T4      DW 0
    T5      DW 0
    T6      DW 0

DATA ENDS

CODE SEGMENT
START:
    ; Initialize segments
    MOV AX, DATA
    MOV DS, AX
    MOV AX, STACK
    MOV SS, AX
    MOV AX, EXTENDED
    MOV ES, AX
    MOV SP, 1024
    MOV BP, SP

    ; Program start
    MOV sum, 0    ; Initialize sum to 0
    
    ; Read input N
    CALL read
    MOV N, AX     ; N = read()
    
    ; Initialize loop counter i
    MOV i, 1      ; i = 1
    
FOR_LOOP:
    ; Check loop condition i <= N
    MOV AX, i
    CMP AX, N
    JG QUIT       ; If i>N then exit loop
    
    ; Calculate i%2
    MOV AX, i
    MOV BL, 2
    DIV BL        ; Result in AL, remainder in AH
    
    ; Check if i is odd
    CMP AH, 1
    JNE NEXT      ; If not odd, skip addition
    
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
    MOV temp_sum, AX  ; Save sum to temp_sum for write function
    CALL write    ; Call write function to display result
    
    ; End program
    MOV AH, 4CH
    INT 21H

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
_print ENDP

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
read ENDP

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
write ENDP

CODE ENDS
END START