from oompa_types.objects.named import Named


class NamedHash(Named):
    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, Named):
            return self.name == other.name
        return self.name == str(other)
