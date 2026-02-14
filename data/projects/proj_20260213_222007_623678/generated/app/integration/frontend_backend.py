# app/integration/frontend_backend.py

from app.ui.task_creation import TaskCreationUI
from app.ui.task_management import TaskManagementUI
from app.ui.task_organization import TaskOrganizationUI
from app.logic.task_creation import TaskCreationLogic
from app.logic.task_management import TaskManagementLogic
from app.logic.task_organization import TaskOrganizationLogic

class FrontendBackendIntegration:
    def __init__(self):
        self.task_creation_ui = TaskCreationUI()
        self.task_management_ui = TaskManagementUI()
        self.task_organization_ui = TaskOrganizationUI()

        self.task_creation_logic = TaskCreationLogic()
        self.task_management_logic = TaskManagementLogic()
        self.task_organization_logic = TaskOrganizationLogic()

    def create_task(self, task_data):
        task = self.task_creation_logic.create_task(task_data)
        self.task_creation_ui.display_task_creation_status(task)
        return task

    def manage_task(self, task_id, action):
        result = self.task_management_logic.manage_task(task_id, action)
        self.task_management_ui.display_task_management_status(task_id, result)
        return result

    def organize_tasks(self, criteria):
        organized_tasks = self.task_organization_logic.organize_tasks(criteria)
        self.task_organization_ui.display_organized_tasks(organized_tasks)
        return organized_tasks

    def run(self):
        # Sample flow of integration
        task_data = {"title": "Sample Task", "description": "This is a sample task."}
        task = self.create_task(task_data)

        task_id = task.get('id')
        self.manage_task(task_id, "complete")

        criteria = {"sort_by": "date", "order": "ascending"}
        self.organize_tasks(criteria)

if __name__ == "__main__":
    integration = FrontendBackendIntegration()
    integration.run()