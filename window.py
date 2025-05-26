import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QFileDialog, QTextEdit,
    QSplitter, QWidget, QPlainTextEdit
)
from PyQt5.QtGui import QFont  # 用于创建并设置字体
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QPainter, QColor, QFontMetricsF
from Compilers.lexer.manual_lexer import lexical_analysis as manual_lexical_analysis
from Compilers.lexer.manual_lexer import tokens_to_terminals
from Compilers.lexer.auto_lexer import lexer, analyze

# 导入编译器组件
from Compilers.ll_parser.core.ll_main import parse_with_tree
from Compilers.ll_parser.core.parse_tree import cst_to_ast
from Compilers.semantic_analyzer import run_semantic_analysis
from Compilers.ir_generator import IRBuilder
from Compilers.compiler import Compiler, format_quads, format_string_literals


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
        self.compiler = Compiler()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('词法 & 语法 & 语义 & 中间代码 分析器')
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
        ir_action = QAction('中间代码生成', self)
        ir_action.triggered.connect(self.ir_generation)
        menubar.addAction(ir_action)
        compile_action = QAction('一键编译', self)
        compile_action.triggered.connect(self.compile_all)
        menubar.addAction(compile_action)
        generate_code_action = QAction('生成目标代码', self)
        generate_code_action.triggered.connect(self.generate_target_code)
        menubar.addAction(generate_code_action)

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
        self.output_text_edit.setPlainText(f"已切换为 {mode} 分析模式")

    def create_t_shape_layout(self):
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

        # 右侧：合并输出区
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        self.output_text_edit.setPlaceholderText("输出区域")
        self.output_text_edit.setFont(QFont("Courier New", 10))
        main_splitter.addWidget(self.output_text_edit)

        main_splitter.setSizes([500, 700])

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
                self.output_text_edit.setPlainText("\n".join(lines))
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
                self.output_text_edit.setPlainText("\n".join(lines))
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

        terms_only = tokens_to_terminals(tokens)
        lexemes_only = [lexeme for (_, lexeme) in tokens]
        term_pairs = list(zip(terms_only, lexemes_only))

        try:
            cst = parse_with_tree(term_pairs, self.compiler.grammar, self.compiler.table, 'Program')
            ast = cst_to_ast(cst)
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
            self.output_text_edit.setPlainText("\n".join(out))
            self.error_text_edit.setPlainText("语法分析成功，无错误。")
        except SyntaxError as e:
            msg = e.args[0] if e.args else str(e)
            self.output_text_edit.clear()
            self.error_text_edit.setPlainText(f"语法错误，原因: {msg}")

    def semantic_analysis(self):
        try:
            source = self.source_text_edit.toPlainText()
            tokens, lex_errs = manual_lexical_analysis(source)
            if lex_errs:
                self.error_text_edit.setPlainText(
                    "词法错误，无法进行语义分析:\n" + "\n".join(lex_errs)
                )
                return

            terms_only = tokens_to_terminals(tokens)
            lexemes_only = [lexeme for (_, lexeme) in tokens]
            term_pairs = list(zip(terms_only, lexemes_only))

            try:
                cst = parse_with_tree(term_pairs, self.compiler.grammar, self.compiler.table, 'Program')
                ast = cst_to_ast(cst)
            except SyntaxError as e:
                msg = e.args[0] if e.args else str(e)
                self.error_text_edit.setPlainText(f"语法错误，无法进行语义分析: {msg}")
                return

            symbol_tables = run_semantic_analysis(ast)
            result = []
            result.append("语义分析结果：\n")
            # Constants
            result.append("常量表：")
            for name, info in sorted(symbol_tables['constants'].items(), key=lambda x: int(x[0][1:])):
                result.append(f"{name:<8} {info['type']:<8} {info['value']:<12} {info['scope']}")
            result.append("\n字符串表：")
            for name, info in symbol_tables['strings'].items():
                result.append(f"{name:<8} {info['string']:<20} {info['scope']}")
            result.append("\n变量表：")
            for name, info in sorted(symbol_tables['variables'].items()):
                result.append(f"{name:<12} {info['type']:<8} {info['scope']}")
            result.append("\n函数表：")
            for name, info in sorted(symbol_tables['functions'].items()):
                result.append(f"{name:<12} {info['retType']:<8} {info['#params']:<8} {str(info['paramTypes']):<15} {info['scope']}")

            self.output_text_edit.setPlainText("\n".join(result))
            self.error_text_edit.setPlainText("语义分析成功，无错误。")
        except Exception as e:
            self.error_text_edit.setPlainText(f"语义分析错误：{str(e)}")
            self.output_text_edit.clear()

    def ir_generation(self):
        try:
            source = self.source_text_edit.toPlainText()
            tokens, lex_errs = manual_lexical_analysis(source)
            if lex_errs:
                self.error_text_edit.setPlainText(
                    "词法错误，无法进行中间代码生成:\n" + "\n".join(lex_errs)
                )
                return

            terms_only = tokens_to_terminals(tokens)
            lexemes_only = [lexeme for (_, lexeme) in tokens]
            term_pairs = list(zip(terms_only, lexemes_only))

            try:
                cst = parse_with_tree(term_pairs, self.compiler.grammar, self.compiler.table, 'Program')
                ast = cst_to_ast(cst)
            except SyntaxError as e:
                msg = e.args[0] if e.args else str(e)
                self.error_text_edit.setPlainText(f"语法错误，无法进行中间代码生成: {msg}")
                return

            irb = IRBuilder()
            irb.gen(ast)
            quads = irb.get_quads()
            string_literals = irb.get_string_literals()

            result = format_quads(quads) + "\n" + format_string_literals(string_literals)
            self.output_text_edit.setPlainText(result)
            self.error_text_edit.setPlainText("中间代码生成成功，无错误。")
        except Exception as e:
            self.error_text_edit.setPlainText(f"中间代码生成错误：{str(e)}")
            self.output_text_edit.clear()

    def compile_all(self):
        source = self.source_text_edit.toPlainText()
        result = self.compiler.compile(source, self.analysis_mode)
        if result['status'] == 'success':
            # Combine all outputs
            combined = []
            combined.append("--- 词法分析 ---")
            for i, (syn, tok) in enumerate(result['tokens'], start=1):
                if syn == 0: continue
                combined.append(f"{i}\t{tok}\t{syn}")
            combined.append("\n--- 语法分析 ---")
            def recurse(n, pref='', last=True):
                conn = '└─ ' if last else '├─ '
                if n.value is not None and n.is_leaf():
                    combined.append(f"{pref}{conn}{n.label}: {n.value}")
                else:
                    combined.append(f"{pref}{conn}{n.label}")
                newp = pref + ('   ' if last else '│  ')
                for i, ch in enumerate(n.children): recurse(ch, newp, i == len(n.children)-1)
            recurse(result['ast'])
            combined.append("\n--- 语义分析 ---")
            # Similar to above semantic formatting
            for name, info in sorted(result['symbol_tables']['variables'].items()):
                combined.append(f"Var {name}: {info['type']}")
            combined.append("\n--- 中间代码 ---")
            combined.append(format_quads(result['quads']))
            combined.append(format_string_literals(result['string_literals']))

            self.output_text_edit.setPlainText("\n".join(combined))
            self.error_text_edit.setPlainText("编译成功，无错误。")
        else:
            self.error_text_edit.setPlainText(f"编译失败: {result['error']}")

    def generate_target_code(self):
        from io import StringIO
        import sys

        old_stdout = sys.stdout
        new_stdout = StringIO()
        sys.stdout = new_stdout

        try:
            from Compilers.test_for_if import test_for_if_sum
            test_for_if_sum()
        except Exception as e:
            self.error_text_edit.setPlainText(f"生成目标代码时出错: {str(e)}")
            sys.stdout = old_stdout
            return

        sys.stdout = old_stdout
        asm_code = new_stdout.getvalue()
        self.output_text_edit.setPlainText(asm_code)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
