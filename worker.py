import os

class Worker():
    def __init__(self,job,name):
        self.fn = job
        self.name = name

    def do(self,timestamp):
        pid = None
        try:
            print('[{timestamp}] {name}'.format(timestamp=timestamp,name=self.name))
            pid = os.fork()
            if pid == 0:
                self.fn()
                exit(0)
            else:
                # Don't need to wait
                # have handler to get terminated process when SIGCHLD is raised
                # in arrange_schedule.py 

                #TODO find out why there is still zombie process
                return 0
        except Exception as e:
            #TODO logging the error message
            print(str(e))
            if pid is not None and pid == 0: # child fn() raise exception
                exit(1)
            else: # fork fail
                return 1
