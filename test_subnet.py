import pytest
from subnet import calculate, plan, parse_requirements


@pytest.mark.parametrize("ip,p,net", [
    ("192.168.10.25", 24, "192.168.10.0"), ("10.0.0.130", 25, "10.0.0.128"),
    ("172.16.5.70", 26, "172.16.5.64"), ("192.168.1.5", 30, "192.168.1.4")])
def test_network(ip, p, net):
    assert calculate(ip, p)["network"] == net


def test_details():
    r = calculate("192.168.10.25", 24)
    assert (r["mask"], r["broadcast"], r["first"], r["last"], r["total"], r["usable"]) == \
        ("255.255.255.0", "192.168.10.255", "192.168.10.1", "192.168.10.254", 256, 254)


def test_special_prefixes():
    assert calculate("1.2.3.4", 31)["usable"] == 2
    assert calculate("1.2.3.4", 32)["usable"] == 1


@pytest.mark.parametrize("ip,p", [("300.1.1.1", 24), ("abc", 24), ("1.1.1.1", 33), ("1.1.1.1", "x")])
def test_invalid(ip, p):
    with pytest.raises(ValueError):
        calculate(ip, p)


def test_vlsm_report_example():
    rows, free = plan("192.168.10.0/24", parse_requirements("IT,100\nHR,50\nFinance,25"))
    assert [(r["network"], r["prefix"]) for r in rows] == \
        [("192.168.10.0", 25), ("192.168.10.128", 26), ("192.168.10.192", 27)]
    assert free == 32


def test_insufficient_space():
    with pytest.raises(ValueError):
        plan("192.168.10.0/24", [("A", 200), ("B", 100)])
