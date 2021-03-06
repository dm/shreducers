import string

from shreducers import tokenizers
from shreducers.grammar import Grammar
from shreducers.tokenizers import EOF, BOF


class BetterArithmeticsG(Grammar):
    class t:
        IDENT = None
        PLUS_MINUS = '+-'
        MULTIPLY_DIVIDE = '*/'
        PARENS_OPEN = '('
        PARENS_CLOSE = ')'
        PRODUCT = ()

    @classmethod
    def get_default_tokenizer(cls):
        return tokenizers.create_shlex_tokenizer(
            with_bof=True,
            with_eof=True,
            wordchars=string.digits + '.',
        )

    @classmethod
    def get_rules(cls):
        return [
            ([cls.t.PRODUCT, cls.t.MULTIPLY_DIVIDE, cls.t.PRODUCT], cls.product_expr),
            ([cls.t.PRODUCT, cls.t.MULTIPLY_DIVIDE, cls.t.IDENT], cls.product_expr),
            ([cls.t.IDENT, cls.t.MULTIPLY_DIVIDE, cls.t.IDENT], cls.product_expr),
            ([cls.t.IDENT, cls.t.MULTIPLY_DIVIDE, cls.t.PRODUCT], cls.product_expr),

            # Parentheses.
            # Opening parentheses are pretty much like BOF - beginning of sentence -
            # and closing parentheses are like EOF - end of sentence.
            # So all rules with parentheses also apply for BOF and EOF.

            ([cls.t.PARENS_OPEN, cls.t.PRODUCT, cls.t.PARENS_CLOSE], cls.remove_parens),
            ([BOF, cls.t.PRODUCT, EOF], cls.remove_parens),  # redundant for our parser, added just for completeness

            # Addition and subtraction is safe when we have seen the ending of "sentence"
            ([cls.t.IDENT, EOF], cls.product_at_eof),
            ([cls.t.IDENT, cls.t.PARENS_CLOSE], cls.product_at_eof),

            ([cls.t.IDENT, cls.t.PLUS_MINUS, cls.t.PRODUCT, EOF], cls.product_expr_at_eof),
            ([cls.t.IDENT, cls.t.PLUS_MINUS, cls.t.PRODUCT, cls.t.PARENS_CLOSE], cls.product_expr_at_eof),

            ([cls.t.PRODUCT, cls.t.PLUS_MINUS, cls.t.PRODUCT, EOF], cls.product_expr_at_eof),
            ([cls.t.PRODUCT, cls.t.PLUS_MINUS, cls.t.PRODUCT, cls.t.PARENS_CLOSE], cls.product_expr_at_eof),

            # Negation.
            # Opposite of addition and subtraction -- it is only safe in the beginning
            ([BOF, cls.t.PLUS_MINUS, cls.t.IDENT], cls.negation_at_bof),
            ([cls.t.PARENS_OPEN, cls.t.PLUS_MINUS, cls.t.IDENT], cls.negation_at_bof),

            ([BOF, cls.t.PLUS_MINUS, cls.t.PRODUCT], cls.negation_at_bof),
            ([cls.t.PARENS_OPEN, cls.t.PLUS_MINUS, cls.t.PRODUCT], cls.negation_at_bof),
        ]

    @classmethod
    def product_expr(cls, types, (a, op, b)):
        return [cls.t.PRODUCT], [(op, a, b)]

    @classmethod
    def product_at_eof(cls, types, (a, eof)):
        return [cls.t.PRODUCT, types[1]], [a, eof]

    @classmethod
    def product_expr_at_eof(cls, types, (a, op, b, eof)):
        return [cls.t.PRODUCT, types[3]], [(op, a, b), eof]

    @classmethod
    def remove_parens(cls, types, (p1, x, p2)):
        return [types[1]], [x]

    @classmethod
    def negation_at_bof(cls, (bof_type, op_type, a_type), (bof, op, a)):
        if a_type == cls.t.IDENT:
            sign = op if op == '-' else ''
            return [bof_type, a_type], [bof, '{}{}'.format(sign, a)]
        else:
            return [bof_type, cls.t.PRODUCT], [bof, (op, '0', a)]
