class JobManager:
    def __init__(self):
        self.jobs = {}

    def add_job(self, name, task):
        self.jobs[name] = task

    def get_status(self, name):
        task = self.jobs.get(name)
        if task is None:
            return "No jobs"

        if task.done():
            return "done"
        else:
            return "running"
        
    def get_job_list(self):
        return self.jobs