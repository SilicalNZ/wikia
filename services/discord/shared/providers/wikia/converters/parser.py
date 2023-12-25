from html.parser import HTMLParser as _HTMLParser


class HTMLTag(list):
    tag = None

    def append(self, value) -> None:
        combiners = ' ', ',', ';'
        if not self \
                or (all(value[0] != i and self[-1][-1] != i for i in combiners)
                    and value != ')'
                    and value != '.'
        ):
            super().append(value)
        else:
            self[-1] += value

    def __repr__(self):
        return str(f"{self.tag} {super().__repr__()}")


class P(HTMLTag):
    tag = 'p'


class A(HTMLTag):
    tag = 'a'


class Li(HTMLTag):
    tag = 'li'


class Dl(HTMLTag):
    tag = 'dl'


class Td(HTMLTag):
    tag = 'td'


class Th(HTMLTag):
    tag = 'th'


class H2(HTMLTag):
    tag = 'h2'


class Url(HTMLTag):
    tag = 'url'


class H1(HTMLTag):
    tag = 'h1'


class Extra(HTMLTag):
    tag = 'ext'


class Handler:
    def __init__(self):
        self.n = []
        self.scope = self.n

        self.out_of_scope = []

    def unscope(self):
        if not self.out_of_scope:
            return False

        self.zoom_out()
        self.n.append(self.out_of_scope[-1]())
        self.out_of_scope = self.out_of_scope[:-1]
        self.zoom_in()
        return False

    @property
    def is_zoomed_in(self) -> bool:
        return self.scope is not self.n

    def zoom_in(self):
        self.scope = self.n[-1]

    def zoom_out(self):
        self.scope = self.n

    def append_tag(self, tag):
        if self.is_zoomed_in:
            self.out_of_scope.append(self.scope.__class__)

        self.zoom_out()
        self.n.append(tag)
        self.zoom_in()

    def append_data(self, data):
        self.scope.append(data)

    def __iter__(self):
        yield from self.n

    def __repr__(self):
        return repr(self.n)

    def __str__(self):
        return str(self.n)

    def filter(self, key):
        self.n = [*filter(key, self.n)]


class PreciseHTMLParser(_HTMLParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.handle = Handler()
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        for i in (Li, Dl):
            if i.tag != tag:
                continue

            if self.handle.n and isinstance(self.handle.n[-1], i):
                self.handle.zoom_in()
            else:
                self.handle.append_tag(i())
            return

        for i in (P, H2, Td, Th, H1):
            if i.tag != tag:
                continue

            self.handle.append_tag(i())

        for key, item in attrs:
            if key in ('data-src', 'href', 'src') \
                    and item[:5] == 'https':
                item = Url((item,))
                self.handle.zoom_out()
                self.handle.n.append(item)

    def handle_endtag(self, tag):
        if any(i.tag == tag for i in (Li, Dl, P, H2, Td, Th, H1)):
            self.handle.zoom_out()

    def handle_data(self, data):
        data = data.replace('  ', ' ')  # Non breaking Space

        if data.strip():  # Ignore " "
            if self.handle.is_zoomed_in:
                self.handle.scope.append(data)
            elif self.handle.n and isinstance(self.handle.n[-1], Extra):
                self.handle.n[-1].append(data)
            else:
                self.handle.append_tag(Extra((data,)))
                self.handle.zoom_out()

    def feed(self, data) -> Handler:
        data = data.replace('\u200b', '')

        super().feed(data)
        return self.handle
