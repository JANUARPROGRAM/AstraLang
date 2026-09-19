"""
AstraLang Lexer (v0.1, diperluas di v0.3)
============================================
Bertugas membaca source code AstraLang (.as) dan mengubahnya
menjadi deretan token yang akan diproses oleh Parser.

Desain:
- Setiap token punya: type, value, line, column (untuk error message yang jelas)
- Error karakter/sintaks dilempar sebagai LexerError, bukan exception generik Python,
  supaya pesan error konsisten dan mudah dibaca pemula.
"""

# ---------------------------------------------------------------------------
# Tipe-tipe token yang dikenali
# ---------------------------------------------------------------------------
TOKEN_TYPES = (
    "NUMBER", "STRING", "IDENT",
    "LET", "PRINT", "IF", "ELSE", "WHILE", "FUNCTION", "RETURN",
    "TRUE", "FALSE",
    "PLUS", "MINUS", "STAR", "SLASH", "PERCENT",
    "ASSIGN", "EQ", "NEQ", "LT", "GT", "LTE", "GTE",
    "AND", "OR", "NOT",
    "LPAREN", "RPAREN", "LBRACE", "RBRACE",
    "COMMA", "SEMI",
    "NEWLINE", "EOF",
    # -- Ditambahkan v0.3: Type System (List & null) --
    "LBRACKET", "RBRACKET", "NULL",
    # -- Ditambahkan v0.3 lanjutan: Custom Type --
    "TYPE", "DOT", "COLON",
    # -- Ditambahkan v0.5: for-loop --
    "FOR", "IN",
    # -- Ditambahkan v0.5: Web Route --
    "ROUTE",
)

KEYWORDS = {
    "let": "LET",
    "print": "PRINT",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "function": "FUNCTION",
    "return": "RETURN",
    "true": "TRUE",
    "false": "FALSE",
    "and": "AND",
    "or": "OR",
    "not": "NOT",
    # -- Ditambahkan v0.3: Type System --
    "null": "NULL",
    # -- Ditambahkan v0.3 lanjutan: Custom Type --
    "type": "TYPE",
    # -- Ditambahkan v0.5: for-loop --
    "for": "FOR",
    "in": "IN",
    # -- Ditambahkan v0.5: Web Route --
    # CATATAN: 'html' SENGAJA TIDAK dijadikan keyword reserved di sini,
    # karena contoh lama (web_demo.as, web_game.as, leaderboard_demo.as)
    # sudah memakai 'html' sebagai NAMA VARIABEL biasa (let html = "...").
    # Menjadikannya keyword reserved akan memecah kompatibilitas mundur.
    # Sebagai gantinya, blok 'html { ... }' dikenali di PARSER berdasarkan
    # posisi (IDENT bernilai "html" tepat di awal statement, diikuti '{'),
    # dengan pola yang sama seperti heuristik instance-literal custom type.
    "route": "ROUTE",
}


class LexerError(Exception):
    """Error yang muncul saat karakter/sintaks tidak dikenali di tahap lexing."""

    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"[Lexer Error] Baris {line}, Kolom {column}: {message}")


class Token:
    __slots__ = ("type", "value", "line", "column")

    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, L{self.line}:C{self.column})"


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.length = len(source)

    # -- helper dasar -------------------------------------------------
    def _peek(self, offset=0):
        idx = self.pos + offset
        if idx < self.length:
            return self.source[idx]
        return "\0"

    def _advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _match(self, expected):
        if self._peek() == expected:
            self._advance()
            return True
        return False

    # -- tokenizing -----------------------------------------------------
    def tokenize(self):
        tokens = []
        while self.pos < self.length:
            ch = self._peek()

            # Lewati spasi/tab (bukan newline, karena newline signifikan sbg pemisah statement)
            if ch in " \t\r":
                self._advance()
                continue

            # Komentar: # sampai akhir baris
            if ch == "#":
                while self._peek() != "\n" and self._peek() != "\0":
                    self._advance()
                continue

            # Newline -> token tersendiri (dipakai parser sbg pemisah statement opsional)
            if ch == "\n":
                start_line, start_col = self.line, self.column
                self._advance()
                tokens.append(Token("NEWLINE", "\\n", start_line, start_col))
                continue

            # String literal "..."
            if ch == '"':
                tokens.append(self._read_string())
                continue

            # Angka (integer & float sederhana)
            if ch.isdigit():
                tokens.append(self._read_number())
                continue

            # Identifier / keyword
            if ch.isalpha() or ch == "_":
                tokens.append(self._read_ident())
                continue

            # Operator & simbol
            token = self._read_symbol()
            tokens.append(token)

        tokens.append(Token("EOF", None, self.line, self.column))
        return tokens

    def _read_string(self):
        start_line, start_col = self.line, self.column
        self._advance()  # lewati pembuka "
        chars = []
        while True:
            ch = self._peek()
            if ch == "\0" or ch == "\n":
                raise LexerError(
                    "String tidak ditutup dengan tanda kutip (\")",
                    start_line, start_col,
                )
            if ch == '"':
                self._advance()
                break
            if ch == "\\":
                self._advance()
                esc = self._peek()
                escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                if esc in escapes:
                    chars.append(escapes[esc])
                    self._advance()
                else:
                    raise LexerError(
                        f"Escape character tidak dikenal: \\{esc}",
                        self.line, self.column,
                    )
                continue
            chars.append(ch)
            self._advance()
        return Token("STRING", "".join(chars), start_line, start_col)

    def _read_number(self):
        start_line, start_col = self.line, self.column
        chars = []
        is_float = False
        while self._peek().isdigit():
            chars.append(self._advance())
        if self._peek() == "." and self._peek(1).isdigit():
            is_float = True
            chars.append(self._advance())  # titik
            while self._peek().isdigit():
                chars.append(self._advance())
        text = "".join(chars)
        value = float(text) if is_float else int(text)
        return Token("NUMBER", value, start_line, start_col)

    def _read_ident(self):
        start_line, start_col = self.line, self.column
        chars = []
        while self._peek().isalnum() or self._peek() == "_":
            chars.append(self._advance())
        text = "".join(chars)
        token_type = KEYWORDS.get(text, "IDENT")
        return Token(token_type, text, start_line, start_col)

    def _read_symbol(self):
        start_line, start_col = self.line, self.column
        ch = self._advance()

        two_char = ch + self._peek()
        two_char_map = {
            "==": "EQ", "!=": "NEQ",
            "<=": "LTE", ">=": "GTE",
        }
        if two_char in two_char_map:
            self._advance()
            return Token(two_char_map[two_char], two_char, start_line, start_col)

        single_map = {
            "+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH", "%": "PERCENT",
            "=": "ASSIGN", "<": "LT", ">": "GT",
            "(": "LPAREN", ")": "RPAREN",
            "{": "LBRACE", "}": "RBRACE",
            ",": "COMMA", ";": "SEMI",
            "[": "LBRACKET", "]": "RBRACKET",  # v0.3: List literal & indexing
            ".": "DOT", ":": "COLON",           # v0.3: Custom Type (field access & literal)
        }
        if ch in single_map:
            return Token(single_map[ch], ch, start_line, start_col)

        raise LexerError(f"Karakter tidak dikenal: '{ch}'", start_line, start_col)


def tokenize_source(source: str):
    """Fungsi bantu singkat untuk dipakai modul lain."""
    return Lexer(source).tokenize()
