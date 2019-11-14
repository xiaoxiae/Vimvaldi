def center_coordinate(a: int, b: int) -> int:
    """Return the starting coordinate of an object of size a centered in an  object 
    of size b. Note that the function can return negative values (if a > b)."""
    return (a // 2) - (b // 2) - b % 2
