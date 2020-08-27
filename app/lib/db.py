import pickledb

class PickleDatabase:
    def __init__(self, file):
    	self.db = pickledb.load(file, False)

    def get_data(self, attribute):
    	return self.db.get(attribute)

    def set_data(self, attribute, value):
    	self.db.set(attribute, value)
    	db.dump()

    	return True