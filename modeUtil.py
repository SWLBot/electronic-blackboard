class ModeUtil(object):
    @staticmethod
    def checkOrderById(arrangeMode):
        if arrangeMode in [0,3]:
            return True
        else:
            return False
