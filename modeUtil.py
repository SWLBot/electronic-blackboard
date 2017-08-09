from random import sample

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

    @staticmethod
    def selectDisplayCandidates(mode,candidates):
        if mode in [2,5]:
            if len(candidates) > 20:
                return sample(candidates,20)
        elif mode in [1,4]:
            return sample(candidates,len(candidates))

        return candidates
