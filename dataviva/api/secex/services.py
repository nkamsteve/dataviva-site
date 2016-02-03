from dataviva.api.attrs.models import Wld, Bra, Hs
from dataviva.api.secex.models import Ymw, Ymbw, Ympw
from dataviva import db
from sqlalchemy.sql.expression import func, desc, asc

class TradePartner:
    def __init__(self, wld_id):
        self._country_info = None

        self.wld_id = wld_id
        self.ymw_max_year = db.session.query(func.max(Ymw.year)).filter_by(wld_id=wld_id)
        self.ymbw_max_year = db.session.query(func.max(Ymbw.year)).filter_by(wld_id=wld_id)
        self.ympw_max_year = db.session.query(func.max(Ympw.year)).filter_by(wld_id=wld_id)

    def __country_info__(self):
        if not self._country_info:
            ymw_query = Ymw.query.join(Wld).filter(
                Ymw.wld_id == self.wld_id,
                Ymw.month == 0,
                Ymw.year == self.ymw_max_year)

            ymw_data = ymw_query.values(
                Wld.name_pt,
                Ymw.year,
                (Ymw.export_val-Ymw.import_val),
                Ymw.export_val,
                (Ymw.export_kg/Ymw.export_val),
                Ymw.import_val,
                (Ymw.import_kg/Ymw.import_val))

            country = {}

            for name_pt, year, trade_balance, total_exported, unity_weight_export_price, total_imported, unity_weight_import_price in ymw_data:
                country['name'] = name_pt
                country['year'] = year
                country['trade_balance'] = trade_balance
                country['total_exported'] = total_exported
                country['unity_weight_export_price'] = unity_weight_export_price
                country['total_imported'] = total_imported
                country['unity_weight_import_price'] = unity_weight_import_price

            self._country_info = country

        return self._country_info

    def country_name(self):
        return self.__country_info__()['name']

    def year(self):
        return self.__country_info__()['year']

    def trade_balance(self):
        return self.__country_info__()['trade_balance']

    def total_exported(self):
        return self.__country_info__()['total_exported']

    def unity_weight_export_price(self):
        return self.__country_info__()['unity_weight_export_price']

    def total_imported(self):
        return self.__country_info__()['total_imported']

    def unity_weight_import_price(self):
        return self.__country_info__()['unity_weight_import_price']

    def municipality_with_more_exports(self):
        ymbw_municipality_export_query = Ymbw.query.join(Bra).filter(
            Ymbw.wld_id == self.wld_id,
            Ymbw.month == 0,
            Ymbw.year == self.ymbw_max_year,
            func.length(Ymbw.bra_id) == 9).order_by(desc(Ymbw.export_val)).limit(1)

        ymbw_municipality_export_data = ymbw_municipality_export_query.values(
            Bra.name_pt,
            Ymbw.export_val)

        municipality = {}

        for name_pt, export_val in ymbw_municipality_export_data:
            municipality['name'] = name_pt
            municipality['value'] = export_val

        return municipality

    def municipality_with_more_imports(self):
        ymbw_municipality_import_query = Ymbw.query.join(Bra).filter(
            Ymbw.wld_id == self.wld_id,
            Ymbw.month == 0,
            Ymbw.year == self.ymbw_max_year,
            func.length(Ymbw.bra_id) == 9).order_by(desc(Ymbw.import_val)).limit(1)

        ymbw_municipality_import_data = ymbw_municipality_import_query.values(
            Bra.name_pt,
            Ymbw.import_val)

        municipality = {}

        for name_pt, import_val in ymbw_municipality_import_data:
            municipality['name'] = name_pt
            municipality['value'] = import_val

        return municipality

    def product_with_more_exports(self):
        ympw_product_export_query = Ympw.query.join(Hs).filter(
            Ympw.wld_id == self.wld_id,
            Ympw.month == 0,
            Ympw.hs_id_len == 6,
            Ympw.year == self.ympw_max_year).order_by(desc(Ympw.export_val)).limit(1)

        ympw_product_export_data = ympw_product_export_query.values(
            Hs.name_pt,
            Ympw.export_val)

        product = {}

        for name_pt, export_val in ympw_product_export_data:
            product['name'] = name_pt
            product['value'] = export_val

        return product

    def product_with_more_imports(self):

        ympw_product_import_query = Ympw.query.join(Hs).filter(
            Ympw.wld_id == self.wld_id,
            Ympw.month == 0,
            Ympw.hs_id_len == 6,
            Ympw.year == self.ympw_max_year).order_by(desc(Ympw.import_val)).limit(1)

        ympw_product_import_data = ympw_product_import_query.values(
            Hs.name_pt,
            Ympw.import_val)

        product = {}

        for name_pt, import_val in ympw_product_import_data:
            product['name'] = name_pt
            product['value'] = import_val

        return product

    def product_with_highest_balance(self):
        ympw_highest_balance_query = Ympw.query.join(Hs).filter(
            Ympw.wld_id == self.wld_id,
            Ympw.month == 0,
            Ympw.hs_id_len == 6,
            Ympw.year == self.ympw_max_year).order_by(desc(Ympw.export_val-Ympw.import_val)).limit(1)

        ympw_highest_balance_data = ympw_highest_balance_query.values(
            Hs.name_pt,
            (Ympw.export_val - Ympw.import_val))

        product = {}

        for name_pt, trade_balance in ympw_highest_balance_data:
            product['name'] = name_pt
            product['value'] = trade_balance

        return product

    def product_with_lowest_balance(self):
        ympw_lowest_balance_query = Ympw.query.join(Hs).filter(
            Ympw.wld_id == self.wld_id,
            Ympw.month == 0,
            Ympw.hs_id_len == 6,
            Ympw.year == self.ympw_max_year).order_by(asc(Ympw.export_val-Ympw.import_val)).limit(1)

        ympw_lowest_balance_data = ympw_lowest_balance_query.values(
            Hs.name_pt,
            (Ympw.export_val - Ympw.import_val))

        product = {}

        for name_pt, trade_balance in ympw_lowest_balance_data:
            product['name'] = name_pt
            product['value'] = trade_balance

        return product