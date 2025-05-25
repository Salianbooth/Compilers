from code_generator import CodeGenerator, Quadruple
from compiler import Compiler

def test_for_if_sum():
    """
    测试用例：for嵌套if,求1到给定数N以内所有奇数的和
    源代码直接转汇编
    """
    # 源代码
    source_code = """
    int main()
    {
        int i, N, sum = 0;
        N = read();
        for(i=1; i<=N; i=i+1)
        {
            if(i%2 == 1)
                sum = sum+i;
        }
        write(sum);
        return 0;
    }
    """
    
    print("\n测试用例：for嵌套if,求1到给定数N以内所有奇数的和")
    print("-" * 60)
    print("\n源代码：")
    print(source_code)
    
    # 使用编译器从源代码生成四元式
    compiler = Compiler()
    result = compiler.compile(source_code)
    
    if result['status'] != 'success':
        print(f"编译失败: {result['error']}")
        return
    
    print("\n词法分析结果:")
    for i, (syn, tok) in enumerate(result['tokens']):
        print(f"{i}: {tok} ({syn})")
    
    quads = result['quads']
    print("\n生成的四元式：")
    for i, quad in enumerate(quads):
        print(f"{i}: {quad}")
    
    # 创建代码生成器，将四元式转换为汇编代码
    cg = CodeGenerator()
    
    # 生成汇编代码
    print("\n生成的汇编代码：")
    asm_code = cg.generate_code(quads, 4)  # 使用4作为测试编号
    print(asm_code)
    
    # 将汇编代码保存到文件
    with open("test_for_if.asm", "w") as f:
        f.write(asm_code)
    print("\n汇编代码已保存到 test_for_if.asm")

if __name__ == "__main__":
    test_for_if_sum() 