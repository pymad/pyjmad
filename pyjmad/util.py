class HtmlDict(dict):
    def _repr_html_(self):
        return ''.join([s._repr_html_() for s in self.values()])
