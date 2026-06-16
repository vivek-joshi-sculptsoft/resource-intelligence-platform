import { useDocumentTitle } from '../../shared/hooks/useDocumentTitle'
import { WorklogsPage } from '../../modules/worklogs/components/WorklogsPage'

export function WorklogsRoute() {
  useDocumentTitle('Worklogs')
  return <WorklogsPage />
}
