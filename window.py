# window.py
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QFileDialog, QTextEdit,
    QSplitter, QWidget, QPlainTextEdit
)
from PyQt5.QtGui import QFont  # 用于创建并设置字体
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QPainter, QColor, QFontMetricsF
from manual_lexer import lexical_analysis as manual_lexical_analysis
from manual_lexer import tokens_to_terminals
from auto_lexer import lexer, analyze

# window.py 或者其他脚本里
from Compilers.ll_parser.core.ll_main import parse_with_tree
from Compilers.ll_parser.core.grammar_oop import Grammar, load_grammar_from_file
from Compilers.ll_parser.core.parse_table import build_parse_table
from Compilers.ll_parser.core.parse_tree import cst_to_ast
from Compilers.semantic_analyzer import run_semantic_analysis



# 行号绘制组件
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


# 代码编辑器，带行号显示
class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.lineNumberArea = LineNumberArea(self)

        # 文本块变化和更新事件
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.updateLineNumberAreaWidth(0)

        # 设置等宽字体
        font = self.document().defaultFont()
        font.setFamily("Courier New")
        font.setPointSize(10)
        self.document().setDefaultFont(font)
        self.setTabStopDistance(QFontMetricsF(font).horizontalAdvance(' ') * 4)

    def lineNumberAreaWidth(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value //= 10
            digits += 1
        space = 3 + QFontMetricsF(self.font()).horizontalAdvance('9') * digits
        return int(space)

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor(240, 240, 240))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        font_metrics = QFontMetricsF(self.font())
        line_height = font_metrics.height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor(100, 100, 100))
                painter.drawText(0, int(top), self.lineNumberArea.width(), int(line_height), Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1


# 主窗口
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.analysis_mode = '手动'
        # 构建文法与预测表，只做一次
        self.grammar = Grammar()
        # 获取当前文件所在目录的路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cfg_path = os.path.join(current_dir, 'll_parser', 'examples', 'CFG.txt')
        load_grammar_from_file(cfg_path, self.grammar)
        self.grammar.finalize(eliminate_lr=True, left_fact=True)
        self.table, self.is_ll1, self.terminals = build_parse_table(self.grammar, start_symbol='Program')
        self.initUI()

    def initUI(self):
        self.setWindowTitle('词法 & 语法 & 语义 分析器')
        self.setGeometry(850, 200, 1200, 800)

        menubar = self.menuBar()
        open_action = QAction('打开', self)
        open_action.triggered.connect(self.open_file)
        menubar.addAction(open_action)
        save_action = QAction('保存', self)
        save_action.triggered.connect(self.save_file)
        menubar.addAction(save_action)
        lex_action = QAction('词法分析', self)
        lex_action.triggered.connect(self.lexical_analysis)
        menubar.addAction(lex_action)
        syntax_action = QAction('语法分析', self)
        syntax_action.triggered.connect(self.syntax_analysis)
        menubar.addAction(syntax_action)
        semantic_action = QAction('语义分析', self)
        semantic_action.triggered.connect(self.semantic_analysis)
        menubar.addAction(semantic_action)

        mode_menu = menubar.addMenu('词法模式')
        manual_action = QAction('手动分析', self)
        manual_action.triggered.connect(lambda: self.set_analysis_mode('手动'))
        mode_menu.addAction(manual_action)
        auto_action = QAction('自动分析（PLY）', self)
        auto_action.triggered.connect(lambda: self.set_analysis_mode('自动'))
        mode_menu.addAction(auto_action)

        self.create_t_shape_layout()

    def set_analysis_mode(self, mode):
        self.analysis_mode = mode
        self.error_text_edit.setText(f"已切换为 {mode} 分析模式")

    def create_t_shape_layout(self):
        # 整体左右分割
        main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(main_splitter)

        # 左侧：源代码 + 错误
        left_splitter = QSplitter(Qt.Vertical)
        self.source_text_edit = CodeEditor()
        self.source_text_edit.setPlaceholderText("源代码区")
        left_splitter.addWidget(self.source_text_edit)
        self.error_text_edit = QTextEdit()
        self.error_text_edit.setReadOnly(True)
        self.error_text_edit.setPlaceholderText("Error")
        self.error_text_edit.setFont(QFont("Courier New", 10))
        left_splitter.addWidget(self.error_text_edit)
        left_splitter.setSizes([600, 200])
        main_splitter.addWidget(left_splitter)

        # 右侧：词法 + 语法 + 语义
        right_splitter = QSplitter(Qt.Vertical)
        self.lex_text_edit = QTextEdit()
        self.lex_text_edit.setReadOnly(True)
        self.lex_text_edit.setPlaceholderText("词法分析结果")
        self.lex_text_edit.setFont(QFont("Courier New", 10))
        right_splitter.addWidget(self.lex_text_edit)
        self.syntax_text_edit = QTextEdit()
        self.syntax_text_edit.setReadOnly(True)
        self.syntax_text_edit.setPlaceholderText("语法分析结果")
        self.syntax_text_edit.setFont(QFont("Courier New", 10))
        right_splitter.addWidget(self.syntax_text_edit)
        self.semantic_text_edit = QTextEdit()
        self.semantic_text_edit.setReadOnly(True)
        self.semantic_text_edit.setPlaceholderText("语义分析结果")
        self.semantic_text_edit.setFont(QFont("Courier New", 10))
        right_splitter.addWidget(self.semantic_text_edit)
        right_splitter.setSizes([200, 200, 200])
        main_splitter.addWidget(right_splitter)

        main_splitter.setSizes([500, 500])

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "打开文件", "", "所有文件 (*);;文本文件 (*.txt);;C 文件 (*.c)")
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.source_text_edit.setPlainText(f.read())

    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "C 文件 (*.c);;文本文件 (*.txt);;所有文件 (*)")
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.source_text_edit.toPlainText())

    def lexical_analysis(self):
        source = self.source_text_edit.toPlainText()
        try:
            if self.analysis_mode == '手动':
                tokens, errs = manual_lexical_analysis(source)
                lines = ["序号\t单词\t种别码", "-"*40]
                for i, (syn, tok) in enumerate(tokens, start=1):
                    if syn == 0: continue
                    if 1 <= syn < 17:
                        typ = "关键字"
                    elif 20 <= syn < 44:
                        typ = "运算符"
                    elif 50 <= syn < 64:
                        typ = "分隔符"
                    elif syn == 45:
                        typ = "标识符"
                    elif syn == 46:
                        typ = "整数"
                    elif syn == 47:
                        typ = "浮点数"
                    elif syn == 48:
                        typ = "字符串"
                    else:
                        typ = "未知"
                    lines.append(f"{i}\t{tok}\t{typ}({syn})")
                self.lex_text_edit.setPlainText("\n".join(lines))
                self.error_text_edit.setPlainText("无词法错误" if not errs else "词法错误:\n" + "\n".join(errs))
            else:
                tokens, errs = analyze(source)
                lexer.input(source)
                lines = ["序号\t单词\t类型", "-"*40]
                idx = 1
                while True:
                    tk = lexer.token()
                    if not tk: break
                    lines.append(f"{idx}\t{tk.value}\t{tk.type}")
                    idx += 1
                self.lex_text_edit.setPlainText("\n".join(lines))
                self.error_text_edit.setPlainText("无词法错误" if not errs else "词法错误:\n" + "\n".join(errs))
        except Exception as e:
            self.error_text_edit.setPlainText(f"词法分析异常: {e}")

    def syntax_analysis(self):
        source = self.source_text_edit.toPlainText()
        tokens, lex_errs = manual_lexical_analysis(source)
        if lex_errs:
            self.error_text_edit.setPlainText(
                "词法错误，无法进行语法分析:\n" + "\n".join(lex_errs)
            )
            return

        # 把 tokens 拆成两并行数组
        terms_only = tokens_to_terminals(tokens)
        lexemes_only = [lexeme for (_, lexeme) in tokens]
        term_pairs = list(zip(terms_only, lexemes_only))

        sync_set = {';', '}'}

        try:
            # 传入 (类型, 文本) 对列表
            cst = parse_with_tree(term_pairs, self.grammar, self.table, 'Program')
            ast = cst_to_ast(cst)

            # 递归构造打印字符串
            out = []

            def recurse(n, pref='', last=True):
                conn = '└─ ' if last else '├─ '
                if n.value is not None and n.is_leaf():
                    out.append(f"{pref}{conn}{n.label}: {n.value}")
                else:
                    out.append(f"{pref}{conn}{n.label}")
                newp = pref + ('   ' if last else '│  ')
                for i, ch in enumerate(n.children):
                    recurse(ch, newp, i == len(n.children) - 1)

            recurse(ast)
            self.syntax_text_edit.setPlainText("\n".join(out))
            self.error_text_edit.setPlainText("语法分析成功，无错误。")

        except SyntaxError as e:
            msg = e.args[0] if e.args else str(e)
            info = f"语法错误，原因: {msg}"
            self.syntax_text_edit.clear()
            self.error_text_edit.setPlainText(info)

    def semantic_analysis(self):
        """执行语义分析"""
        try:
            # 先进行词法分析
            source = self.source_text_edit.toPlainText()
            tokens, lex_errs = manual_lexical_analysis(source)
            if lex_errs:
                self.error_text_edit.setPlainText(
                    "词法错误，无法进行语义分析:\n" + "\n".join(lex_errs)
                )
                return

            # 把 tokens 拆成两并行数组
            terms_only = tokens_to_terminals(tokens)
            lexemes_only = [lexeme for (_, lexeme) in tokens]
            term_pairs = list(zip(terms_only, lexemes_only))

            # 进行语法分析获取语法树
            try:
                cst = parse_with_tree(term_pairs, self.grammar, self.table, 'Program')
                ast = cst_to_ast(cst)
            except SyntaxError as e:
                msg = e.args[0] if e.args else str(e)
                self.error_text_edit.setPlainText(f"语法错误，无法进行语义分析: {msg}")
                return
            
            # 执行语义分析
            symbol_tables = run_semantic_analysis(ast)
            
            # 显示符号表
            result = "语义分析结果：\n\n"
            
            # 显示常量表
            result += "常量表：\n"
            result += "name   type     value        scope\n"
            result += "----------------------------------------\n"
            for name, info in sorted(symbol_tables['constants'].items(), key=lambda x: int(x[0][1:])):
                result += f"{name:<8} {info['type']:<8} {info['value']:<12} {info['scope']}\n"
            result += "\n"
            
            # 显示字符串表
            result += "字符串表：\n"
            result += "name   string               scope\n"
            result += "----------------------------------------\n"
            for name, info in symbol_tables['strings'].items():
                result += f"{name:<8} {info['string']:<20} {info['scope']}\n"
            result += "\n"
            
            # 显示变量表
            result += "变量表：\n"
            result += "name        type     scope\n"
            result += "----------------------------------------\n"
            for name, info in sorted(symbol_tables['variables'].items()):
                result += f"{name:<12} {info['type']:<8} {info['scope']}\n"
            result += "\n"
            
            # 显示函数表
            result += "函数表：\n"
            result += "name       retType  #params  paramTypes      scope\n"
            result += "----------------------------------------\n"
            for name, info in sorted(symbol_tables['functions'].items()):
                result += f"{name:<12} {info['retType']:<8} {info['#params']:<8} {str(info['paramTypes']):<15} {info['scope']}\n"
            
            self.semantic_text_edit.setPlainText(result)
            self.error_text_edit.setPlainText("语义分析成功，无错误。")
            
        except Exception as e:
            self.error_text_edit.setPlainText(f"语义分析错误：{str(e)}")
            self.semantic_text_edit.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())