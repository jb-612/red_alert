import codecs


def strip_bom(text: str) -> str:
    """Strip UTF-8 BOM from response text.

    OREF API responses include a UTF-8 BOM (EF BB BF) that must
    be removed before JSON or CSV parsing.
    """
    return codecs.decode(text.encode(), "utf-8-sig")
