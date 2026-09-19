"""
AstraLang Parser (v0.1)
========================
Mengubah deretan Token dari Lexer menjadi Abstract Syntax Tree (AST).
Menggunakan teknik recursive-descent parsing dengan precedence climbing
untuk ekspresi matematika/logika.

Semua node AST didefinisikan sebagai class kecil (bukan dict) supaya
mudah dibaca dan dikembangkan oleh interpreter.
"""

from lexer import Lexer


class ParserError(Exception):
    """
    Error struktur kode di tahap parsing.
    v0.3: menambahkan field `hint` opsional berisi saran perbaikan konkret,
    supaya error message tidak cuma bilang "salah" tapi juga "coba begini".
    """

    def __init__(self, message, line, column, hint=None):
        self.message = message
        self.line = line
        self.column = column
        self.hint = hint
        text = f"[Parser Error] Baris {line}, Kolom {column}: {message}"
        if hint:
            text += f"\n  Saran: {hint}"
        super().__init__(text)


# ---------------------------------------------------------------------------
# AST Node definitions
# ---------------------------------------------------------------------------
class Node:
    """Base class, hanya untuk penanda tipe."""
    pass


class Program(Node):
    def __init__(self, statements):
        self.statements = statements


class LetStatement(Node):
    def __init__(self, name, value, line):
        self.name = name
        self.value = value
        self.line = line


class PrintStatement(Node):
    def __init__(self, value, line):
        self.value = value
        self.line = line


class IfStatement(Node):
    def __init__(self, condition, then_branch, else_branch, line):
        self.condition = condition
        self.then_branch = then_branch    # list of statements
        self.else_branch = else_branch    # list of statements or None
        self.line = line


class WhileStatement(Node):
    def __init__(self, condition, body, line):
        self.condition = condition
        self.body = body
        self.line = line


class FunctionDecl(Node):
    def __init__(self, name, params, body, line):
        self.name = name
        self.params = params
        self.body = body
        self.line = line


class ReturnStatement(Node):
    def __init__(self, value, line):
        self.value = value
        self.line = line


class ExpressionStatement(Node):
    def __init__(self, expr, line):
        self.expr = expr
        self.line = line


class AssignExpr(Node):
    def __init__(self, name, value, line):
        self.name = name
        self.value = value
        self.line = line


class BinaryExpr(Node):
    def __init__(self, left, op, right, line):
        self.left = left
        self.op = op
        self.right = right
        self.line = line


class UnaryExpr(Node):
    def __init__(self, op, operand, line):
        self.op = op
        self.operand = operand
        self.line = line


class LiteralExpr(Node):
    def __init__(self, value, line):
        self.value = value
        self.line = line


class VarExpr(Node):
    def __init__(self, name, line):
        self.name = name
        self.line = line


class CallExpr(Node):
    def __init__(self, callee, args, line):
        self.callee = callee
        self.args = args
        self.line = line


# -- Ditambahkan v0.3: Type System (List) ---------------------------------
class ListExpr(Node):
    """Literal list, mis. [1, 2, 3]"""
    def __init__(self, elements, line):
        self.elements = elements  # list of Node
        self.line = line


class IndexExpr(Node):
    """Akses elemen list dengan index, mis. daftar[0]"""
    def __init__(self, collection, index, line):
        self.collection = collection  # Node (biasanya VarExpr atau ListExpr)
        self.index = index            # Node (ekspresi index)
        self.line = line


class IndexAssignExpr(Node):
    """Assignment ke elemen list, mis. daftar[0] = 99"""
    def __init__(self, collection, index, value, line):
        self.collection = collection
        self.index = index
        self.value = value
        self.line = line


# -- Ditambahkan v0.3 lanjutan: Custom Type -------------------------------
class TypeDecl(Node):
    """Deklarasi custom type, mis. type Point { x y }"""
    def __init__(self, name, fields, line):
        self.name = name      # nama type, mis. 'Point'
        self.fields = fields  # list of field name (string)
        self.line = line


class InstanceExpr(Node):
    """Literal instance dari custom type, mis. Point { x: 10, y: 20 }"""
    def __init__(self, type_name, field_values, line):
        self.type_name = type_name        # nama type, mis. 'Point'
        self.field_values = field_values  # list of (field_name, Node)
        self.line = line


class FieldAccessExpr(Node):
    """Akses field instance, mis. p.x"""
    def __init__(self, obj, field_name, line):
        self.obj = obj              # Node (biasanya VarExpr)
        self.field_name = field_name
        self.line = line


class FieldAssignExpr(Node):
    """Assignment ke field instance, mis. p.x = 99"""
    def __init__(self, obj, field_name, value, line):
        self.obj = obj
        self.field_name = field_name
        self.value = value
        self.line = line


# -- Ditambahkan v0.5: for-loop ---------------------------------------------
class ForStatement(Node):
    """for item in daftar { ... } -- iterasi setiap elemen List/string"""
    def __init__(self, var_name, iterable, body, line):
        self.var_name = var_name
        self.iterable = iterable
        self.body = body
        self.line = line


# -- Ditambahkan v0.5: Web Route & HTML block -------------------------------
class RouteStatement(Node):
    """route "/path" { ... return "isi respons" } -- daftarkan route HTTP"""
    def __init__(self, path_expr, body, line):
        self.path_expr = path_expr  # Node yang menghasilkan string path
        self.body = body            # list of statement (biasanya diakhiri return)
        self.line = line


class HtmlBlockExpr(Node):
    """
    html { title "Judul" text "isi" } -- gula sintaks untuk menyusun HTML
    sederhana tanpa perlu menulis tag manual. Dikenali berdasarkan posisi
    (IDENT bernilai 'html' di awal statement diikuti '{'), BUKAN keyword
    reserved, supaya 'let html = "..."' (dipakai di contoh v0.4) tetap sah.
    """
    def __init__(self, entries, line):
        self.entries = entries  # list of (kind, Node) -- kind: 'title'/'text'/'heading'
        self.line = line


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        # v0.3 lanjutan: saat True, `Nama { ... }` di posisi ekspresi primer
        # boleh diartikan sebagai instance literal. Dimatikan sementara waktu
        # parsing kondisi if/while, supaya `if Aktif { ... }` (Aktif = variabel
        # boolean berhuruf besar) tidak salah diartikan sebagai instance
        # literal yang menelan blok if itu sendiri.
        self._allow_instance_literal = True

    # -- helper dasar ---------------------------------------------------
    def _peek(self, offset=0):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]  # EOF

    def _current(self):
        return self._peek()

    def _advance(self):
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def _check(self, type_):
        return self._current().type == type_

    def _match(self, *types):
        if self._current().type in types:
            return self._advance()
        return None

    def _expect(self, type_, message, hint=None):
        if self._check(type_):
            return self._advance()
        tok = self._current()
        raise ParserError(message, tok.line, tok.column, hint=hint)

    def _skip_newlines(self):
        while self._check("NEWLINE") or self._check("SEMI"):
            self._advance()

    # -- entry point ------------------------------------------------------
    def parse(self):
        statements = []
        self._skip_newlines()
        while not self._check("EOF"):
            statements.append(self._statement())
            self._skip_newlines()
        return Program(statements)

    # -- statements ---------------------------------------------------------
    def _statement(self):
        tok = self._current()

        if tok.type == "LET":
            return self._let_statement()
        if tok.type == "PRINT":
            return self._print_statement()
        if tok.type == "IF":
            return self._if_statement()
        if tok.type == "WHILE":
            return self._while_statement()
        if tok.type == "FOR":
            return self._for_statement()
        if tok.type == "FUNCTION":
            return self._function_decl()
        if tok.type == "RETURN":
            return self._return_statement()
        if tok.type == "TYPE":
            return self._type_decl()
        if tok.type == "ROUTE":
            return self._route_statement()

        return self._expression_statement()

    def _let_statement(self):
        line = self._current().line
        self._advance()  # 'let'
        name_tok = self._expect("IDENT", "Diharapkan nama variabel setelah 'let'")
        self._expect("ASSIGN", f"Diharapkan '=' setelah nama variabel '{name_tok.value}'")
        value = self._expression()
        return LetStatement(name_tok.value, value, line)

    def _print_statement(self):
        line = self._current().line
        self._advance()  # 'print'
        value = self._expression()
        return PrintStatement(value, line)

    def _block(self):
        """Mem-parse blok { ... } dan mengembalikan list statement."""
        self._expect("LBRACE", "Diharapkan '{' untuk memulai blok")
        self._skip_newlines()
        statements = []
        while not self._check("RBRACE") and not self._check("EOF"):
            statements.append(self._statement())
            self._skip_newlines()
        self._expect("RBRACE", "Diharapkan '}' untuk menutup blok")
        return statements

    def _if_statement(self):
        line = self._current().line
        self._advance()  # 'if'
        self._allow_instance_literal = False
        condition = self._expression()
        self._allow_instance_literal = True
        then_branch = self._block()
        else_branch = None
        self._skip_newlines_peek_else()
        if self._check("ELSE"):
            self._advance()
            if self._check("IF"):
                else_branch = [self._if_statement()]
            else:
                else_branch = self._block()
        return IfStatement(condition, then_branch, else_branch, line)

    def _skip_newlines_peek_else(self):
        # Izinkan newline sebelum 'else' tanpa memakannya kalau bukan else
        save = self.pos
        while self._check("NEWLINE"):
            self._advance()
        if not self._check("ELSE"):
            self.pos = save

    def _while_statement(self):
        line = self._current().line
        self._advance()  # 'while'
        self._allow_instance_literal = False
        condition = self._expression()
        self._allow_instance_literal = True
        body = self._block()
        return WhileStatement(condition, body, line)

    # -- Ditambahkan v0.5: for-loop -----------------------------------------
    def _for_statement(self):
        line = self._current().line
        self._advance()  # 'for'
        var_tok = self._expect(
            "IDENT", "Diharapkan nama variabel setelah 'for'",
            hint="Contoh: for item in daftar { ... }",
        )
        self._expect(
            "IN", f"Diharapkan 'in' setelah nama variabel '{var_tok.value}'",
            hint=f"Contoh: for {var_tok.value} in daftar {{ ... }}",
        )
        self._allow_instance_literal = False
        iterable = self._expression()
        self._allow_instance_literal = True
        body = self._block()
        return ForStatement(var_tok.value, iterable, body, line)

    # -- Ditambahkan v0.5: Web Route -----------------------------------------
    def _route_statement(self):
        line = self._current().line
        self._advance()  # 'route'
        path_expr = self._expression()
        body = self._block()
        return RouteStatement(path_expr, body, line)

    def _function_decl(self):
        line = self._current().line
        self._advance()  # 'function'
        name_tok = self._expect("IDENT", "Diharapkan nama fungsi setelah 'function'")
        self._expect("LPAREN", f"Diharapkan '(' setelah nama fungsi '{name_tok.value}'")
        params = []
        if not self._check("RPAREN"):
            params.append(self._expect("IDENT", "Diharapkan nama parameter").value)
            while self._match("COMMA"):
                params.append(self._expect("IDENT", "Diharapkan nama parameter").value)
        self._expect("RPAREN", "Diharapkan ')' setelah daftar parameter")
        body = self._block()
        return FunctionDecl(name_tok.value, params, body, line)

    def _return_statement(self):
        line = self._current().line
        self._advance()  # 'return'
        value = None
        if not self._check("NEWLINE") and not self._check("RBRACE") and not self._check("EOF"):
            value = self._expression()
        return ReturnStatement(value, line)

    def _expression_statement(self):
        line = self._current().line
        expr = self._expression()
        return ExpressionStatement(expr, line)

    # -- Ditambahkan v0.3 lanjutan: Custom Type -----------------------------
    def _type_decl(self):
        line = self._current().line
        self._advance()  # 'type'
        name_tok = self._expect("IDENT", "Diharapkan nama type setelah 'type'")
        self._expect(
            "LBRACE", f"Diharapkan '{{' setelah nama type '{name_tok.value}'",
            hint=f"Contoh: type {name_tok.value} {{ x y }}",
        )
        self._skip_newlines()
        fields = []
        while not self._check("RBRACE") and not self._check("EOF"):
            field_tok = self._expect(
                "IDENT", "Diharapkan nama field di dalam deklarasi type",
                hint="Setiap baris di dalam 'type { }' berisi satu nama field, mis. x",
            )
            fields.append(field_tok.value)
            self._skip_newlines()
        self._expect("RBRACE", f"Diharapkan '}}' untuk menutup deklarasi type '{name_tok.value}'")
        if not fields:
            raise ParserError(
                f"Type '{name_tok.value}' tidak punya field sama sekali",
                line, self._current().column,
                hint="Tambahkan minimal satu field, mis. type Point { x y }",
            )
        return TypeDecl(name_tok.value, fields, line)

    # -- expressions (precedence climbing) ---------------------------------
    def _expression(self):
        return self._assignment()

    def _assignment(self):
        expr = self._logic_or()
        if self._check("ASSIGN"):
            line = self._current().line
            self._advance()
            value = self._assignment()
            if isinstance(expr, VarExpr):
                return AssignExpr(expr.name, value, line)
            if isinstance(expr, IndexExpr):
                # v0.3: daftar[0] = 99
                return IndexAssignExpr(expr.collection, expr.index, value, line)
            if isinstance(expr, FieldAccessExpr):
                # v0.3 lanjutan: p.x = 99
                return FieldAssignExpr(expr.obj, expr.field_name, value, line)
            raise ParserError(
                "Target assignment tidak valid",
                line, self._current().column,
                hint="Assignment hanya bisa ke variabel (x = 5), elemen list (daftar[0] = 5), atau field instance (p.x = 5)",
            )
        return expr

    def _logic_or(self):
        expr = self._logic_and()
        while self._check("OR"):
            op = self._advance()
            right = self._logic_and()
            expr = BinaryExpr(expr, op.value, right, op.line)
        return expr

    def _logic_and(self):
        expr = self._equality()
        while self._check("AND"):
            op = self._advance()
            right = self._equality()
            expr = BinaryExpr(expr, op.value, right, op.line)
        return expr

    def _equality(self):
        expr = self._comparison()
        while self._check("EQ") or self._check("NEQ"):
            op = self._advance()
            right = self._comparison()
            expr = BinaryExpr(expr, op.value, right, op.line)
        return expr

    def _comparison(self):
        expr = self._term()
        while self._current().type in ("LT", "GT", "LTE", "GTE"):
            op = self._advance()
            right = self._term()
            expr = BinaryExpr(expr, op.value, right, op.line)
        return expr

    def _term(self):
        expr = self._factor()
        while self._current().type in ("PLUS", "MINUS"):
            op = self._advance()
            # v0.4: izinkan baris baru setelah operator +/- supaya ekspresi
            # panjang (mis. penggabungan string HTML) bisa ditulis multi-baris:
            #   let html = "<a>" +
            #       "<b>" +
            #       "<c>"
            self._skip_newlines()
            right = self._factor()
            expr = BinaryExpr(expr, op.value, right, op.line)
        return expr

    def _factor(self):
        expr = self._unary()
        while self._current().type in ("STAR", "SLASH", "PERCENT"):
            op = self._advance()
            right = self._unary()
            expr = BinaryExpr(expr, op.value, right, op.line)
        return expr

    def _unary(self):
        if self._current().type in ("MINUS", "NOT"):
            op = self._advance()
            operand = self._unary()
            return UnaryExpr(op.value, operand, op.line)
        return self._call()

    def _call(self):
        expr = self._primary()
        while True:
            if self._check("LPAREN"):
                line = self._current().line
                self._advance()
                args = []
                if not self._check("RPAREN"):
                    args.append(self._expression())
                    while self._match("COMMA"):
                        args.append(self._expression())
                self._expect("RPAREN", "Diharapkan ')' setelah argumen fungsi")
                expr = CallExpr(expr, args, line)
            elif self._check("LBRACKET"):
                # v0.3: indexing, mis. daftar[0], matrix[0][1]
                line = self._current().line
                self._advance()  # '['
                index_expr = self._expression()
                self._expect(
                    "RBRACKET",
                    "Diharapkan ']' untuk menutup indexing",
                )
                expr = IndexExpr(expr, index_expr, line)
            elif self._check("DOT"):
                # v0.3 lanjutan: field access, mis. p.x
                line = self._current().line
                self._advance()  # '.'
                field_tok = self._expect(
                    "IDENT", "Diharapkan nama field setelah '.'",
                    hint="Contoh: p.x untuk mengakses field 'x' pada instance p",
                )
                expr = FieldAccessExpr(expr, field_tok.value, line)
            elif self._check("LBRACE") and self._allow_instance_literal \
                    and isinstance(expr, VarExpr) and expr.name[:1].isupper():
                # v0.3 lanjutan: instance literal, mis. Point { x: 10, y: 20 }
                # Hanya dipicu kalau nama diawali huruf besar (konvensi nama Type)
                # supaya tidak bentrok dengan blok lain yang kebetulan muncul
                # setelah sebuah identifier di posisi ekspresi.
                expr = self._instance_literal(expr.name, expr.line)
            elif self._check("LBRACE") and self._allow_instance_literal \
                    and isinstance(expr, VarExpr) and expr.name == "html":
                # v0.5: html { title "..." text "..." } sebagai EKSPRESI,
                # supaya bisa dipakai mis. 'return html { ... }' di dalam
                # route, atau 'let h = html { ... }'. Dideteksi berdasarkan
                # posisi (bukan keyword reserved) supaya 'let html = "..."'
                # (dipakai contoh v0.4) tetap sah -- lihat catatan di lexer.py.
                expr = self._html_block(expr.line)
            else:
                break
        return expr

    def _html_block(self, line):
        self._advance()  # '{'
        self._skip_newlines()
        entries = []
        while not self._check("RBRACE") and not self._check("EOF"):
            kind_tok = self._current()
            if kind_tok.type != "IDENT" or kind_tok.value not in ("title", "text", "heading"):
                raise ParserError(
                    f"Di dalam blok 'html {{ }}' hanya boleh berisi title/heading/text, ketemu '{kind_tok.value}'",
                    kind_tok.line, kind_tok.column,
                    hint='Contoh: html { title "Judul" heading "Halo" text "isi" }',
                )
            self._advance()
            value_expr = self._expression()
            entries.append((kind_tok.value, value_expr))
            self._skip_newlines()
        self._expect(
            "RBRACE", "Diharapkan '}' untuk menutup blok html",
            hint='Contoh: html { title "Judul" text "isi" }',
        )
        return HtmlBlockExpr(entries, line)

    def _instance_literal(self, type_name, line):
        self._advance()  # '{'
        self._skip_newlines()
        field_values = []
        if not self._check("RBRACE"):
            field_values.append(self._instance_field())
            while self._match("COMMA"):
                self._skip_newlines()
                if self._check("RBRACE"):
                    break
                field_values.append(self._instance_field())
            self._skip_newlines()
        self._expect(
            "RBRACE", f"Diharapkan '}}' untuk menutup instance '{type_name}'",
            hint=f"Contoh: {type_name} {{ field: nilai }}",
        )
        return InstanceExpr(type_name, field_values, line)

    def _instance_field(self):
        self._skip_newlines()
        field_tok = self._expect(
            "IDENT", "Diharapkan nama field di dalam instance literal",
            hint="Contoh: x: 10",
        )
        self._expect(
            "COLON", f"Diharapkan ':' setelah nama field '{field_tok.value}'",
            hint=f"Contoh: {field_tok.value}: nilai",
        )
        value = self._expression()
        return (field_tok.value, value)

    def _primary(self):
        tok = self._current()

        if tok.type == "NUMBER":
            self._advance()
            return LiteralExpr(tok.value, tok.line)
        if tok.type == "STRING":
            self._advance()
            return LiteralExpr(tok.value, tok.line)
        if tok.type == "TRUE":
            self._advance()
            return LiteralExpr(True, tok.line)
        if tok.type == "FALSE":
            self._advance()
            return LiteralExpr(False, tok.line)
        if tok.type == "NULL":
            # v0.3: null sebagai literal eksplisit
            self._advance()
            return LiteralExpr(None, tok.line)
        if tok.type == "IDENT":
            self._advance()
            return VarExpr(tok.value, tok.line)
        if tok.type == "LPAREN":
            self._advance()
            expr = self._expression()
            self._expect("RPAREN", "Diharapkan ')' untuk menutup ekspresi")
            return expr
        if tok.type == "LBRACKET":
            # v0.3: literal list, mis. [1, 2, 3]
            # v0.3 lanjutan: mendukung penulisan multi-baris, mis.
            #   [
            #       1,
            #       2,
            #   ]
            self._advance()
            self._skip_newlines()
            elements = []
            if not self._check("RBRACKET"):
                elements.append(self._expression())
                self._skip_newlines()
                while self._match("COMMA"):
                    self._skip_newlines()
                    # Izinkan trailing comma, mis. [1, 2, 3,]
                    if self._check("RBRACKET"):
                        break
                    elements.append(self._expression())
                    self._skip_newlines()
            self._expect(
                "RBRACKET",
                "Diharapkan ']' untuk menutup literal list",
                hint="Pastikan setiap '[' punya pasangan ']', mis. [1, 2, 3]",
            )
            return ListExpr(elements, tok.line)

        raise ParserError(
            f"Token tidak terduga: {tok.type} ({tok.value!r})",
            tok.line, tok.column,
            hint=self._suggest_hint_for_unexpected_token(tok),
        )

    def _suggest_hint_for_unexpected_token(self, tok):
        """v0.3: memberi saran perbaikan kontekstual untuk error token tak terduga."""
        if tok.type == "RBRACE":
            return "Ada '}' berlebih, atau blok sebelumnya belum dibuka dengan '{'"
        if tok.type == "RPAREN":
            return "Ada ')' berlebih, atau kurung buka '(' belum ditulis"
        if tok.type == "RBRACKET":
            return "Ada ']' berlebih, atau list belum dibuka dengan '['"
        if tok.type == "EOF":
            return "Kode berakhir tiba-tiba, kemungkinan ada blok/kurung yang belum ditutup"
        if tok.type == "ASSIGN":
            return "Tanda '=' di sini tidak terduga, cek apakah ada nilai yang hilang sebelumnya"
        return None


def parse_source(source: str):
    """Fungsi bantu: source code string -> AST Program."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()
