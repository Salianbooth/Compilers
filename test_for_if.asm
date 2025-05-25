assume cs:code,ds:data,ss:stack,es:extended

extended segment
    db 1024 dup(0)
extended ends

stack segment
    db 1024 dup(0)
stack ends

data segment
; —— 以下是全局变量，全部初始化为 0 ——
sum     dw 0
N       dw 0
i       dw 0
T0      dw 0
T1      dw 0
T2      dw 0
T3      dw 0
T4      dw 0
T5      dw 0
data ends

include io.inc

start:
    mov ax,extended
    mov es,ax
    mov ax,stack
    mov ss,ax
    mov sp,1024
    mov bp,sp
    mov ax,data
    mov ds,ax
_T4_L0:
main: PUSH BP
MOV BP,SP
SUB SP,0
_T4_L1:
MOV AX,0
MOV sum,AX
_T4_L2:
CALL read
MOV T0,AX
_T4_L3:
MOV AX,T0
MOV N,AX
_T4_L4:
MOV AX,1
MOV i,AX
_T4_L5:
MOV DX,1
MOV AX,i
CMP AX,N
JLE _T4_LE_0
MOV DX,0
_T4_LE_0:
MOV T1,DX
_T4_L6:
MOV AX,T1
CMP AX,0
JE _T4_LABEL19
_T4_L7:
MOV AX,i
MOV DX,0
DIV 2
MOV T3,DX
_T4_L8:
MOV DX,1
MOV AX,T3
CMP AX,1
JE _T4_LE_1
MOV DX,0
_T4_LE_1:
MOV T4,DX
_T4_L9:
MOV AX,T4
CMP AX,0
JE _T4_LABEL12
_T4_L10:
MOV AX,sum
ADD AX,i
MOV T5,AX
_T4_L11:
MOV AX,T5
MOV sum,AX
_T4_L12:
MOV AX,i
ADD AX,1
MOV T2,AX
_T4_L13:
MOV AX,T2
MOV i,AX
_T4_L14:
JMP _T4_LABEL5
_T4_L15:
PUSH sum
_T4_L16:
CALL write
_T4_L17:
MOV AX,0
MOV SP,BP
POP BP
RET
quit:
    mov ah,4ch
    int 21h
code ends
end start