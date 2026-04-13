import quantum_properties as qp


def test_public_symbols_are_exported():
    for symbol in qp.__all__:
        assert hasattr(qp, symbol)


def test_package_metadata_present():
    assert isinstance(qp.__version__, str)
    assert isinstance(qp.__author__, str)
