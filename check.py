class B:

    def __hash__(self):
        return id(self)


v = B()
print(hash(v), id(v))
