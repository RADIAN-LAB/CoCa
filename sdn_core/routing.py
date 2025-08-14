routing_table = {
    0: {
        "default": 1,
    },
    1: {
        0: 0,
        2: 2,
        "default": 3,
    },
    2: {
        "default": 1,
    },
    3: {
        4: 4,
        "default": 1,
    },
    4: {
        "default": 3,
    },
}


def route(src: int, dst: int) -> int:
    """Return next-hop from src toward dst using the predefined routing table."""
    if dst in routing_table[src]:
        return routing_table[src][dst]
    return routing_table[src]["default"]


def calculate_num_hob(src: int, dst: int) -> int:
    """Calculate hop count between src and dst."""
    src -= 1
    dst -= 1
    current = src
    num_hob = 0
    while current != dst:
        num_hob += 1
        current = route(current, dst)
    return num_hob
