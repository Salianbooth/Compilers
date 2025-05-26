from collections import deque

class SemanticError(Exception):
    """语义错误异常类"""
    pass

class Symbol:
    """符号类，用于表示变量、函数、常量等"""
    def __init__(self, name, kind, typ, params=None, scope_path=None, value=None):
        self.name = name           # 符号名称
        self.kind = kind           # 符号类型：'var'（变量）、'func'（函数）、'const'（常量）
        self.typ = typ             # 符号的数据类型，例如'int'、'char *'等
        self.params = params or []  # 函数参数类型列表（如果是函数）
        self.scope_path = scope_path  # 符号的作用域路径
        self.value = value          # 常量的字面值（如果是常量）
        self.is_vararg = False      # 是否为可变参数函数
        self.is_input_function = False  # 是否为输入函数（如scanf）

    def __repr__(self):
        # 格式化输出符号信息
        p = f", params={self.params}" if self.params else ""
        v = f", value={self.value!r}" if self.kind == 'const' else ""
        va = ", vararg" if self.is_vararg else ""
        return f"<Symbol {self.name}:{self.kind}:{self.typ}{p}{va} @{self.scope_path}>"

class SymbolTable:
    """符号表类，用于管理作用域和符号"""
    def __init__(self):
        self.scopes = deque()  # 使用双端队列存储作用域
        self.history = []       # 记录作用域历史，用于打印
        self._scope_id = 0     # 作用域ID计数
        self.scope_path = []    # 当前作用域路径
        self.enter_scope()      # 进入全局作用域

    def enter_scope(self):
        """进入新的作用域"""
        self._scope_id += 1  # 增加作用域ID
        self.scope_path = self.scope_path + [self._scope_id]  # 更新作用域路径
        new_scope = {}  # 创建新的作用域字典
        self.scopes.append(new_scope)  # 将新作用域添加到队列
        self.history.append((list(self.scope_path), new_scope))  # 记录作用域历史

    def leave_scope(self):
        """离开当前作用域"""
        self.scopes.pop()  # 移除当前作用域
        self.scope_path = self.scope_path[:-1]  # 更新作用域路径

    def declare(self, sym: Symbol):
        """在当前作用域中声明符号"""
        curr = self.scopes[-1]  # 获取当前作用域
        if sym.name in curr:
            raise SemanticError(f"重复声明: {sym.name} in scope {self.scope_path}")  # 抛出重复声明错误
        sym.scope_path = list(self.scope_path)  # 设置符号的作用域路径
        curr[sym.name] = sym  # 将符号添加到当前作用域

    def lookup(self, name):
        """查找符号，从内层作用域向外层查找"""
        for scope in reversed(self.scopes):  # 从内层作用域开始查找
            if name in scope:
                return scope[name]  # 返回找到的符号
        return None  # 如果未找到，返回None

    def __repr__(self):
        """格式化输出符号表内容"""
        # 收集符号信息
        consts = []  # 常量列表
        strings = []  # 字符串列表
        vars_ = []  # 变量列表
        funcs = []  # 函数列表
        for path, scope in self.history:
            sid = ";".join(map(str, path))  # 生成作用域ID字符串
            for sym in scope.values():
                if sym.kind == 'const':
                    consts.append((sym.name, sym.typ, sym.value, sid))  # 添加常量信息
                elif sym.kind == 'var':
                    vars_.append((sym.name, sym.typ, sid))  # 添加变量信息
                elif sym.kind == 'func':
                    funcs.append((sym.name, sym.typ, len(sym.params), sym.params, sid))  # 添加函数信息
                if sym.kind == 'const' and sym.typ == 'char *':
                    strings.append((sym.name, sym.value, sid))  # 添加字符串信息

        # 输出符号表内容
        lines = []

        # 常量表
        lines.append("常量表：")
        lines.append(f"{'name':<6} {'type':<8} {'value':<12} {'scope'}")
        for n, t, v, s in consts:
            if t == 'char *': continue  # 跳过字符串常量
            lines.append(f"{n:<6} {t:<8} {repr(v):<12} {s}")
        lines.append("")

        # 字符串表
        lines.append("字符串表：")
        lines.append(f"{'name':<6} {'string':<20} {'scope'}")
        for n, val, s in strings:
            lines.append(f"{n:<6} {repr(val):<20} {s}")
        lines.append("")

        # 变量表
        lines.append("变量表：")
        lines.append(f"{'name':<6} {'type':<8} {'scope'}")
        for n, t, s in vars_:
            lines.append(f"{n:<6} {t:<8} {s}")
        lines.append("")

        # 函数表
        lines.append("函数表：")
        lines.append(f"{'name':<6} {'retType':<8} {'#params':<8} {'paramTypes':<15} {'scope'}")
        for n, rt, pn, pts, s in funcs:
            lines.append(f"{n:<6} {rt:<8} {pn:<8} {pts!s:<15} {s}")

        return "\n".join(lines)

    def lookup_all(self):
        """查找所有符号"""
        symbols = []
        for scope in self.scopes:
            symbols.extend(scope.values())  # 收集所有作用域中的符号
        return symbols

class SemanticAnalyzer:
    """语义分析器类"""
    def __init__(self):
        self.symbols = SymbolTable()  # 创建符号表实例
        self._const_seq = 0  # 常量序列计数

    def add_constant(self, value, type='int'):
        """添加常量到符号表，如果已存在则返回已有常量名"""
        # 检查是否已存在相同值的常量
        for sym in self.symbols.lookup_all():
            if sym.kind == 'const' and sym.typ == type and sym.value == value:
                return sym.name  # 返回已存在的常量名
        
        # 创建新的常量
        self._const_seq += 1  # 增加常量序列计数
        name = f"C{self._const_seq}"  # 生成常量名
        sym = Symbol(name, 'const', type, value=value)  # 创建常量符号
        self.symbols.declare(sym)  # 在符号表中声明常量
        return name  # 返回新常量名

    def handle_variable_decl(self, ast):
        """处理变量声明"""
        # 获取变量名（从ID节点的text属性）
        id_node = ast.children[1]  # 假设变量名在第二个子节点
        var_name = id_node.text if hasattr(id_node, 'text') else id_node.value  # 获取变量名
        if not var_name:
            return  # 如果没有变量名，返回

        # 添加变量到符号表
        var_sym = Symbol(var_name, 'var', 'int')  # 创建变量符号，假设类型为'int'
        self.symbols.declare(var_sym)  # 在符号表中声明变量
        
        # 处理变量初始化
        if len(ast.children) > 2 and ast.children[2].label == 'VarDeclPrime':
            init_node = ast.children[2].children[1]  # 获取初始化节点
            if init_node.label == 'INT_LITERAL':
                init_value = init_node.text if hasattr(init_node, 'text') else init_node.value  # 获取初始化值
                if init_value:
                    self.add_constant(init_value, 'int')  # 添加常量到符号表

    def handle_function_decl(self, ast):
        """处理函数声明"""
        # 获取函数名
        id_node = ast.children[1]  # 假设函数名在第二个子节点
        func_name = id_node.text if hasattr(id_node, 'text') else id_node.value  # 获取函数名
        if not func_name:
            return  # 如果没有函数名，返回

        # 收集参数类型
        param_types = []
        for child in ast.children:
            if child.label == 'Param':
                param_types.append(['int'])  # 假设参数类型为'int'

        # 添加函数到符号表
        func_sym = Symbol(func_name, 'func', 'int', params=param_types)  # 创建函数符号
        self.symbols.declare(func_sym)  # 在符号表中声明函数
        
        # 进入函数作用域
        self.symbols.enter_scope()
        
        # 处理参数
        for child in ast.children:
            if child.label == 'Param':
                param_node = child.children[1]  # 获取参数节点
                param_name = param_node.text if hasattr(param_node, 'text') else param_node.value  # 获取参数名
                if param_name:
                    param_sym = Symbol(param_name, 'var', 'int')  # 创建参数符号
                    self.symbols.declare(param_sym)  # 在符号表中声明参数
        
        # 处理函数体
        for child in ast.children:
            if child.label == 'CompoundStmt':
                self.analyze(child)  # 递归分析函数体
        
        # 退出函数作用域
        self.symbols.leave_scope()

    def analyze(self, ast):
        """分析语法树"""
        if ast is None:
            return  # 如果AST为空，返回

        # 处理声明节点
        if ast.label == 'Decl':
            if ast.children[0].label == 'int':
                # 判断是函数声明还是变量声明
                if len(ast.children) >= 3 and ast.children[2].label == '(':
                    self.handle_function_decl(ast)  # 处理函数声明
                else:
                    self.handle_variable_decl(ast)  # 处理变量声明

        # 处理复合语句
        elif ast.label == 'CompoundStmt':
            self.symbols.enter_scope()  # 进入新的作用域
            for child in ast.children:
                self.analyze(child)  # 递归分析每个子节点
            self.symbols.leave_scope()  # 离开作用域

        # 处理字面量
        elif ast.label == 'INT_LITERAL':
            value = ast.text if hasattr(ast, 'text') else ast.value  # 获取字面量值
            if value:
                self.add_constant(value, 'int')  # 添加常量到符号表

        # 处理其他节点
        for child in ast.children:
            self.analyze(child)  # 递归分析每个子节点

    def get_symbol_tables(self):
        """获取符号表"""
        return {
            'constants': {sym.name: {'type': sym.typ, 'value': sym.value, 'scope': sym.scope_path[-1]} 
                         for sym in self.symbols.lookup_all() if sym.kind == 'const'},
            'strings': {sym.name: {'string': sym.value, 'scope': sym.scope_path[-1]} 
                       for sym in self.symbols.lookup_all() if sym.kind == 'const' and sym.typ == 'char *'},
            'variables': {sym.name: {'type': sym.typ, 'scope': sym.scope_path[-1]} 
                         for sym in self.symbols.lookup_all() if sym.kind == 'var'},
            'functions': {sym.name: {'retType': sym.typ, '#params': len(sym.params), 
                                   'paramTypes': sym.params, 'scope': sym.scope_path[-1]} 
                         for sym in self.symbols.lookup_all() if sym.kind == 'func'}
        }

def run_semantic_analysis(ast_root):
    """运行语义分析的入口函数"""
    analyzer = SemanticAnalyzer()  # 创建语义分析器实例
    analyzer.analyze(ast_root)  # 分析给定的AST根节点
    return analyzer.get_symbol_tables()  # 返回符号表