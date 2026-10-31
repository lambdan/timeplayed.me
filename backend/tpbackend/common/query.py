def sort_by(query, column, order: str):
    """order the query by column, games/users/platforms without stats (nulls) always last"""
    if order == "desc":
        return query.order_by(column.desc(nulls="LAST"))
    return query.order_by(column.asc(nulls="LAST"))
