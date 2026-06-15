import { useDocumentTitle } from '../../shared/hooks/useDocumentTitle'
import { MyAssignmentsPage } from '../../modules/worklogs/components/MyAssignmentsPage'

export function MyAssignmentsRoute() {
  useDocumentTitle('My Assignments')
  return <MyAssignmentsPage />
}
