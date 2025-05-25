from code_generator import CodeGenerator, Quadruple

def test_for_if_sum():
    """
    测试用例：for嵌套if,求1到给定数N以内所有奇数的和
    源代码:
    main()
    {
        int i,N,sum = 0;
        N = read();
        for(i=1;i<=N;i=i+1)
        {
            if(i%2 == 1)
                sum = sum+i;
        }
        write(sum);
    }
    """
    # 四元式列表
    quads = [
        Quadruple('fun', 'main', '0', None),     # 0: ['main', '_', '_', '_']
        Quadruple('=', '0', None, 'sum'),        # 1: ['=', '0', '_', 'sum']
        Quadruple('call', 'read', None, 'T0'),   # 2: ['call', 'read', '_', 'T0']
        Quadruple('=', 'T0', None, 'N'),         # 3: ['=', 'T0', '_', 'N']
        Quadruple('=', '1', None, 'i'),          # 4: ['=', '1', '_', 'i']
        Quadruple('<=', 'i', 'N', 'T1'),         # 5: ['<=', 'i', 'N', 'T1']
        Quadruple('jz', 'T1', None, '19'),       # 6: ['jz', 'T1', '_', 19]
        Quadruple('%', 'i', '2', 'T3'),          # 7: ['%', 'i', '2', 'T3']
        Quadruple('==', 'T3', '1', 'T4'),        # 8: ['==', 'T3', '1', 'T4']
        Quadruple('jz', 'T4', None, '12'),       # 9: ['jz', 'T4', '_', 12]
        Quadruple('+', 'sum', 'i', 'T5'),        # 10: ['+', 'sum', 'i', 'T5']
        Quadruple('=', 'T5', None, 'sum'),       # 11: ['=', 'T5', '_', 'sum']
        Quadruple('+', 'i', '1', 'T2'),          # 12: ['+', 'i', '1', 'T2']
        Quadruple('=', 'T2', None, 'i'),         # 13: ['=', 'T2', '_', 'i']
        Quadruple('j', None, None, '5'),         # 14: ['j', '_', '_', 5]
        Quadruple('para', 'sum', None, None),    # 15: ['para', 'sum', '_', '_']
        Quadruple('call', 'write', None, None),  # 16: ['call', 'write', '_', '_']
        Quadruple('ret', '0', None, None)        # 17: ['ret', '0', '_', '_']
    ]
    
    # 创建代码生成器
    cg = CodeGenerator()
    
    # 生成汇编代码
    print("\n测试用例：for嵌套if,求1到给定数N以内所有奇数的和")
    print("-" * 60)
    print("\n源代码：")
    print("""
main()
{
    int i,N,sum = 0;
    N = read();
    for(i=1;i<=N;i=i+1)
    {
        if(i%2 == 1)
            sum = sum+i;
    }
    write(sum);
}
    """)
    
    print("\n四元式：")
    for i, quad in enumerate(quads):
        print(f"{i}: {quad}")
    
    print("\n生成的汇编代码：")
    asm_code = cg.generate_code(quads, 4)  # 使用4作为测试编号
    print(asm_code)
    
    # 将汇编代码保存到文件
    with open("test_for_if.asm", "w") as f:
        f.write(asm_code)
    print("\n汇编代码已保存到 test_for_if.asm")

if __name__ == "__main__":
    test_for_if_sum() 