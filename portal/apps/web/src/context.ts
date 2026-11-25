import { createContext, useContext } from 'react'
import type { User, Workspace } from './types'
export interface WorkspaceContextType {
  data: Workspace
  user: User
  refresh: () => Promise<void>
  notify: (text: string, error?: boolean) => void
  openCase: (id: string) => void
  openDocument: (id: string, version?: number) => void
}
export const WorkspaceContext = createContext<WorkspaceContextType | null>(null)
export function useWorkspace() {
  const v = useContext(WorkspaceContext)
  if (!v) throw new Error('Workspace context required')
  return v
}
