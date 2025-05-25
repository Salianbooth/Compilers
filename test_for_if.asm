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
_i dw 0

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
assume cs:code,ds:data,ss:stack,es:extended
include io.inc
code segment
start:
    mov ax,data
    mov ds,ax
    mov ax,stack
    mov ss,ax
    mov sp,1024
    mov bp,sp
_T4_L1:
_T4_L2:
_T4_L3:
    mov ax,10
    mov T0,ax
_T4_L4:
    mov ax,T0
    mov N,ax
_T4_L5:
    mov ax,1
    mov T1,ax
_T4_L6:
    mov ax,T1
    mov i,ax
_T4_L7:
main_L0:
_T4_L8:
_T4_L9:
    mov ax,i
    mov T2,ax
_T4_L10:
    mov ax,2
    mov T3,ax
_T4_L11:
    xor dx,dx
    mov ax,T2
    mov bx,T3
    idiv bx
    mov T4,dx
_T4_L12:
    mov ax,1
    mov T5,ax
_T4_L13:
    mov ax,T4
    cmp ax,T5
    je _T4_TRUE_0
    mov T6,0
    jmp _T4_END_1
_T4_TRUE_0:
    mov T6,1
_T4_END_1:
_T4_L14:
    mov ax,T6
    cmp ax,0
    je main_L2
_T4_L15:
    mov ax,sum
    mov T7,ax
_T4_L16:
    mov ax,i
    mov T8,ax
_T4_L17:
    mov ax,T7
    add ax,T8
    mov T9,ax
_T4_L18:
    mov ax,T9
    mov sum,ax
_T4_L19:
main_L2:
_T4_L20:
    mov ax,i
    mov T10,ax
_T4_L21:
    mov ax,N
    mov T11,ax
_T4_L22:
    mov ax,T10
    cmp ax,T11
    jle _T4_TRUE_2
    mov T12,0
    jmp _T4_END_3
_T4_TRUE_2:
    mov T12,1
_T4_END_3:
_T4_L23:
    jmp main_L0
_T4_L24:
main_L1:
_T4_L25:
    mov ax,0
    mov T13,ax
_T4_L26:
    mov ax,T13
    mov sp,bp
    pop bp
    ret
_T4_L27:
    mov ah,4ch
    int 21h
code ends
end start
quit:
    mov ah,4ch
    int 21h
code ends
end start