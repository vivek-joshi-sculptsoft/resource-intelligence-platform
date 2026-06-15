import { AvailabilityView } from '../../modules/utilization/components/AvailabilityView'
import { useDocumentTitle } from '../../shared/hooks/useDocumentTitle'

export function AvailabilityPage() {
  useDocumentTitle('Resource Availability')

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[22px] font-bold" style={{ color: '#1e1b4b' }}>Resource Availability</h1>
          <div className="text-[13px] mt-0.5" style={{ color: '#6b7280' }}>
            View allocation status of all active resources across the organization
          </div>
        </div>
      </div>
      <AvailabilityView />
    </div>
  )
}
