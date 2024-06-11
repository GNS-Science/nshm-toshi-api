from graphene.types.scalars import Scalar

# from graphql.language.ast import IntValue
from graphql.language import ast


class BigInt(Scalar):
    """
    BigInt is an extension of the regular Int field
        that supports Integers bigger than a signed
        32-bit integer.
    """

    @staticmethod
    def coerce_int(value):
        try:
            num = int(value)
        except ValueError:
            try:
                num = int(float(value))
            except ValueError:
                return None
        return num

    serialize = coerce_int
    parse_value = coerce_int

    @staticmethod
    def parse_literal(ast_node):
        if isinstance(ast_node, ast.IntValue): #Node):
            return int(ast_node.value)
