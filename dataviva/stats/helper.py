import pickle

from dataviva.utils import table_helper, query_helper
from dataviva.stats.util import compute_allowed

from dataviva.utils.cached_query import cached_query
from dataviva.stats.cache import object_cache

from dataviva import db

import dataviva.ei.models as ei
import dataviva.rais.models as rais
import dataviva.hedu.models as hedu
import dataviva.attrs.models as attrs
from dataviva.stats.util import get_profiles

from sqlalchemy import func
from sqlalchemy import desc, asc

from dataviva.stats.cache import profile_cache_serialized
from dataviva.stats.util import gen_table_list

from dataviva import __latest_year__

# TODO: Add SECEX once API is updated
possible_tables = {
    "bra_id_r" : [ei.Ymr],
    "bra_id_s" : [ei.Yms],
    "bra_id" : [rais.Yb_rais, hedu.Yb_hedu, hedu.Ybu, attrs.Bra],
    "cnae_id" : [rais.Yi],
    "cbo_id" : [rais.Yo],
    "university_id" : [hedu.Yu, hedu.Ybu],
    "course_hedu_id" : [hedu.Yc_hedu],
}

allowed_when_not = compute_allowed(gen_table_list(possible_tables))

max_depth = {
    "bra_id": 9,
    "course_hedu_id": 6,
    "cnae_id": 6,
    "cbo_id": 4,
    "hs_id": 6,
    "wld_id": 5,
}

no_length_column = { attrs.Bra: 9 }
CAROSEL_NS = "carosel:"

filters_map = {
    rais.Yb_rais : [rais.Yb_rais.year == __latest_year__['rais']],
    rais.Yi : [rais.Yi.year == __latest_year__['rais']],
    rais.Yo : [rais.Yo.year == __latest_year__['rais'], rais.Yo.cbo_id != u'xxxx'],
    hedu.Ybu : [hedu.Ybu.year == __latest_year__['hedu'], hedu.Ybu.bra_id != '0xx000007'],
    hedu.Yu : [hedu.Yu.year == __latest_year__['hedu']],
    hedu.Yb_hedu : [hedu.Yb_hedu.year == __latest_year__['hedu'], hedu.Yb_hedu.bra_id != '0xx000007'],
    hedu.Yc_hedu : [hedu.Yc_hedu.year == __latest_year__['hedu']],
}

def carousel_maker(title, typestr, metric, shows, limit=10, offset=0, sort="desc"):
    result = stats_list(metric, shows, limit=limit, offset=offset, sort=sort)
    posters = get_profiles(result, typestr)
    return {
        "title": title,
        "type": typestr,
        "posters": posters
    }

def make_key(*args, **kwargs):
    return str(kwargs)

def stats_list(metric, shows, limit=None, offset=None, sort="desc", depth=None, listify=False):
    if type(shows) is str:
        shows = [shows]
    raw = compute_stats(metric, shows, limit=limit, offset=offset, sort=sort, depth=depth)
    # assumes there is only 1 metric possible and it is last column
    if len(shows) > 1 or listify:
        return [x[:-1] for x in raw["data"]]
    return [x[0] for x in raw["data"]]


def compute_stats(metric, shows, limit=None, offset=None, sort="desc", depth=None, filters=[]):
    cache_key = CAROSEL_NS + "".join(([metric] + shows) + ([str(limit), str(offset),sort,str(depth)]))
    prev = cached_query(cache_key)
    if prev:
        return pickle.loads(prev)
    
    kwargs = {metric:"dummy"}
    kwargs[shows[0]] = 'show'
    for show in shows[1:]:
        kwargs[show] = "dummy"

    table = table_helper.select_best_table(kwargs, allowed_when_not, possible_tables)

    if not table:
        raise Exception("No Valid Table Available!")

    filters = []

    show_columns = [getattr(table, show) for show in shows]
    metric_col = getattr(table, metric)
    i = 0
    for show_column in show_columns:
        show=shows[i]
        if table in no_length_column:
            depth_val = depth or max_depth[show]
            filters.append(func.char_length(show_column) == depth_val )
        elif show in max_depth:
            depth_val = depth or max_depth[show]
            filters.append(getattr(table, show + table_helper.LEN) == depth_val )
        i+=1

    if table in filters_map:
        filters += filters_map[table]

    columns = show_columns + [metric_col]
    results = query_helper.query_table(table, columns, filters, order=metric, limit=limit, sort=sort, offset=offset)

    cached_query(cache_key, pickle.dumps(results))
    return results

def top_occupations(year, bra_id):
    cache_key = CAROSEL_NS + "top_occupations" + str(year) + bra_id
    prev = object_cache(cache_key)
    if prev:
        return pickle.loads(prev)

    table = rais.Ybo
    filters = [table.bra_id == bra_id, table.year == year]
    raw = query_helper.query_table(table, [table.cbo_id], filters, order=table.wage_avg, limit=10, sort="desc")
    cbos = [x[0] for x in raw["data"]]
    table = raisd.Ybod
    filters = [table.bra_id == bra_id, table.year == year, table.cbo_id.in_(cbos), table.d_id.in_(["A", "B"])]
    columns = [table.cbo_id, table.d_id, table.num_emp, table.wage_avg, table.wage_growth]
    results = query_helper.query_table(table, columns, filters, order=table.wage_avg)
    
    object_cache(cache_key, pickle.dumps(results))
    return results

def generic_join_breakdown(namespace, params, left_table, right_table, join_criteria, columns, order_col="ratio", filters=[], 
                           limit=10, sort_order="desc", offset=0, col_select=None):

    cache_key = CAROSEL_NS + namespace + "_" + str(params)
    
    prev = object_cache(cache_key)
    if prev:
        return pickle.loads(prev) 

    order = desc(order_col) if sort_order != "asc" else asc(order_col)
    results = left_table.query.join(right_table, join_criteria) \
                            .with_entities(*columns) \
                            .filter(*filters) \
                            .order_by(order) \
                            .limit(limit) \
                            .offset(offset) \
                            .all()

    if not col_select:
        raise Exception("Please specify the column to select for results")

    results = [row.__dict__[col_select] for row in results]

    object_cache(cache_key, pickle.dumps(results))
    return results