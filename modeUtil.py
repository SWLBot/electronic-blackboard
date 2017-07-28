class ModeUtil(object):
    @staticmethod
    def checkOrderById(arrangeMode):
        if arrangeMode in [0,3]:
            return True
        else:
            return False

    @staticmethod
    def checkConditionAssigned(arrangeMode):
        if arrangeMode in [3,4,5,7]:
            return True
        else:
            return False
