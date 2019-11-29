from . import Router


def test_format_address_list_abc():
    router = Router("test")
    assert(router._format_address_list(["abc"]) == ["abc"])


def test_format_address_list_a_b_c():
    router = Router("test")
    assert(router._format_address_list(["a b c"]) == ["a+b+c"])
