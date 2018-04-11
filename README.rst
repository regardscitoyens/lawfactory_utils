lawfactory-utils
================

A few utilities for `the-law-factory-parser`_ project, shared by
`senapy`_ and `anpy`_.

-  A simple caching library:

::

    from lawfactory_utils.urls import enable_requests_cache, download
    enable_requests_cache()

    .....

    resp = download(url)
    print(resp.text)

The cached responses are stored in the directory where this lib is
installed. You can use ``lawfactory_where_is_my_cache`` to print the
path.

-  URL cleaning for senat/AN/legifrance/conseil-constit

::

    >>> from lawfactory_utils.urls import clean_url
    >>> clean_url('https://www.legifrance.gouv.fr/eli/loi/2017/9/15/JUSC1715752L/jo/texte')
    'https://www.legifrance.gouv.fr/affichTexte.do?cidTexte=JORFTEXT000035567936&categorieLien=id'

.. _the-law-factory-parser: https://github.com/regardscitoyens/the-law-factory-parser
.. _senapy: https://github.com/regardscitoyens/senapy
.. _anpy: https://github.com/regardscitoyens/anpy