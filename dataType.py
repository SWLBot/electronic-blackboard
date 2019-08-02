class DataType:
    def __init__(self, type_id=None, type_name=None, type_dir=None):
        if not (type_id and type_name and type_dir):
            raise ValueError("Missing arguement for DataType")

        self.type_id = type_id
        self.type_name = type_name
        self.type_dir = type_dir
