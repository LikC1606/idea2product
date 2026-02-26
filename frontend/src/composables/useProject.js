import { ref, readonly } from 'vue'
import * as api from '../api/projects'

export const projectId = ref(null)
export const files = ref([])
export const currentFile = ref(null)
export const fileContent = ref(null)

export function useProject() {
  const createProject = async () => {
    const data = await api.createProject(true)
    projectId.value = data.project_id
    return data.project_id
  }

  const ensureProject = async () => {
    if (projectId.value) return projectId.value
    return createProject()
  }

  const loadProject = async (pid) => {
    projectId.value = pid
    currentFile.value = null
    fileContent.value = null
    files.value = []
    try {
      const data = await api.getChat(pid)
      const msgs = data.messages || []
      return msgs
    } catch {
      return []
    }
  }

  const loadFiles = async () => {
    if (!projectId.value) return
    try {
      const data = await api.listFiles(projectId.value)
      files.value = data.files || []
    } catch {
      files.value = []
    }
  }

  const loadFileContent = async (path) => {
    if (!projectId.value) return null
    currentFile.value = path
    try {
      const data = await api.getFile(projectId.value, path)
      fileContent.value = data
      return data
    } catch {
      fileContent.value = null
      return null
    }
  }

  const resetProject = () => {
    projectId.value = null
    files.value = []
    currentFile.value = null
    fileContent.value = null
  }

  return {
    projectId: readonly(projectId),
    files: readonly(files),
    currentFile: readonly(currentFile),
    fileContent: readonly(fileContent),
    createProject,
    ensureProject,
    loadProject,
    loadFiles,
    loadFileContent,
    resetProject,
  }
}
