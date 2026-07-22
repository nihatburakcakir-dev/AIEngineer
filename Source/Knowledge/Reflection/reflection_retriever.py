############################################################
## REFLECTION ENGINE V2
##
## PART 1 / 12
##
## DOSYANIN EN ÜSTÜNE YAPIŞTIR.
############################################################

import sqlite3
import json
import difflib
from functools import lru_cache


class ReflectionEngine:

    def __init__(

        self,

        db_path="knowledge.db"

    ):

        self.db_path = db_path

        self.conn = sqlite3.connect(

            db_path

        )

        self.conn.row_factory = sqlite3.Row

        self.cache = {}

        self.statistics = {

            "queries": 0,

            "cache_hits": 0,

            "cache_miss": 0

        }


    ########################################################
    ## INTERNAL
    ########################################################

    def close(

        self

    ):

        self.conn.close()


    def _decode_json(

        self,

        value

    ):

        if value is None:

            return []

        if value == "":

            return []

        try:

            return json.loads(

                value

            )

        except:

            return []


    def _normalize_row(

        self,

        row

    ):

        item = dict(row)

        item["methods"] = self._decode_json(

            item.get("methods")

        )

        item["properties"] = self._decode_json(

            item.get("properties")

        )

        item["fields"] = self._decode_json(

            item.get("fields")

        )

        return item


    def _rows(

        self,

        sql,

        params=()

    ):

        self.statistics["queries"] += 1

        cur = self.conn.execute(

            sql,

            params

        )

        rows = []

        for row in cur.fetchall():

            rows.append(

                self._normalize_row(

                    row

                )

            )

        return rows


    def _one(

        self,

        sql,

        params=()

    ):

        rows = self._rows(

            sql,

            params

        )

        if rows:

            return rows[0]

        return None


    ########################################################
    ## DATABASE
    ########################################################

    def count(

        self

    ):

        cur = self.conn.execute(

            """

            SELECT COUNT(*)

            FROM reflection_types

            """

        )

        return cur.fetchone()[0]


    def all(

        self

    ):

        return self._rows(

            """

            SELECT *

            FROM reflection_types

            ORDER BY class_name

            """

        )


    def assemblies(

        self

    ):

        cur = self.conn.execute(

            """

            SELECT DISTINCT assembly

            FROM reflection_types

            ORDER BY assembly

            """

        )

        return [

            x[0]

            for x in cur.fetchall()

        ]


    def namespaces(

        self

    ):

        cur = self.conn.execute(

            """

            SELECT DISTINCT namespace

            FROM reflection_types

            ORDER BY namespace

            """

        )

        return [

            x[0]

            for x in cur.fetchall()

        ]


############################################################
## REFLECTION ENGINE V2
##
## PART 2 / 12
##
## CTRL + F
##
## def namespaces(
##
## namespaces() FONKSİYONUNUN HEMEN ALTINA YAPIŞTIR.
############################################################


    ########################################################
    ## CLASS SEARCH
    ########################################################

    def find_class(

        self,

        class_name

    ):

        return self._rows(

            """

            SELECT *

            FROM reflection_types

            WHERE class_name LIKE ?

            ORDER BY class_name

            """,

            (

                f"%{class_name}%",

            )

        )


    def class_exists(

        self,

        class_name

    ):

        return len(

            self.find_class(

                class_name

            )

        ) > 0


    def get_class(

        self,

        class_name

    ):

        rows = self.find_class(

            class_name

        )

        if rows:

            return rows[0]

        return None


    ########################################################
    ## ASSEMBLY SEARCH
    ########################################################

    def find_assembly(

        self,

        assembly

    ):

        return self._rows(

            """

            SELECT *

            FROM reflection_types

            WHERE assembly LIKE ?

            ORDER BY class_name

            """,

            (

                f"%{assembly}%",

            )

        )


    ########################################################
    ## NAMESPACE SEARCH
    ########################################################

    def find_namespace(

        self,

        namespace

    ):

        return self._rows(

            """

            SELECT *

            FROM reflection_types

            WHERE namespace LIKE ?

            ORDER BY class_name

            """,

            (

                f"%{namespace}%",

            )

        )


    ########################################################
    ## INHERITANCE
    ########################################################

    def inherits_from(

        self,

        base_class

    ):

        return self._rows(

            """

            SELECT *

            FROM reflection_types

            WHERE base_class LIKE ?

            ORDER BY class_name

            """,

            (

                f"%{base_class}%",

            )

        )


    def derived_classes(

        self,

        base_class

    ):

        return self.inherits_from(

            base_class

        )

############################################################
## REFLECTION ENGINE V2
##
## PART 3 / 12
##
## CTRL + F
##
## def derived_classes(
##
## ALTINA YAPIŞTIR
############################################################


    ########################################################
    ## METHOD SEARCH
    ########################################################

    def find_method(

        self,

        method_name

    ):

        keyword = method_name.lower()

        result = []

        for cls in self.all():

            for method in cls["methods"]:

                if keyword in method.lower():

                    result.append(cls)

                    break

        return result


    def method_exists(

        self,

        method_name

    ):

        return len(

            self.find_method(

                method_name

            )

        ) > 0


    ########################################################
    ## PROPERTY SEARCH
    ########################################################

    def find_property(

        self,

        property_name

    ):

        keyword = property_name.lower()

        result = []

        for cls in self.all():

            for prop in cls["properties"]:

                if keyword in prop.lower():

                    result.append(cls)

                    break

        return result


    def property_exists(

        self,

        property_name

    ):

        return len(

            self.find_property(

                property_name

            )

        ) > 0


    ########################################################
    ## FIELD SEARCH
    ########################################################

    def find_field(

        self,

        field_name

    ):

        keyword = field_name.lower()

        result = []

        for cls in self.all():

            for field in cls["fields"]:

                if keyword in field.lower():

                    result.append(cls)

                    break

        return result


    def field_exists(

        self,

        field_name

    ):

        return len(

            self.find_field(

                field_name

            )

        ) > 0


############################################################
## REFLECTION ENGINE V2
##
## PART 4 / 12
##
## CTRL + F
##
## def field_exists(
##
## ALTINA YAPIŞTIR
############################################################


    ########################################################
    ## INTERNAL SEARCH ENGINE
    ########################################################

    def _contains(

        self,

        value,

        keyword

    ):

        if value is None:

            return False

        return keyword in value.lower()


    def _list_contains(

        self,

        values,

        keyword

    ):

        for item in values:

            if keyword in item.lower():

                return True

        return False


    def _search_column(

        self,

        column,

        keyword

    ):

        keyword = keyword.lower()

        result = []

        for row in self.all():

            value = row.get(

                column

            )

            if isinstance(

                value,

                list

            ):

                if self._list_contains(

                    value,

                    keyword

                ):

                    result.append(

                        row

                    )

            else:

                if self._contains(

                    str(value),

                    keyword

                ):

                    result.append(

                        row

                    )

        return result


    ########################################################
    ## GENERIC SEARCH
    ########################################################

    def search(

        self,

        keyword

    ):

        keyword = keyword.lower()

        result = []

        visited = set()

        columns = [

            "class_name",

            "namespace",

            "assembly",

            "base_class",

            "methods",

            "properties",

            "fields"

        ]

        for column in columns:

            rows = self._search_column(

                column,

                keyword

            )

            for row in rows:

                key = (

                    row["assembly"],

                    row["class_name"]

                )

                if key in visited:

                    continue

                visited.add(

                    key

                )

                result.append(

                    row

                )

        return result


    def exists(

        self,

        keyword

    ):

        return len(

            self.search(

                keyword

            )

        ) > 0


############################################################
## REFLECTION ENGINE V2
##
## PART 5 / 12
##
## CTRL + F
##
## def exists(
##
## ALTINA YAPIŞTIR
############################################################


    ########################################################
    ## CACHE ENGINE
    ########################################################

    def clear_cache(

        self

    ):

        self.cache.clear()


    def cache_size(

        self

    ):

        return len(

            self.cache

        )


    def cache_keys(

        self

    ):

        return list(

            self.cache.keys()

        )


    def _cache_get(

        self,

        key

    ):

        if key in self.cache:

            self.statistics[

                "cache_hits"

            ] += 1

            return self.cache[

                key

            ]

        self.statistics[

            "cache_miss"

        ] += 1

        return None


    def _cache_set(

        self,

        key,

        value

    ):

        self.cache[key] = value

        return value


    ########################################################
    ## CACHED SEARCH
    ########################################################

    def cached_search(

        self,

        keyword

    ):

        key = (

            "search",

            keyword.lower()

        )

        cached = self._cache_get(

            key

        )

        if cached is not None:

            return cached

        result = self.search(

            keyword

        )

        return self._cache_set(

            key,

            result

        )


    def cached_find_class(

        self,

        class_name

    ):

        key = (

            "class",

            class_name.lower()

        )

        cached = self._cache_get(

            key

        )

        if cached is not None:

            return cached

        result = self.find_class(

            class_name

        )

        return self._cache_set(

            key,

            result

        )


############################################################
## REFLECTION ENGINE V2
##
## PART 6 / 12
##
## CTRL + F
##
## def cached_find_class(
##
## ALTINA YAPIŞTIR
############################################################


    ########################################################
    ## SIMILARITY ENGINE
    ########################################################

    def similarity(

        self,

        a,

        b

    ):

        return difflib.SequenceMatcher(

            None,

            a.lower(),

            b.lower()

        ).ratio()


    def rank_by_similarity(

        self,

        keyword,

        rows,

        field="class_name"

    ):

        keyword = keyword.lower()

        ranked = []

        for row in rows:

            score = self.similarity(

                keyword,

                str(

                    row.get(

                        field,

                        ""

                    )

                )

            )

            item = dict(

                row

            )

            item["_score"] = score

            ranked.append(

                item

            )

        ranked.sort(

            key=lambda x: x["_score"],

            reverse=True

        )

        return ranked


    ########################################################
    ## SMART SEARCH
    ########################################################

    def smart_search(

        self,

        keyword

    ):

        rows = self.search(

            keyword

        )

        return self.rank_by_similarity(

            keyword,

            rows

        )


    def best_match(

        self,

        keyword

    ):

        rows = self.smart_search(

            keyword

        )

        if rows:

            return rows[0]

        return None


    ########################################################
    ## TOP RESULTS
    ########################################################

    def top(

        self,

        keyword,

        limit=10

    ):

        rows = self.smart_search(

            keyword

        )

        return rows[:limit]


############################################################
## REFLECTION ENGINE V2
##
## PART 7 / 12
##
## CTRL + F
##
## def top(
##
## ALTINA YAPIŞTIR
############################################################


    ########################################################
    ## TYPE FILTERS
    ########################################################

    def unity_types(

        self

    ):

        return self.find_assembly(

            "Unity"

        )


    def user_types(

        self

    ):

        return self.find_assembly(

            "Assembly-CSharp"

        )


    def ai_types(

        self

    ):

        return self.find_assembly(

            "AIEngineer"

        )


    ########################################################
    ## API RECOMMENDATION
    ########################################################

    def recommend_class(

        self,

        keyword,

        limit=5

    ):

        rows = self.smart_search(

            keyword

        )

        return rows[:limit]


    def recommend_method(

        self,

        keyword,

        limit=10

    ):

        keyword = keyword.lower()

        result = []

        visited = set()

        for row in self.all():

            for method in row["methods"]:

                if keyword in method.lower():

                    key = (

                        row["class_name"],

                        method

                    )

                    if key in visited:

                        continue

                    visited.add(

                        key

                    )

                    result.append(

                        {

                            "class": row["class_name"],

                            "method": method,

                            "assembly": row["assembly"],

                            "namespace": row["namespace"]

                        }

                    )

        result.sort(

            key=lambda x: x["method"]

        )

        return result[:limit]


    ########################################################
    ## QUICK HELPERS
    ########################################################

    def methods_of(

        self,

        class_name

    ):

        cls = self.best_match(

            class_name

        )

        if cls is None:

            return []

        return cls["methods"]


    def properties_of(

        self,

        class_name

    ):

        cls = self.best_match(

            class_name

        )

        if cls is None:

            return []

        return cls["properties"]


    def fields_of(

        self,

        class_name

    ):

        cls = self.best_match(

            class_name

        )

        if cls is None:

            return []

        return cls["fields"]


############################################################
## REFLECTION ENGINE V2
##
## PART 8 / 12
##
## CTRL + F
##
## def fields_of(
##
## ALTINA YAPIŞTIR
############################################################


    ########################################################
    ## STATISTICS
    ########################################################

    def statistics_report(

        self

    ):

        report = dict(

            self.statistics

        )

        report["classes"] = self.count()

        report["assemblies"] = len(

            self.assemblies()

        )

        report["namespaces"] = len(

            self.namespaces()

        )

        report["cache_size"] = self.cache_size()

        return report


    ########################################################
    ## INDEX BUILDERS
    ########################################################

    def class_index(

        self

    ):

        index = {}

        for row in self.all():

            index[

                row["class_name"]

            ] = row

        return index


    def namespace_index(

        self

    ):

        index = {}

        for row in self.all():

            namespace = row["namespace"]

            if namespace not in index:

                index[namespace] = []

            index[namespace].append(

                row

            )

        return index


    def assembly_index(

        self

    ):

        index = {}

        for row in self.all():

            assembly = row["assembly"]

            if assembly not in index:

                index[assembly] = []

            index[assembly].append(

                row

            )

        return index


    ########################################################
    ## QUERY HISTORY
    ########################################################

    def reset_statistics(

        self

    ):

        self.statistics = {

            "queries": 0,

            "cache_hits": 0,

            "cache_miss": 0

        }


    def cache_hit_rate(

        self

    ):

        total = (

            self.statistics["cache_hits"]

            +

            self.statistics["cache_miss"]

        )

        if total == 0:

            return 0.0

        return (

            self.statistics["cache_hits"]

            /

            total

        )


############################################################
## REFLECTION ENGINE V2
##
## PART 9 / 12
##
## CTRL + F
##
## def cache_hit_rate(
##
## ALTINA YAPIŞTIR
############################################################


    ########################################################
    ## RELATIONSHIP ENGINE
    ########################################################

    def related_classes(

        self,

        class_name

    ):

        cls = self.best_match(

            class_name

        )

        if cls is None:

            return []

        result = []

        base = cls["base_class"]

        namespace = cls["namespace"]

        for row in self.all():

            if row["class_name"] == cls["class_name"]:

                continue

            score = 0

            if row["namespace"] == namespace:

                score += 2

            if row["base_class"] == base:

                score += 3

            common = len(

                set(

                    cls["methods"]

                ).intersection(

                    row["methods"]

                )

            )

            score += common

            if score > 0:

                result.append(

                    {

                        "score": score,

                        "class": row

                    }

                )

        result.sort(

            key=lambda x: x["score"],

            reverse=True

        )

        return result


    ########################################################
    ## API SUGGESTIONS
    ########################################################

    def suggest_methods(

        self,

        class_name,

        limit=10

    ):

        cls = self.best_match(

            class_name

        )

        if cls is None:

            return []

        methods = sorted(

            cls["methods"]

        )

        return methods[:limit]


    def suggest_properties(

        self,

        class_name,

        limit=10

    ):

        cls = self.best_match(

            class_name

        )

        if cls is None:

            return []

        props = sorted(

            cls["properties"]

        )

        return props[:limit]


    def suggest_fields(

        self,

        class_name,

        limit=10

    ):

        cls = self.best_match(

            class_name

        )

        if cls is None:

            return []

        fields = sorted(

            cls["fields"]

        )

        return fields[:limit]


############################################################
## REFLECTION ENGINE V2
##
## PART 10 / 12
##
## CTRL + F
##
## def suggest_fields(
##
## ALTINA YAPIŞTIR
############################################################


    ########################################################
    ## QUERY ENGINE
    ########################################################

    def query(

        self,

        text

    ):

        words = [

            x.strip().lower()

            for x in text.split()

            if x.strip()

        ]

        result = []

        visited = set()

        for word in words:

            rows = self.search(

                word

            )

            for row in rows:

                key = (

                    row["assembly"],

                    row["class_name"]

                )

                if key in visited:

                    continue

                visited.add(

                    key

                )

                result.append(

                    row

                )

        return result


    def resolve(

        self,

        text

    ):

        rows = self.query(

            text

        )

        ranked = self.rank_by_similarity(

            text,

            rows

        )

        if ranked:

            return ranked[0]

        return None


    ########################################################
    ## CLASS INSPECTOR
    ########################################################

    def inspect(

        self,

        class_name

    ):

        cls = self.best_match(

            class_name

        )

        if cls is None:

            return None

        return {

            "assembly":

                cls["assembly"],

            "namespace":

                cls["namespace"],

            "class":

                cls["class_name"],

            "base":

                cls["base_class"],

            "method_count":

                len(

                    cls["methods"]

                ),

            "property_count":

                len(

                    cls["properties"]

                ),

            "field_count":

                len(

                    cls["fields"]

                ),

            "methods":

                cls["methods"],

            "properties":

                cls["properties"],

            "fields":

                cls["fields"]

        }


    ########################################################
    ## EXPORT
    ########################################################

    def export_summary(

        self

    ):

        return {

            "classes":

                self.count(),

            "assemblies":

                self.assemblies(),

            "namespaces":

                self.namespaces(),

            "statistics":

                self.statistics_report()

        }


############################################################
## REFLECTION ENGINE V2
##
## PART 11 / 12
##
## CTRL + F
##
## def export_summary(
##
## ALTINA YAPIŞTIR
############################################################


    ########################################################
    ## PUBLIC API
    ########################################################

    def search_class(

        self,

        name

    ):

        return self.cached_find_class(

            name

        )


    def search_method(

        self,

        name

    ):

        return self.find_method(

            name

        )


    def search_property(

        self,

        name

    ):

        return self.find_property(

            name

        )


    def search_field(

        self,

        name

    ):

        return self.find_field(

            name

        )


    ########################################################
    ## AUTO COMPLETE
    ########################################################

    def complete(

        self,

        text,

        limit=10

    ):

        rows = self.smart_search(

            text

        )

        result = []

        used = set()

        for row in rows:

            name = row["class_name"]

            if name in used:

                continue

            used.add(

                name

            )

            result.append(

                name

            )

            if len(result) >= limit:

                break

        return result


    ########################################################
    ## VALIDATION
    ########################################################

    def validate(

        self,

        class_name,

        method=None

    ):

        cls = self.best_match(

            class_name

        )

        if cls is None:

            return False

        if method is None:

            return True

        return method in cls["methods"]


    ########################################################
    ## INFORMATION
    ########################################################

    def info(

        self

    ):

        return {

            "engine":

                "ReflectionEngine",

            "version":

                "2.0",

            "database":

                self.db_path,

            "classes":

                self.count(),

            "assemblies":

                len(

                    self.assemblies()

                ),

            "namespaces":

                len(

                    self.namespaces()

                )

        }


############################################################
## REFLECTION ENGINE V2
##
## PART 12 / 12
##
## CTRL + F
##
## def info(
##
## ALTINA YAPIŞTIR
############################################################


    ########################################################
    ## SELF CHECK
    ########################################################

    def self_check(

        self

    ):

        report = {}

        try:

            report["database"] = True

            report["classes"] = self.count()

            report["assemblies"] = len(

                self.assemblies()

            )

            report["namespaces"] = len(

                self.namespaces()

            )

            report["cache"] = self.cache_size()

            report["status"] = "OK"

        except Exception as ex:

            report["status"] = "ERROR"

            report["message"] = str(

                ex

            )

        return report


    ########################################################
    ## WARMUP
    ########################################################

    def warmup(

        self

    ):

        self.all()

        self.assemblies()

        self.namespaces()

        return True


    ########################################################
    ## RELOAD
    ########################################################

    def reload(

        self

    ):

        try:

            self.conn.close()

        except:

            pass

        self.conn = sqlite3.connect(

            self.db_path

        )

        self.conn.row_factory = sqlite3.Row

        self.clear_cache()

        self.reset_statistics()

        return True


    ########################################################
    ## DISPOSE
    ########################################################

    def dispose(

        self

    ):

        try:

            self.conn.close()

        except:

            pass

        self.cache.clear()


    ########################################################
    ## MAGIC METHODS
    ########################################################

    def __len__(

        self

    ):

        return self.count()


    def __contains__(

        self,

        item

    ):

        return self.class_exists(

            item

        )


    def __repr__(

        self

    ):

        return (

            f"<ReflectionEngine "

            f"classes={self.count()} "

            f"assemblies={len(self.assemblies())}>"

        )


############################################################
## REFLECTION ENGINE V2
##
## DOSYA TAMAMLANDI
########################################################################################################################
## PART 11 BİTTİ
##
## SIRADAKİ:
##
## info()
##
## PART 12'Yİ
##
## info()
##
## ALTINA YAPIŞTIR.
########################################################################################################################
## PART 10 BİTTİ
##
## SIRADAKİ:
##
## export_summary()
##
## PART 11'İ
##
## export_summary()
##
## ALTINA YAPIŞTIR.
########################################################################################################################
## PART 9 BİTTİ
##
## SIRADAKİ:
##
## suggest_fields()
##
## PART 10'U
##
## suggest_fields()
##
## ALTINA YAPIŞTIR.
########################################################################################################################
## PART 8 BİTTİ
##
## SIRADAKİ:
##
## cache_hit_rate()
##
## PART 9'U
##
## cache_hit_rate()
##
## ALTINA YAPIŞTIR.
########################################################################################################################
## PART 7 BİTTİ
##
## SIRADAKİ:
##
## fields_of()
##
## PART 8'İ
##
## fields_of()
##
## ALTINA YAPIŞTIR.
########################################################################################################################
## PART 6 BİTTİ
##
## SIRADAKİ:
##
## top()
##
## PART 7'Yİ
##
## top()
##
## ALTINA YAPIŞTIR.
########################################################################################################################
## PART 5 BİTTİ
##
## SIRADAKİ:
##
## cached_find_class()
##
## PART 6'YI
##
## cached_find_class()
##
## ALTINA YAPIŞTIR.
########################################################################################################################
## PART 4 BİTTİ
##
## SIRADAKİ:
##
## exists()
##
## PART 5'İ
##
## exists()
##
## FONKSİYONUNUN ALTINA
##
## YAPIŞTIR.
########################################################################################################################
## PART 3 BİTTİ
##
## SIRADAKİ:
##
## field_exists()
##
## PART 4'Ü
##
## field_exists()
##
## FONKSİYONUNUN ALTINA
##
## YAPIŞTIR.
############################################################