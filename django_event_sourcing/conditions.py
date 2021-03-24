import operator


class LogicMixin:
    def __and__(self, other):
        return BinaryConditionFactory(operator.and_, self, other)

    def __or__(self, other):
        return BinaryConditionFactory(operator.or_, self, other)

    def __xor__(self, other):
        return BinaryConditionFactory(operator.xor, self, other)

    def __invert__(self):
        return UnaryConditionFactory(operator.not_, self)


class UnaryMixin:
    def __init__(self, operator, operand):
        self.operator = operator
        self.operand = operand


class BinaryMixin:
    def __init__(self, operator, lhs, rhs):
        self.operator = operator
        self.lhs = lhs
        self.rhs = rhs


class MetaCondition(type, LogicMixin):
    pass


class BinaryConditionFactory(LogicMixin, BinaryMixin):
    def __call__(self):
        return BinaryCondition(self.operator, self.lhs, self.rhs)


class UnaryConditionFactory(LogicMixin, UnaryMixin):
    def __call__(self):
        return UnaryCondition(self.operator, self.operand)


class Condition(metaclass=MetaCondition):
    def has_condition(self, *args, **kwargs):
        raise NotImplementedError()


class BinaryCondition(Condition, BinaryMixin):
    def has_condition(self, *args, **kwargs):
        return self.operator(
            self.lhs().has_condition(*args, **kwargs),
            self.rhs().has_condition(*args, **kwargs),
        )


class UnaryCondition(Condition, UnaryMixin):
    def has_condition(self, *args, **kwargs):
        return self.operator(self.operand().has_condition(*args, **kwargs))
