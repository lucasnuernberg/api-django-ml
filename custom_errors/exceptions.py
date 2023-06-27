
class CustomValidationErrorsDict(dict):
    def add(self, key, value):
        if key not in self:
            self[key] = ''
        if not self[key]:
            self[key] = value
        else:
            self[key] = value

