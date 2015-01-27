import re
from dataviva import db
from sqlalchemy import func, desc

SHOW='show'
SHOW2='.show.'
ALL='all'
LEN='_len'
OR='_'

def parse_value(column, value):
    if OR in str(value):
        return column.in_(value.split(OR))
    return column == value

def query_table(table, columns=[], filters=[], groups=[], limit=0, order=None, sort="desc", offset=None, serialize=True, having=[]):
    headers = [c.key for c in columns] or table.__table__.columns.keys()
    columns = columns or table.__table__.columns.values()
    if isinstance(order, (str, unicode)) and hasattr(table, order):
        filters.append(getattr(table, order) != None)
    # raise Exception(having)
    query = table.query \
        .with_entities(*columns) \
        .filter(*filters) \
        .group_by(*groups)
    if having:
        query = query.having(*having)
    if order:
        if sort != "asc":
            order = desc(order)
        query = query.order_by(order)
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    # raise Exception(query)
    if serialize:
        data = {
            "headers": headers,
            "data": [ list(row) for row in query]
        }
    else:
        column_names = [c.key for c in columns]
        data = [dict(zip(column_names, vals)) for vals in query.all()]
    return data

def _show_filters_to_add(column, value, table, colname):
    to_add = []
    pattern = '(\w+)?\.?show\.?(\w+)?'
    matches = re.match(pattern, value)
    if matches: 
        prefix, length = matches.groups()
        if prefix:
            to_add.append(column.startswith(prefix))
        if length and hasattr(table, colname + LEN):
            lencol = getattr(table, colname + LEN)
            to_add.append(lencol == length)
        # else, the assumption is that IFF a column doesn't have a length col associated with it
        # then it isn't nested and therefore an additional filter is not needed.
    return to_add

def build_filters_and_groups(table, kwargs, exclude=None):
    filters = []
    groups = []
    show_column = None
    
    for colname in kwargs:
        value = str(kwargs[colname])
        if colname == "month" and value == ALL:
            column = getattr(table, colname)
            filters.append(column != 0)
            groups.append(column)
        elif value != ALL: 
            # -- if the value is not "ALL", then we need to group by this column
            column = getattr(table, colname)
            groups.append(column)
            
            if not SHOW in value: # -- if the value does not include a SHOW operation, then just filter based on value
                filters.append(parse_value(column, value))
            else:
                show_column = column # -- set this as the show column
                filters += _show_filters_to_add(column, value, table, colname)

        elif colname == "year":
            column = getattr(table, colname)
            groups.append(column)

    if len(table.__name__) == len(groups):
        groups = []

    if exclude:
        if type(exclude) in [str, unicode]:
            if "%" in exclude:
                filters.append(~show_column.like(exclude))
            else:
                filters.append(show_column != exclude)
        else:
            filters.append(~show_column.in_(exclude))
    return filters, groups, show_column

def convert_filters(table, kwargs, remove=None):
    fake_kwargs = {k:v for k,v in kwargs.items() if not k in remove}
    return build_filters_and_groups(table, fake_kwargs)