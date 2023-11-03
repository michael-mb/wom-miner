staff_page_by_title = {
    "bool": {
        "must": [
            {
                # Search for these terms indicating a staff overview page
                "match": {
                    # "Mitarbeiter" also matches "Mitarbeiter/innen" and "Mitarbeiter*innen"
                    "title": "team mitarbeiter mitarbeitende mitarbeiterinnen lehrbeauftragte personen mitglieder lehrende staff employees people personal members lecturers lehrstuhlteam"
                }
            },
            # Note that this criteria was removed. See e.g. https://www.esaga.uni-due.de/members/ (no name recognized due to "Nachname, Titel Vorname")
            # ... but the handcrafted algorithm for table-analysis works on these pages
            # {
            #     # Exclude pages where the Preprocessing NER did not found any name
            #     "exists": {
            #         "field": "person_names"
            #     }
            # },
        ],
        "must_not": [
            {
                # Exclude non-relevant pages
                "match": {
                    "title": "ehemalige former publikation publikationen publication publications detail details angebot angebote offer offers alumni"
                }
            },
            # Criteria removed because of well-working name heuristics
            # {
            #     # Exclude years in URL and other numbers with at least 4 digits
            #     "regexp": {
            #         "url": ".*\d{4}.*"
            #     }
            # },
            {
                # Exclude URLs with 'publi[ck]ation' in it
                "wildcard": {
                    "url": "*publi?ation*"
                }
            },
            {
                # Exclude detail pages (we are only looking for staff overview pages)
                "wildcard": {
                    "url": "*detail*"
                }
            },
            {
                # Exclude URLs where 'blog' or 'news' is present between two '/'
                # Note that the regex-syntax is different here, since '/' in a query_string indicates a regex, the '/' character itself must be escaped
                # see also https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html#_regular_expressions
                "query_string": {
                    "default_field": "url",
                    "query": "/.*\\/.*aktuelles.*\\/.*/ OR /.*\\/.*blog.*\\/.*/ OR /.*\\/.*news.*\\/.*/"
                }
            },
        ]
    }
}
