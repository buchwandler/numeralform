"""Exceptions raised by numeralform."""


class NumeralFormError(ValueError):
    """Base class for invalid numeralform requests."""


class InvalidValueError(NumeralFormError):
    """A supplied semantic numeric value is invalid."""


class InvalidRequestError(NumeralFormError):
    """A numeral request is invalid."""


class UnsupportedLocaleError(NumeralFormError):
    """The requested locale is not registered."""


class UnsupportedFormError(NumeralFormError):
    """The requested form is not supported by a locale."""


class UnsupportedMorphologyError(NumeralFormError):
    """A locale cannot realize the requested morphology."""


class UnsupportedStyleError(NumeralFormError):
    """A locale cannot realize the requested output style."""
