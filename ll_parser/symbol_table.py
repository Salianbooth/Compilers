# 作   者：陈中超
# 开发日期:2025/5/20
from typing import Dict, List, Optional, Any

class SymbolInfo:
    """
    存储符号的相关信息，如类型、声明位置、额外属性等
    """
    def __init__(self, name: str, sym_type: str, lineno: Optional[int] = None, **attrs: Any):
        self.name = name
        self.type = sym_type
        self.lineno = lineno
        self.attrs = attrs

    def __repr__(self):
        return f"SymbolInfo(name={self.name!r}, type={self.type!r}, lineno={self.lineno}, attrs={self.attrs})"

class SymbolTable:
    """
    单个作用域的符号表
    """
    def __init__(self):
        # name -> SymbolInfo
        self._symbols: Dict[str, SymbolInfo] = {}

    def declare(self, name: str, sym_type: str, lineno: Optional[int] = None, **attrs: Any) -> SymbolInfo:
        """
        在当前作用域声明新符号，若重复声明则抛出错误。
        返回插入的 SymbolInfo。
        """
        if name in self._symbols:
            raise KeyError(f"重复声明符号 '{name}' (line {lineno})")
        info = SymbolInfo(name, sym_type, lineno, **attrs)
        self._symbols[name] = info
        return info

    def lookup(self, name: str) -> Optional[SymbolInfo]:
        """
        在当前作用域查找符号，找不到返回 None。
        """
        return self._symbols.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._symbols

    def __repr__(self):
        return f"SymbolTable({self._symbols})"

class ScopedSymbolTable:
    """
    管理多个作用域的栈：全局、函数、块等
    """
    def __init__(self):
        # 作用域栈, 栈顶为当前作用域
        self.scopes: List[SymbolTable] = [SymbolTable()]

    def enter_scope(self) -> None:
        """进入一个新作用域"""
        self.scopes.append(SymbolTable())

    def exit_scope(self) -> None:
        """退出当前作用域"""
        if len(self.scopes) <= 1:
            raise IndexError("无法退出全局作用域")
        self.scopes.pop()

    def declare(self, name: str, sym_type: str, lineno: Optional[int] = None, **attrs: Any) -> SymbolInfo:
        """
        在当前作用域声明符号，重复声明抛错
        """
        return self.scopes[-1].declare(name, sym_type, lineno, **attrs)

    def lookup(self, name: str) -> Optional[SymbolInfo]:
        """
        从当前作用域向外层依次查找符号，返回首次命中的 SymbolInfo 或 None
        """
        for table in reversed(self.scopes):
            info = table.lookup(name)
            if info is not None:
                return info
        return None

    def __repr__(self):
        return f"ScopedSymbolTable(scopes={self.scopes})"

# 文件名: symbol_table.py
# 用于后续的语义分析模块，引入该模块以管理声明、查找及作用域嵌套。
