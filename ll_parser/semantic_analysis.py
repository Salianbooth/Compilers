from symbol_table import ScopedSymbolTable, SymbolInfo
from parse_tree import Node

class SemanticError(Exception):
    """语义分析错误"""
    pass

class SemanticAnalyzer:
    def __init__(self):
        self.symtab = ScopedSymbolTable()
        self.errors = []  # List[str]

    def error(self, msg: str, node: Node):
        # 尝试获取行号属性
        lineno = getattr(node, 'lineno', None)
        loc = f" (line {lineno})" if lineno else ""
        self.errors.append(msg + loc)

    def analyze(self, ast: Node) -> list:
        """入口：对 AST 根节点执行语义分析"""
        self.visit(ast)
        return self.errors

    def visit(self, node: Node):
        method = f"visit_{node.label}"
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: Node):
        for child in node.children:
            if isinstance(child, Node):
                self.visit(child)

    # Program -> PPList DeclList StmtList
    def visit_Program(self, node: Node):
        # 全局作用域已自动创建
        for child in node.children:
            self.visit(child)

    # Decl -> Type ID DeclTail
    def visit_Decl(self, node: Node):
        # children: [Type, ID, DeclTail]
        _, id_node, tail = node.children
        name = id_node.label
        var_type = node.children[0].label  # Type 节点直接为 int/float/void
        try:
            self.symtab.declare(name, var_type)
        except KeyError:
            self.error(f"重复声明变量 '{name}'", id_node)
        # 继续分析初始化或函数体
        self.visit(tail)

    # VarDeclPrime -> = Expr ; | ;
    def visit_VarDeclPrime(self, node: Node):
        if node.children and node.children[0].label == '=':
            expr = node.children[1]
            self.visit(expr)

    # DeclTail -> ( ParamList ) CompoundStmt | VarDeclPrime
    def visit_DeclTail(self, node: Node):
        first = node.children[0]
        if first.label == '(':
            # 函数声明
            # ID 和参数已在外部声明，进入新作用域
            self.symtab.enter_scope()
            param_list = node.children[1]
            self.visit(param_list)
            # 函数体
            body = node.children[3]
            self.visit(body)
            self.symtab.exit_scope()
        else:
            # 变量后缀
            self.visit(node.children[0])

    # ParamList -> Param ParamListTail | ε
    def visit_ParamList(self, node: Node):
        for child in node.children:
            if child.label == 'Param':
                self.visit(child)

    # Param -> Type ID
    def visit_Param(self, node: Node):
        _, id_node = node.children
        name = id_node.label
        typ = node.children[0].label
        try:
            self.symtab.declare(name, typ)
        except KeyError:
            self.error(f"重复声明参数 '{name}'", id_node)

    # CompoundStmt -> { DeclList StmtList }
    def visit_CompoundStmt(self, node: Node):
        self.symtab.enter_scope()
        # children: ['{', DeclList, StmtList, '}']
        self.visit(node.children[1])
        self.visit(node.children[2])
        self.symtab.exit_scope()

    # StmtList and DeclList: 递归列表或 ε
    def visit_StmtList(self, node: Node):
        for child in node.children:
            if isinstance(child, Node) and child.label != 'ε':
                self.visit(child)

    def visit_DeclList(self, node: Node):
        for child in node.children:
            if isinstance(child, Node) and child.label != 'ε':
                self.visit(child)

    # AssignStmt -> ID = Expr ;
    def visit_AssignStmt(self, node: Node):
        id_node = node.children[0]
        expr_node = node.children[2]
        info = self.symtab.lookup(id_node.label)
        if not info:
            self.error(f"未声明的标识符 '{id_node.label}'", id_node)
        self.visit(expr_node)

    # ExprStmt -> Expr ; | ;
    def visit_ExprStmt(self, node: Node):
        if node.children and node.children[0].label != ';':
            self.visit(node.children[0])

    # IfStmt -> if ( Expr ) Stmt ElseStmt
    def visit_IfStmt(self, node: Node):
        cond = node.children[2]
        self.visit(cond)
        self.visit(node.children[4])
        self.visit(node.children[5])

    # WhileStmt -> while ( Expr ) Stmt
    def visit_WhileStmt(self, node: Node):
        cond = node.children[2]
        self.visit(cond)
        self.visit(node.children[4])

    # ReturnStmt -> return Expr ;
    def visit_ReturnStmt(self, node: Node):
        expr = node.children[1]
        self.visit(expr)

    # Expr and binary operations
    def visit_Expr(self, node: Node):
        # Expr -> ExprOr
        self.visit(node.children[0])

    # ExprPrimary -> ID | INT_LITERAL | FLOAT_LITERAL
    def visit_ExprPrimary(self, node: Node):
        leaf = node.children[0] if node.children else node
        if leaf.label == 'ID':
            # 使用型 ID
            # 实际 label 存储标识符名称
            name = leaf.children[0].label
            info = self.symtab.lookup(name)
            if not info:
                self.error(f"未声明的标识符 '{name}'", leaf)
        # 对常量不做检查

    # 其它节点使用默认遍历
